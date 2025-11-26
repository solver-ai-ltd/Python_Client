from enum import Enum
from json import dumps


class CONSTRAINT(Enum):
    SMALLER_THAN = 'smaller than'
    GREATER_THAN = 'greater than'
    EQUAL_TO = 'equal to'
    INSIDE_RANGE = 'inside range'
    OUTSIDE_RANGE = 'outside range'


class OBJECTIVE(Enum):
    MINIMIZE = 'minimize'
    MAXIMIZE = 'maximize'


class SolverAiComputeInput:

    def __init__(self, problem_id, isDebug=False):
        self.problem_id = problem_id
        self.inputs = {}
        self.constraints = {}
        self.objectives = {}
        self.isDebug = isDebug

        self.setSolverSetup()

    def setSolverSetup(
        self,
        includeLeastInfeasible: bool = False,
        solutionQuality: int = 1
    ):
        self.solverSetup = {
            'includeLeastInfeasible': int(includeLeastInfeasible),
            'solutionQuality': solutionQuality
        }

    def addInput(self,
                 name, Min, Max=0,
                 is_constant=False, is_integer=False):
        if Min == Max:
            is_constant = True
        self.inputs[name] = {
            'Min': Min,
            'Max': Max,
            'Constant': is_constant,
            'Integer': is_integer
        }

    def addConstraint(self, name, operation, value1, value2=0):
        self.constraints[name] = {
            'Operation': operation.value,
            'Value1': value1,
            'Value2': value2
        }

    def addObjective(self, name, operation):
        self.objectives[name] = {
            'Operation': operation.value}

    def getJson(self):
        return dumps({
            'id': self.problem_id,
            'solverSetup': self.solverSetup,
            'inputs': self.inputs,
            'constraints': self.constraints,
            'objectives': self.objectives,
            'isDebug': self.isDebug
        })
