import requests
import json
from dataclasses import dataclass
from time import sleep
from typing import Optional

from .SolverAiComputeInput import SolverAiComputeInput
from .SolverAiComputeResults import SolverAiComputeResults
from .SolverAiClientExceptions import SetupInExecutionException


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

    def __init__(self, computerUrl: str, token: str, problemId: str) -> None:
        self.__base_url_Computer = computerUrl + "/"
        self.__problemId = problemId
        self.__headers = {
            "Authorization": f"Token {token}"
        }

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

    def getInputsOutputs(self):
        headers = self.__headers.copy()
        headers["Content-Type"] = "application/json"
        url = f'{self.__base_url_Computer}problem_setup/{self.__problemId}'
        response = requests.get(url, headers=headers)
        if self.__isStatusCodeOk(response):
            data = self.__parseJsonResponse(response)
            try:
                return data['inputs'], data['outputs']
            except Exception:
                raise Exception('Failed retrieving data.')
        raise Exception(f'Failed with code: {self.__parseJsonResponse(response)}.')

    def getProblemSetup(self):
        return self.getInputsOutputs()

    def _runSolver(self, input: SolverAiComputeInput) -> SolverAiComputeResults:
        headers = self.__headers.copy()
        headers["Content-Type"] = "application/json"
        url = f'{self.__base_url_Computer}solvejson/'
        jsonData = input.getJson()
        response = requests.post(url, headers=headers, data=jsonData)
        if self.__isStatusCodeOk(response):
            if self.__isSetupInExecution(response):
                raise SetupInExecutionException()
            data = self.__parseJsonResponse(response)
            return SolverAiComputeResults(data['results'])
        else:
            raise Exception(f'{self.__parseJsonResponse(response)}.')

    def runSolver(self, input: SolverAiComputeInput) -> SolverAiComputeResults:
        while True:
            try:
                return self._runSolver(input)
            except SetupInExecutionException:
                sleep(5)
