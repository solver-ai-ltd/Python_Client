import requests
import json
import math
import random
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from time import monotonic, sleep
from typing import Optional

from .SolverAiComputeInput import SolverAiComputeInput
from .SolverAiComputeResults import SolverAiComputeResults
from .SolverAiClientExceptions import (
    SetupInExecutionException,
    SolverAiDrainingException,
)


@dataclass(frozen=True)
class SolverAiProblemStatusInfo:
    http_status_code: int
    state: str
    detail: str
    is_ready: bool
    is_processing: bool
    is_error: bool
    is_updating: bool = False
    require_not_updating: bool = False
    raw_status_text: str = ''
    error_origin: Optional[str] = None


class SolverAiClientCompute:

    def __init__(
        self,
        computerUrl: str,
        token: str,
        problemId: str,
        drain_max_retries: int = 1,
        drain_retry_default_seconds: float = 60,
        honor_retry_after: bool = True,
        drain_max_wait_seconds: Optional[float] = None,
    ) -> None:
        self.__base_url_Computer = computerUrl + "/"
        self.__problemId = problemId
        self.__headers = {
            "Authorization": f"Token {token}"
        }
        self.__drain_max_retries = drain_max_retries
        self.__drain_retry_default_seconds = drain_retry_default_seconds
        self.__honor_retry_after = honor_retry_after
        self.__drain_max_wait_seconds = drain_max_wait_seconds

    @staticmethod
    def __isStatusCodeOk(response):
        statusCode = response.status_code
        return 200 <= statusCode and statusCode < 300

    @staticmethod
    def __isSetupInExecution(response):
        statusCode = response.status_code
        return statusCode == 202

    def getProblemStatus(self):
        headers = self.__headers.copy()
        headers["Content-Type"] = "application/json"
        url = (f'{self.__base_url_Computer}'
               f'check_problem_status/{self.__problemId}')
        response = requests.get(url, headers=headers)
        if self.__isStatusCodeOk(response):
            try:
                data = json.loads(response.text)
                return data['inputs'], data['outputs']
            except Exception:
                raise Exception('Failed retrieving data.')
        else:
            raise Exception(f'Failed with code: {json.loads(response.text)}.')

    @staticmethod
    def __parseJsonResponse(response):
        try:
            return json.loads(response.text)
        except Exception:
            raise Exception('Failed retrieving data.')

    @staticmethod
    def __parseRetryAfterSeconds(retry_after_value):
        if retry_after_value is None:
            return None

        stripped_value = str(retry_after_value).strip()
        if not stripped_value:
            return None

        try:
            parsed_seconds = float(stripped_value)
            if not math.isfinite(parsed_seconds):
                return None
            if parsed_seconds < 0:
                return 0.0
            return parsed_seconds
        except ValueError:
            pass

        try:
            parsed_datetime = parsedate_to_datetime(stripped_value)
            if parsed_datetime.tzinfo is None:
                parsed_datetime = parsed_datetime.replace(tzinfo=timezone.utc)
            wait_seconds = (
                parsed_datetime - datetime.now(timezone.utc)
            ).total_seconds()
            if wait_seconds < 0:
                return 0.0
            return wait_seconds
        except Exception:
            return None

    @classmethod
    def __isControlledDraining(cls, response):
        if response.status_code != 503:
            return False

        try:
            data = json.loads(response.text)
        except Exception:
            return False

        return isinstance(data, dict) and data.get("detail") == "Draining"

    @classmethod
    def __buildDrainingException(cls, response):
        headers = getattr(response, "headers", {}) or {}
        return SolverAiDrainingException(
            status_code=response.status_code,
            detail="Draining",
            retry_after_seconds=cls.__parseRetryAfterSeconds(
                headers.get("Retry-After")
            ),
        )

    @staticmethod
    def __normalizeStatusState(status_code, raw_status_text):
        normalized_text = raw_status_text.strip()
        lowered_text = normalized_text.lower()

        if status_code == 200 and lowered_text == 'ready':
            return 'READY'
        if status_code == 202 and lowered_text == 'setup in execution':
            return 'PROCESSING'
        if status_code == 202 and lowered_text == 'updating':
            return 'UPDATING'
        if status_code == 400 and normalized_text.startswith('NOT_READY:'):
            return 'NOT_READY'
        if status_code == 400 and normalized_text.startswith('ERROR:'):
            return 'ERROR'
        raise Exception(f'Failed with code: {raw_status_text}.')

    def getProblemStatusInfo(self, require_not_updating: bool = False):
        headers = self.__headers.copy()
        headers["Content-Type"] = "application/json"
        url = (f'{self.__base_url_Computer}'
               f'check_problem_status/{self.__problemId}')
        params = None
        if require_not_updating:
            params = {"require_not_updating": "true"}
        response = requests.get(url, headers=headers, params=params)
        if response.status_code not in {200, 202, 400}:
            raise Exception(
                f'Failed with code: {self.__parseJsonResponse(response)}.'
            )

        raw_status_text = self.__parseJsonResponse(response)
        if not isinstance(raw_status_text, str):
            raise Exception('Failed retrieving data.')

        state = self.__normalizeStatusState(
            response.status_code,
            raw_status_text,
        )

        return SolverAiProblemStatusInfo(
            http_status_code=response.status_code,
            state=state,
            detail=raw_status_text,
            is_ready=state == 'READY',
            is_processing=state == 'PROCESSING',
            is_error=state == 'ERROR',
            is_updating=state == 'UPDATING',
            require_not_updating=require_not_updating,
            raw_status_text=raw_status_text,
            error_origin='unknown' if state == 'ERROR' else None,
        )

    def waitForProblemReady(
        self,
        require_not_updating: bool = False,
        poll_interval_seconds: float = 1.0,
        max_wait_seconds: Optional[float] = None,
    ) -> SolverAiProblemStatusInfo:
        deadline = None
        if max_wait_seconds is not None:
            deadline = monotonic() + max_wait_seconds

        has_polled = False
        while True:
            if has_polled and deadline is not None and monotonic() >= deadline:
                raise TimeoutError(
                    'Timed out waiting for the problem to become ready.'
                )

            status_info = self.getProblemStatusInfo(
                require_not_updating=require_not_updating,
            )
            has_polled = True

            if status_info.is_ready:
                return status_info

            if status_info.is_error:
                raise RuntimeError(
                    f'Problem entered terminal state: '
                    f'{status_info.state} ({status_info.detail}).'
                )

            if status_info.state == 'NOT_READY':
                raise RuntimeError(
                    f'Problem is not ready to wait on: '
                    f'{status_info.detail}.'
                )

            is_transient_processing = status_info.is_processing
            is_transient_updating = (
                require_not_updating and status_info.is_updating
            )
            if not (is_transient_processing or is_transient_updating):
                raise RuntimeError(
                    f'Unexpected wait state: '
                    f'{status_info.state} ({status_info.detail}).'
                )

            if deadline is None:
                sleep(poll_interval_seconds)
                continue

            remaining_seconds = deadline - monotonic()
            if remaining_seconds <= 0:
                raise TimeoutError(
                    'Timed out waiting for the problem to become ready.'
                )

            sleep(min(poll_interval_seconds, remaining_seconds))

    def __runWithDrainRetry(self, operation):
        drain_retries_used = 0
        drain_wait_used = 0.0

        while True:
            try:
                return operation()
            except SolverAiDrainingException as error:
                if drain_retries_used >= self.__drain_max_retries:
                    raise

                wait_seconds = None
                if (
                    self.__honor_retry_after
                    and error.retry_after_seconds is not None
                ):
                    wait_seconds = error.retry_after_seconds
                else:
                    wait_seconds = (
                        self.__drain_retry_default_seconds + random.random()
                    )

                if (
                    self.__drain_max_wait_seconds is not None
                    and drain_wait_used + wait_seconds >
                    self.__drain_max_wait_seconds
                ):
                    raise

                sleep(wait_seconds)
                drain_retries_used += 1
                drain_wait_used += wait_seconds

    def __getInputsOutputsOnce(self):
        headers = self.__headers.copy()
        headers["Content-Type"] = "application/json"
        url = f'{self.__base_url_Computer}problem_setup/{self.__problemId}'
        response = requests.get(url, headers=headers)
        if self.__isControlledDraining(response):
            raise self.__buildDrainingException(response)
        if self.__isStatusCodeOk(response):
            data = self.__parseJsonResponse(response)
            try:
                return data['inputs'], data['outputs']
            except Exception:
                raise Exception('Failed retrieving data.')
        raise Exception(f'Failed with code: {self.__parseJsonResponse(response)}.')

    def getInputsOutputs(self):
        return self.__runWithDrainRetry(self.__getInputsOutputsOnce)

    def getProblemSetup(self):
        return self.getInputsOutputs()

    def _runSolver(self, input: SolverAiComputeInput) -> SolverAiComputeResults:
        headers = self.__headers.copy()
        headers["Content-Type"] = "application/json"
        url = f'{self.__base_url_Computer}solvejson/'
        jsonData = input.getJson()
        response = requests.post(url, headers=headers, data=jsonData)
        if self.__isControlledDraining(response):
            raise self.__buildDrainingException(response)
        if self.__isStatusCodeOk(response):
            if self.__isSetupInExecution(response):
                raise SetupInExecutionException()
            data = self.__parseJsonResponse(response)
            return SolverAiComputeResults(data['results'])
        else:
            raise Exception(f'{self.__parseJsonResponse(response)}.')

    def runSolver(self, input: SolverAiComputeInput) -> SolverAiComputeResults:
        def run_until_setup_complete():
            while True:
                try:
                    return self._runSolver(input)
                except SetupInExecutionException:
                    sleep(5)

        return self.__runWithDrainRetry(run_until_setup_complete)
