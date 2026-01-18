import json
from os import remove, path


class IdsDataManager:
    def __init__(self, filepath: str = None) -> None:
        self.__filepath = filepath
        self.__data = None

    def write(
        self,
        equation_ids,
        code_ids,
        hard_data_ids,
        soft_data_ids,
        problem_id
    ):
        self.storeInMemory(
            equation_ids,
            code_ids,
            hard_data_ids,
            soft_data_ids,
            problem_id
        )
        with open(self.__filepath, 'w') as f:
            json.dump(self.__data, f)

    def storeInMemory(
        self,
        equation_ids,
        code_ids,
        hard_data_ids,
        soft_data_ids,
        problem_id
    ):
        self.__data = {
            'equation_ids': equation_ids,
            'code_ids': code_ids,
            'hard_data_ids': hard_data_ids,
            'soft_data_ids': soft_data_ids,
            'problem_id': problem_id
        }

    def retrieveFromMemory(self):
        return self.__data['equation_ids'], \
            self.__data['code_ids'], \
            self.__data['hard_data_ids'], \
            self.__data['soft_data_ids'], \
            self.__data['problem_id']

    def fileExists(self):
        return path.exists(self.__filepath)

    def read(self):
        with open(self.__filepath, 'r') as f:
            self.__data = json.load(f)
        return self.retrieveFromMemory()

    def getEquationIds(self):
        return self.__data['equation_ids']

    def getCodeIds(self):
        return self.__data['code_ids']

    def getHardDataIds(self):
        return self.__data['hard_data_ids']

    def getSoftDataIds(self):
        return self.__data['soft_data_ids']

    def getProblemId(self):
        return self.__data['problem_id']

    def readProblemId(self):
        with open(self.__filepath, 'r') as f:
            self.__data = json.load(f)
        return self.getProblemId()

    def removeFile(self):
        remove(self.__filepath)
