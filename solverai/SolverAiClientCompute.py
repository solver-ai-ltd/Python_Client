import requests
import json
from time import sleep

from SolverAiComputeInput import SolverAiComputeInput
from SolverAiComputeResults import SolverAiComputeResults
from SolverAiClientExceptions import SetupInExecutionException


class SolverAiClientCompute:

    def __init__(self, computerUrl: str, token: str, problemId: int) -> None:
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

    def getProblemSetup(self):
        headers = self.__headers.copy()
        headers["Content-Type"] = "application/json"
        url = f'{self.__base_url_Computer}problem_setup/{self.__problemId}'
        response = requests.get(url, headers=headers)
        if self.__isStatusCodeOk(response):
            try:
                data = json.loads(response.text)
                return data['inputs'], data['outputs']
            except Exception:
                raise Exception('Failed retrieving data.')
        else:
            raise Exception(f'Failed with code: {json.loads(response.text)}.')

    def _runSolver(self, input: SolverAiComputeInput) -> SolverAiComputeResults:
        headers = self.__headers.copy()
        headers["Content-Type"] = "application/json"
        url = f'{self.__base_url_Computer}solvejson/'
        jsonData = input.getJson()
        response = requests.post(url, headers=headers, data=jsonData)
        if self.__isStatusCodeOk(response):
            if self.__isSetupInExecution(response):
                raise SetupInExecutionException()
            try:
                data = json.loads(response.text)
            except Exception:
                raise Exception('Failed retrieving data.')
            return SolverAiComputeResults(data['results'])
        else:
            raise Exception(f'{json.loads(response.text)}.')

    def runSolver(self, input: SolverAiComputeInput) -> SolverAiComputeResults:
        while True:
            try:
                return self._runSolver(input)
            except SetupInExecutionException:
                sleep(5)
