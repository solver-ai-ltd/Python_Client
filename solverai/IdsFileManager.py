import json
from os import remove, path


class IdsFileManager:
    def __init__(self, filepath) -> None:
        self.__filepath = filepath

    def write(
        self,
        equation_ids,
        code_ids,
        hard_data_ids,
        soft_data_ids,
        problem_id
    ):
        data = {
            'equation_ids': equation_ids,
            'code_ids': code_ids,
            'hard_data_ids': hard_data_ids,
            'soft_data_ids': soft_data_ids,
            'problem_id': problem_id
        }
        with open(self.__filepath, 'w') as f:
            json.dump(data, f)

    def fileExists(self):
        return path.exists(self.__filepath)

    def read(self):
        with open(self.__filepath, 'r') as f:
            data = json.load(f)
        return data['equation_ids'], data['code_ids'], data['hard_data_ids'], \
            data['soft_data_ids'], data['problem_id']

    def readProblemId(self):
        with open(self.__filepath, 'r') as f:
            data = json.load(f)
        return data['problem_id']

    def removeFile(self):
        remove(self.__filepath)
