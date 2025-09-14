from asyncio import create_task, as_completed
from typing import List, Coroutine, Type

from pydantic import BaseModel

from gravybox.exceptions import DataUnavailable, CollectionFailure
from gravybox.protocol import Condition, UpstreamCallParadigms


def merge_dicts_and_trim_nones(first: dict, second: dict, first_call_precedence: bool):
    trimmed_first = {}
    for key, value in first.items():
        if isinstance(value, str):
            if len(value) > 0:
                trimmed_first[key] = value
        elif value is not None:
            trimmed_first[key] = value
    trimmed_second = {}
    for key, value in second.items():
        if key in trimmed_first and first_call_precedence:
            continue
        if isinstance(value, str):
            if len(value) > 0:
                trimmed_second[key] = value
        elif value is not None:
            trimmed_second[key] = value
    result = trimmed_first | trimmed_second
    return result


def all_fields_populated(instance: BaseModel, nullable_fields: List[str]):
    for key, value in instance.model_dump().items():
        if value is None and key not in nullable_fields:
            return False
    return True


def no_fields_populated(instance: BaseModel):
    for key, value in instance.model_dump().items():
        if value is not None:
            return False
    return True


def all_upstream_calls_failed(failure_conditions, upstream_calls):
    if len(failure_conditions) == len(upstream_calls):
        return True
    else:
        return False


def all_upstream_calls_were_data_unavailable(failure_conditions):
    for condition in failure_conditions:
        if condition != Condition.data_unavailable:
            return False
    return True


class UpstreamCentrifuge:
    def __init__(self, upstream_calls: List[Coroutine],
                 result_model: Type[BaseModel],
                 nullable_fields: List[str] | None = None,
                 first_call_precedence: bool = False):
        self.tasks = [create_task(upstream_call) for upstream_call in upstream_calls]
        self.result_model = result_model
        if nullable_fields is None:
            self.nullable_fields = []
        else:
            self.nullable_fields = nullable_fields
        self.first_call_precedence = first_call_precedence

    async def activate(self):
        final_result = self.result_model()
        failure_conditions = []
        for upstream_call_wrapper in as_completed(self.tasks):
            upstream_result = await upstream_call_wrapper
            if isinstance(upstream_result, Condition):
                failure_conditions.append(upstream_result)
            else:
                final_result_dict = merge_dicts_and_trim_nones(final_result.model_dump(), upstream_result.model_dump(),
                                                               self.first_call_precedence)
                final_result = self.result_model.model_validate(final_result_dict)
                if all_fields_populated(final_result, self.nullable_fields):
                    break
        for task in self.tasks:
            if not task.done():
                task.cancel()
        if all_upstream_calls_failed(failure_conditions, self.tasks):
            if all_upstream_calls_were_data_unavailable(failure_conditions):
                raise DataUnavailable()
            else:
                raise CollectionFailure()
        else:
            return final_result


class UpstreamSequencer:
    def __init__(self, upstream_calls: List[Coroutine],
                 result_model: Type[BaseModel],
                 nullable_fields: List[str] | None = None,
                 first_call_precedence: bool = False):
        self.upstream_calls = upstream_calls
        self.result_model = result_model
        if nullable_fields is None:
            self.nullable_fields = []
        else:
            self.nullable_fields = nullable_fields
        self.first_call_precedence = first_call_precedence

    async def activate(self):
        final_result = self.result_model()
        failure_conditions = []
        for upstream_call_wrapper in self.upstream_calls:
            upstream_result = await upstream_call_wrapper
            if isinstance(upstream_result, Condition):
                failure_conditions.append(upstream_result)
            else:
                final_result_dict = merge_dicts_and_trim_nones(final_result.model_dump(), upstream_result.model_dump(),
                                                               self.first_call_precedence)
                final_result = self.result_model.model_validate(final_result_dict)
                if all_fields_populated(final_result, self.nullable_fields):
                    break
        if all_upstream_calls_failed(failure_conditions, self.upstream_calls):
            if all_upstream_calls_were_data_unavailable(failure_conditions):
                raise DataUnavailable()
            else:
                raise CollectionFailure()
        else:
            return final_result


class UpstreamShortCircuit:
    def __init__(self, upstream_calls: List[Coroutine], result_model: Type[BaseModel]):
        self.upstream_calls = upstream_calls
        self.result_model = result_model

    async def activate(self):
        failure_conditions = []
        for upstream_call_wrapper in self.upstream_calls:
            upstream_result = await upstream_call_wrapper
            if isinstance(upstream_result, Condition):
                failure_conditions.append(upstream_result)
            else:
                return upstream_result
        if all_upstream_calls_failed(failure_conditions, self.upstream_calls):
            if all_upstream_calls_were_data_unavailable(failure_conditions):
                raise DataUnavailable()
            else:
                raise CollectionFailure()
        else:
            return self.result_model()


class UpstreamCaller:
    def __init__(self, upstream_calls: List[Coroutine],
                 result_model: Type[BaseModel],
                 paradigm: UpstreamCallParadigms,
                 nullable_fields: List[str] | None = None,
                 first_call_precedence: bool = False):
        if paradigm == UpstreamCallParadigms.sequential:
            self.upstream_caller = UpstreamSequencer(upstream_calls, result_model, nullable_fields=nullable_fields,
                                                     first_call_precedence=first_call_precedence)
        elif paradigm == UpstreamCallParadigms.simultaneous:
            self.upstream_caller = UpstreamCentrifuge(upstream_calls, result_model, nullable_fields=nullable_fields,
                                                      first_call_precedence=first_call_precedence)
        elif paradigm == UpstreamCallParadigms.short_circuit:
            self.upstream_caller = UpstreamShortCircuit(upstream_calls, result_model)
        else:
            raise ValueError("invalid upstream call paradigm")

    async def activate(self):
        return await self.upstream_caller.activate()
