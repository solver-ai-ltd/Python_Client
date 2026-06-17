# Changelog

## Unreleased

### Added

- `SolverAiProblemStatusInfo` and `getProblemStatusInfo(...)` as the
  status-native surface on `SolverAiClientCompute`
- `getInputsOutputs()` as the preferred problem IO retrieval surface
- `waitForProblemReady(...)` for explicit update-aware waiting before solve
- `SolverAiDrainingException` with stable fields:
  - `status_code`
  - `detail`
  - `retry_after_seconds`

### Changed

- `getProblemSetup()` now serves as a compatibility alias to
  `getInputsOutputs()`
- `runSolver(...)` and `getInputsOutputs()` / `getProblemSetup()` now apply
  bounded controlled-drain handling for exact
  `503 {"detail": "Draining"}` responses
- `runSolver(...)` keeps the existing non-drain `202` setup retry behavior
- `runSolver(...)` does not implicitly perform update-aware waiting; strict
  waiting remains an explicit caller opt-in via `waitForProblemReady(...)`

### Fixed

- metadata-only `patchHardData(...)` and `patchSoftData(...)` paths use JSON
  patching when no replacement file is provided

### Validation

- expanded unit regression coverage in `tests/`
- preserved installed-package smoke coverage through
  `Python_Client_Testing/app/smoke_validate_token.py`
