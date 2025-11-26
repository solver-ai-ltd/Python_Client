from ast import literal_eval
import pandas as pd


class SolverAiComputeResults:
    def __init__(self, j: dict):
        self.numberOfResults = j["Number Of Results"]
        self.objectiveVariableNames = \
            literal_eval(j["Objective Variable Names"])
        self.constraintVariableNames = \
            literal_eval(j["Constraint Variable Names"])
        self.inputVariableNames = literal_eval(j["Input Variable Names"])
        self.outputVariableNames = literal_eval(j["Output Variable Names"])
        self.X = [list(literal_eval(j["X" + str(i)]))
                  for i in range(self.numberOfResults)]
        self.Y = [list(literal_eval(j["Y" + str(i)]))
                  for i in range(self.numberOfResults)]

    def getNumberOfResults(self) -> int:
        return self.numberOfResults

    def getObjectiveVariableNames(self) -> list[str]:
        return self.objectiveVariableNames

    def getConstraintVariableNames(self) -> list[str]:
        return self.constraintVariableNames

    def getInputVariableNames(self) -> list[str]:
        return self.inputVariableNames

    def getOutputVariableNames(self) -> list[str]:
        return self.outputVariableNames

    def getX(self):
        return self.X

    def getY(self):
        return self.Y

    def getDataFrame(self) -> pd.DataFrame:
        inputVariableNames = self.getInputVariableNames()
        outputVariableNames = self.getOutputVariableNames()
        X = self.getX()
        keep_idx = \
            [i for i, variable in enumerate(inputVariableNames) if variable not in outputVariableNames]
        if len(keep_idx) != len(inputVariableNames):
            inputVariableNames = [inputVariableNames[i] for i in keep_idx]
            X = [[row[i] for i in keep_idx] for row in X]
        all_var_names = inputVariableNames + outputVariableNames
        all_data = [
            x + y for x, y in zip(X, self.getY())
        ]
        return pd.DataFrame(all_data, columns=all_var_names)
