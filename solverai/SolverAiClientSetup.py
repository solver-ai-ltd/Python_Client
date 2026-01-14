from typing import Union
from re import escape
from requests import get, post, patch, delete
from json import loads, dumps
from re import search
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import io

import pandas as pd


class SolverAiClientSetup:

    class ID:
        def __init__(self, urlSuffix: str, id: int) -> None:
            self.urlSuffix = urlSuffix
            self.id = id

    def __init__(
        self,
        datamanagerUrl: str,
        token: str,
        post_batch: bool = False
    ) -> None:
        self.__base_url_DM = datamanagerUrl + "/api/data/"
        self.__headers = {
            "Authorization": f"Token {token}"
        }
        self.__equationSuffix = "equations"
        self.__codeSuffix = "code"
        self.__hardDataSuffix = "hard-datas"
        self.__softDataSuffix = "soft-datas"
        self.__problemSuffix = "problems"

        self.__post_batch = post_batch
        self.__post_batch_queue = []

    def _postPatch(self, urlSuffix, data: dict, filePath_or_df: tuple, id=None):
        """
        When batching is ON, this only queues the request and returns None.
        When batching is OFF, it executes immediately and returns the
        created/updated id.
        filePath_or_df: Optional tuple (file_path or DataFrame, field_name) or None
        """
        if self.__post_batch:
            self.__post_batch_queue.append({
                "urlSuffix": urlSuffix,
                "data": deepcopy(data),
                "filePath_or_df": filePath_or_df if filePath_or_df is not None else None,
                "id": id
            })
            return None

        # immediate mode
        return self.__execute_postpatch(urlSuffix, data, filePath_or_df, id)

    def __execute_postpatch(self, urlSuffix, data: dict, filePath_or_df: tuple, id=None):
        isPost = True
        if id is not None:
            isPost = False

        if isPost:
            url = f'{self.__base_url_DM}{urlSuffix}/'
            httpFunction = post
        else:
            url = f'{self.__base_url_DM}{urlSuffix}/{id}/'
            httpFunction = patch

        tempData = data.copy()
        if 'vectorizationIndices' in tempData and \
                not tempData['vectorizationIndices']:
            tempData.pop('vectorizationIndices')
        if filePath_or_df is not None:
            try:
                is_close = False
                file_content, is_close = self.__post_patch_data_processor(filePath_or_df[0])
                response = httpFunction(
                    url, headers=self.__headers, data=tempData,
                    files={filePath_or_df[1]: file_content}
                )
            finally:
                if is_close:
                    file_content.close()
        else:  # If no files, convert data to a JSON string
            headers = self.__headers.copy()
            headers["Content-Type"] = "application/json"
            jsonData = dumps(tempData)
            response = httpFunction(
                url, headers=headers, data=jsonData
            )

        return self.__processResponse(response)

    @staticmethod
    def __post_patch_data_processor(data: Union['str', pd.DataFrame]):
        if isinstance(data, pd.DataFrame):
            buffer = io.StringIO()
            data.to_csv(buffer, index=False)
            buffer.seek(0)
            file_content = ('data.csv', buffer, 'text/csv')
            is_close = False
        else:
            file_content = open(data, 'rb')
            is_close = True
        return file_content, is_close

    def flush_post_batch(self, max_workers: int = None):
        if not self.__post_batch_queue:
            raise Exception('Batch not setup')

        def run_one(item, idx):
            name = item["data"]["name"]
            suffix = item["urlSuffix"]
            try:
                return True, idx, self.__execute_postpatch(
                    suffix, item["data"], item["filePath_or_df"], item["id"]
                ), suffix, name
            except Exception as e:
                return False, idx, e, suffix, name

        results = {}
        errors = []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(run_one, item, idx)
                for idx, item in enumerate(self.__post_batch_queue)
            ]
            # Preserve order by reading futures in submission order
            for fut in futures:
                status, idx, res, urlSuffix, name = fut.result()
                if status:
                    if urlSuffix not in results:
                        results[urlSuffix] = [res]
                    else:
                        results[urlSuffix].append(res)
                else:
                    errors.append(
                        f"[{urlSuffix}, {idx}, {name}] "
                        f"{type(res).__name__}: {res}"
                    )

        self.__post_batch_queue = []

        def getIds(suffix: str):
            return results[suffix] if suffix in results else []

        equationIds = getIds(self.__equationSuffix)
        codeIds = getIds(self.__codeSuffix)
        hardIds = getIds(self.__hardDataSuffix)
        softIds = getIds(self.__softDataSuffix)
        if self.__problemSuffix in results:
            problemId = results[self.__problemSuffix][0]
        else:
            problemId = None

        if errors:
            if self.__problemSuffix in results:
                problemId = results[self.__problemSuffix][0]
            else:
                problemId = None
            self.deleteAll(
                equationIds=equationIds,
                codeIds=codeIds,
                hardIds=hardIds,
                softIds=softIds,
                problemId=problemId
            )

            raise Exception((
                "Batch post completed with errors. "
                "Errors:\n" + "\n".join(errors)
            ))

        return equationIds, codeIds, hardIds, softIds, problemId

    @staticmethod
    def __isStatusCodeOk(response):
        statusCode = response.status_code
        return 200 <= statusCode and statusCode < 300

    def __processResponse(self, response):
        if self.__isStatusCodeOk(response):
            try:
                data = loads(response.text)
            except Exception:
                raise Exception('Failed retrieving data.')
            return data['id']
        else:
            raise Exception(f'Failed with code: {loads(response.text)}.')

    def __getIds(self, urlSuffix: str, nameRegex: str):
        url = f'{self.__base_url_DM}{urlSuffix}/'
        headers = self.__headers.copy()
        response = get(
            url, headers=headers
        )
        if response.status_code != 200:
            raise Exception(loads(response.text)['detail'])
        try:
            data = loads(response.text)
        except Exception:
            raise Exception('Failed retrieving data.')

        ids = list()
        for module in data:
            if search(nameRegex, module['name']):
                ids.append(module['id'])

        return ids

    def deleteAll(
        self,
        equationIds=[],
        codeIds=[],
        hardIds=[],
        softIds=[],
        problemId=None
    ):
        all_errors = []
        errors = ''
        try:
            if problemId is not None:
                # Problem must be deleted first or will not allow deletion
                # of models
                if isinstance(problemId, str):
                    self.__deleteIds(
                        self.__problemSuffix, [problemId], all_errors
                    )
                elif isinstance(problemId, list) \
                        and all(isinstance(x, str) for x in problemId):
                    self.__deleteIds(
                        self.__problemSuffix, problemId, all_errors
                    )
                else:
                    raise Exception('Wrong type for problemId')
            self.__deleteIds(self.__equationSuffix, equationIds, all_errors)
            self.__deleteIds(self.__codeSuffix, codeIds, all_errors)
            self.__deleteIds(self.__hardDataSuffix, hardIds, all_errors)
            self.__deleteIds(self.__softDataSuffix, softIds, all_errors)
            errors = "\n".join(all_errors)
        except Exception:
            raise Exception(f'Failed Deleting With Errors:\n{errors}')
        if len(errors):
            raise Exception(errors)

    def __deleteId(self, urlSuffix: str, id: str) -> str:
        error = ''
        url = f'{self.__base_url_DM}{urlSuffix}/{id}/'
        response = delete(url, headers=self.__headers)
        if not self.__isStatusCodeOk(response):
            error = f'Failed Deleting: {url}\n'
        return error

    def __deleteIds(
        self,
        urlSuffix: str,
        ids: list,
        all_errors: list = None
    ):
        errors_list = []

        with ThreadPoolExecutor() as executor:
            # submit tasks in the same order as ids
            futures = [executor.submit(self.__deleteId, urlSuffix, id)
                       for id in ids]

            # collect results in order of submission, not completion
            for future in futures:
                errors_list.append(future.result())

        clean_errors_list = [error for error in errors_list if error]

        if all_errors is None:
            return "\n".join(clean_errors_list)
        else:
            all_errors.extend(clean_errors_list)

    def __deleteModules(self, urlSuffix: str, nameRegex: str):
        ids = self.__getIds(urlSuffix, nameRegex)
        return self.__deleteIds(urlSuffix, ids)

    def deleteEquation(self, id: int):
        return self.__deleteId(self.__equationSuffix, id)

    def deleteCode(self, id: int):
        return self.__deleteId(self.__codeSuffix, id)

    def deleteHardData(self, id: int):
        return self.__deleteId(self.__hardDataSuffix, id)

    def deleteSoftData(self, id: int):
        return self.__deleteId(self.__softDataSuffix, id)

    def deleteProblem(self, id: int):
        return self.__deleteId(self.__problemSuffix, id)

    def deleteEquations(self, nameRegex: str = ".*"):
        return self.__deleteModules(self.__equationSuffix, nameRegex)

    def deleteCodes(self, nameRegex: str = ".*"):
        return self.__deleteModules(self.__codeSuffix, nameRegex)

    def deleteHardDatas(self, nameRegex: str = ".*"):
        return self.__deleteModules(self.__hardDataSuffix, nameRegex)

    def deleteSoftDatas(self, nameRegex: str = ".*"):
        return self.__deleteModules(self.__softDataSuffix, nameRegex)

    def deleteProblems(self, nameRegex: str = ".*"):
        return self.__deleteModules(self.__problemSuffix, nameRegex)

    def postEquation(
        self,
        name: str,
        equationString: str,
        variablesString: str,
        vectorizationIndices: str = ''
    ):
        data = {
            "name": name,
            "equationString": equationString,
            "variablesString": variablesString,
            "vectorizationIndices": vectorizationIndices
        }
        return self._postPatch(self.__equationSuffix, data, None)

    def patchEquation(
        self,
        id: int,
        name: str = '',
        equationString: str = '',
        variablesString: str = '',
        vectorizationIndices: str = ''
    ):
        data = dict()
        if name:
            data['name'] = name
        if equationString:
            data['equationString'] = equationString
        if variablesString:
            data['variablesString'] = variablesString
        if vectorizationIndices:
            data['vectorizationIndices'] = vectorizationIndices
        return self._postPatch(self.__equationSuffix, data, None, id)

    def postCode(
        self,
        name: str,
        filePath: str,
        variablesStringIn: str,
        variablesStringOut: str,
        vectorizationIndices: str = ''
    ):
        file = (filePath, 'code')
        data = {
            "name": name,
            "variablesStringIn": variablesStringIn,
            "variablesStringOut": variablesStringOut,
            "vectorizationIndices": vectorizationIndices
        }
        return self._postPatch(self.__codeSuffix, data, file)

    def patchCode(
        self,
        id: int,
        name: str = '',
        filePath: str = '',
        variablesStringIn: str = '',
        variablesStringOut: str = '',
        vectorizationIndices: str = ''
    ):
        file = None
        if filePath:
            file = (filePath, 'code')
        data = dict()
        if name:
            data['name'] = name
        if variablesStringIn:
            data['variablesStringIn'] = variablesStringIn
        if variablesStringOut:
            data['variablesStringOut'] = variablesStringOut
        if vectorizationIndices:
            data['vectorizationIndices'] = vectorizationIndices
        return self._postPatch(self.__codeSuffix, data, file, id)

    def postHardData(
        self,
        name: str,
        filePath_or_df: Union[str, pd.DataFrame],
        vectorizationIndices: str = ''
    ):
        _filePath_or_df = (filePath_or_df, 'csv')
        data = {
            "name": name,
            "vectorizationIndices": vectorizationIndices
        }
        return self._postPatch(self.__hardDataSuffix, data, _filePath_or_df)

    def patchHardData(
        self,
        id: int,
        name: str = '',
        filePath_or_df: Union[str, pd.DataFrame] = None,
        vectorizationIndices: str = ''
    ):
        _filePath_or_df = None
        if filePath_or_df is not None or filePath_or_df != '':
            _filePath_or_df = (filePath_or_df, 'csv')
        data = dict()
        if name:
            data['name'] = name
        if vectorizationIndices:
            data['vectorizationIndices'] = vectorizationIndices
        return self._postPatch(self.__hardDataSuffix, data, _filePath_or_df, id)

    def postSoftData(
        self,
        name: str,
        filePath_or_df: Union[str, pd.DataFrame],
        variablesStringIn: str,
        variablesStringOut: str,
        vectorizationIndices: str = '',
        categoricalVariablesStringIn: str = ''
    ):
        _filePath_or_df = (filePath_or_df, 'csv')
        data = {
            "name": name,
            "variablesStringIn": variablesStringIn,
            "variablesStringOut": variablesStringOut,
            "vectorizationIndices": vectorizationIndices,
            "categoricalVariablesStringIn": categoricalVariablesStringIn
        }
        return self._postPatch(self.__softDataSuffix, data, _filePath_or_df)

    def patchSoftData(
        self,
        id: int,
        name: str = '',
        filePath_or_df: Union[str, pd.DataFrame] = None,
        variablesStringIn: str = '',
        variablesStringOut: str = '',
        vectorizationIndices: str = '',
        categoricalVariablesStringIn: str = ''
    ):
        _filePath_or_df = None
        if filePath_or_df is not None or filePath_or_df != '':
            _filePath_or_df = (filePath_or_df, 'csv')
        data = dict()
        if name:
            data['name'] = name
        if variablesStringIn:
            data['variablesStringIn'] = variablesStringIn
        if variablesStringOut:
            data['variablesStringOut'] = variablesStringOut
        if vectorizationIndices:
            data['vectorizationIndices'] = vectorizationIndices
        if categoricalVariablesStringIn:
            data['categoricalVariablesStringIn'] = categoricalVariablesStringIn
        return self._postPatch(self.__softDataSuffix, data, _filePath_or_df, id)

    def postProblem(
        self,
        name: str,
        equationIds=list(),
        codeIds=list(),
        hardIds=list(),
        softIds=list()
    ):
        data = {
            "name": name,
            "equations": equationIds,
            "codes": codeIds,
            "harddatas": hardIds,
            "softdatas": softIds,
            "tags": []
        }
        return self._postPatch(self.__problemSuffix, data, None)

    def patchProblem(
        self,
        id: int,
        name: str = '',
        equationIds=list(),
        codeIds=list(),
        hardIds=list(),
        softIds=list()
    ):
        data = dict()
        if name:
            data['name'] = name
        if len(equationIds):
            data['equations'] = equationIds
        if len(codeIds):
            data['codes'] = codeIds
        if len(hardIds):
            data['harddatas'] = hardIds
        if len(softIds):
            data['softdatas'] = softIds
        return self._postPatch(self.__problemSuffix, data, None, id)

    def __getOne(self, urlSuffix: str, id: str) -> dict:
        """GET /<urlSuffix>/<id>/ and return parsed JSON dict."""
        url = f'{self.__base_url_DM}{urlSuffix}/{id}/'
        response = get(url, headers=self.__headers)
        if not self.__isStatusCodeOk(response):
            # keep error style consistent with your other methods
            try:
                raise Exception(loads(response.text).get('detail', response.text))
            except Exception:
                raise Exception(f"Failed GET: {url} (status={response.status_code})")

        try:
            return loads(response.text)
        except Exception:
            raise Exception("Failed retrieving data.")

    def getProblemModuleIdsByName(self, problem_name: str):
        """
        Given a problem name (exact match), returns:
          (problem_id, equation_ids, code_ids, harddata_ids, softdata_ids)

        Note:
        - If multiple problems share the same name, this returns the most recent one
          (because the API list is ordered by -dateTime, -id in get_queryset()).
        """
        # Exact match (escape to avoid regex surprises)
        nameRegex = f"^{escape(problem_name)}$"

        problem_ids = self.__getIds(self.__problemSuffix, nameRegex)
        if not problem_ids:
            raise Exception(f"No problem found with name='{problem_name}'")

        problem_id = problem_ids[0]  # most recent match
        detail = self.__getOne(self.__problemSuffix, problem_id)

        equation_ids = detail.get("equations", []) or []
        code_ids = detail.get("codes", []) or []
        harddata_ids = detail.get("harddatas", []) or []
        softdata_ids = detail.get("softdatas", []) or []

        return problem_id, equation_ids, code_ids, harddata_ids, softdata_ids
