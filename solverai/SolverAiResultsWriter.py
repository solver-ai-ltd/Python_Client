import csv
import SolverAiComputeResults


class SolverAiResultsWriter:
    def __init__(self, results: SolverAiComputeResults) -> None:
        self.results = results

    def write(self, path: str) -> None:
        with open(path, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Number Of Results",
                             self.results.getNumberOfResults()])
            writer.writerow(["Objective Variable Names"] +
                            self.results.getObjectiveVariableNames())
            writer.writerow(["Constraint Variable Names"] +
                            self.results.getConstraintVariableNames())
            writer.writerow([])

            writer.writerow(['Inputs'])
            input_names = self.results.getInputVariableNames()
            writer.writerow(['#'] + input_names)
            for i, x in enumerate(self.results.getX()):
                writer.writerow([f"X{i}"] + x)

            writer.writerow([])
            writer.writerow(['Outputs'])
            output_names = self.results.getOutputVariableNames()
            writer.writerow(['#'] + output_names)
            for i, y in enumerate(self.results.getY()):
                writer.writerow([f"Y{i}"] + y)
