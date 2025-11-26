from SolverAiClientSetup import SolverAiClientSetup

from client_config import token, datamanagerUrl


def main():
    solverAiClientSetup = \
        SolverAiClientSetup(datamanagerUrl, token)

    try:
        # Deleting everything all data
        errors = solverAiClientSetup.deleteProblems() + \
            solverAiClientSetup.deleteEquations() + \
            solverAiClientSetup.deleteCodes() + \
            solverAiClientSetup.deleteSoftDatas() + \
            solverAiClientSetup.deleteHardDatas()

        if len(errors) > 1:
            raise Exception(str(errors))

    except Exception as e:
        print(f'Exception: {str(e)}')


if __name__ == "__main__":
    main()
    exit(0)
