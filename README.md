# SOLVER-AI Python Client

`solverai` is the Python client package for working with the SOLVER-AI
DataManager and Computer APIs.

Current package version in `pyproject.toml`: `2025.1.0a16`

## Requirements

- Python `>=3.9`
- a SOLVER-AI API token
- a DataManager URL
- a Computer URL

## Repository Layout

- `solverai/`: installable Python package
- `setup/`: example `setup.txt`
- `tests/`: unit regression suite

## Setup File

`get_setup_data(...)` reads a plain-text setup file like:

```text
token=<your-token>
datamanagerUrl=http://datamanagerapi:8000
computerUrl=http://computer:8001
```

Example:

```python
from solverai import get_setup_data

token, datamanager_url, computer_url = get_setup_data("setup/setup.txt")
```

`validate_token(datamanager_url, token)` can be used to verify the token before
running setup or solve flows.

## Public Surface

Top-level imports currently exposed by `solverai`:

- `get_setup_data`
- `validate_token`
- `IdsDataManager`
- `SolverAiClientSetup`
- `SolverAiClientCompute`
- `SolverAiProblemStatusInfo`
- `SetupInExecutionException`
- `SolverAiDrainingException`
- `SolverAiComputeInput`
- `SolverAiComputeResults`
- `SolverAiResultsWriter`

## Setup Flow

`SolverAiClientSetup` is the DataManager-side client for creating and updating
problems and their associated data.

Typical workflow:

```python
from solverai import SolverAiClientSetup

setup_client = SolverAiClientSetup(datamanager_url, token)
```

Representative methods include:

- `postEquation(...)`
- `postCode(...)`
- `postHardData(...)`
- `postSoftData(...)`
- `patchSoftData(...)`
- `postProblem(...)`
- `deleteAll(...)`

## Compute Flow

`SolverAiClientCompute` is the Computer-side client for status checks, problem
IO discovery, and solve calls.

```python
from solverai import SolverAiClientCompute, SolverAiComputeInput

compute_client = SolverAiClientCompute(computer_url, token, problem_id)
compute_input = SolverAiComputeInput(problem_id)
compute_input.addInput("x", 0.0, 1.0)
results = compute_client.runSolver(compute_input)
```

`runSolver(...)` keeps the current non-drain setup behavior: if the Computer
returns the existing non-drain `202` setup-in-execution path, the client keeps
retrying every 5 seconds until setup completes.

## Status And IO Surfaces

For new code, prefer the split surfaces below:

- `getProblemStatusInfo(require_not_updating=False)`:
  returns a `SolverAiProblemStatusInfo` object describing coarse problem state
- `getInputsOutputs()`:
  returns `(inputs, outputs)` for the problem-setup surface
- `getProblemSetup()`:
  compatibility alias to `getInputsOutputs()`

Legacy note:

- `getProblemStatus()` is still present for backward compatibility, but it
  should be treated as a legacy surface.
- New code should not use `getProblemStatus()` for new status or IO flows.

Example status usage:

```python
status_info = compute_client.getProblemStatusInfo()
if status_info.is_ready:
    print("ready")
elif status_info.is_processing:
    print("processing")
elif status_info.is_updating:
    print("updating")
```

## Update-Aware Waiting

`waitForProblemReady(...)` is the explicit helper for callers that need to wait
for the problem to become ready before solving.

Signature:

```python
waitForProblemReady(
    require_not_updating: bool = False,
    poll_interval_seconds: float = 1.0,
    max_wait_seconds: float | None = None,
)
```

Behavior:

- returns the final `SolverAiProblemStatusInfo` once the problem is ready
- when `require_not_updating=False`, waits through `PROCESSING`
- when `require_not_updating=True`, waits through both `PROCESSING` and
  `UPDATING`
- raises `RuntimeError` immediately on terminal `ERROR`
- raises `RuntimeError` immediately on `NOT_READY`
- raises `TimeoutError` if `max_wait_seconds` is exceeded

Important:

- `runSolver()` does not implicitly call `waitForProblemReady(...)`
- callers that require strict update-complete behavior should explicitly call
  `waitForProblemReady(require_not_updating=True)` before `runSolver()`

Example:

```python
compute_client.waitForProblemReady(
    require_not_updating=True,
    poll_interval_seconds=1.0,
    max_wait_seconds=120.0,
)
results = compute_client.runSolver(compute_input)
```

## Controlled Drain Handling

The client now treats controlled drain as a distinct transient condition on the
Computer acceptance surfaces.

Controlled drain detection is limited to responses where:

- the HTTP status is `503`
- the body parses as JSON
- the parsed object contains `{"detail": "Draining"}`

This handling applies to:

- `runSolver(...)`
- `getInputsOutputs()`
- `getProblemSetup()`

It does not apply to:

- `getProblemStatusInfo(...)`
- legacy `getProblemStatus()`

When the client encounters controlled drain, it raises
`SolverAiDrainingException` after the configured bounded retry policy is
exhausted. The exception exposes stable fields:

- `status_code`
- `detail`
- `retry_after_seconds`

`SolverAiClientCompute(...)` drain-related constructor options:

```python
SolverAiClientCompute(
    computer_url,
    token,
    problem_id,
    drain_max_retries=1,
    drain_retry_default_seconds=60,
    honor_retry_after=True,
    drain_max_wait_seconds=None,
)
```

Default behavior:

- one automatic retry after a controlled-drain response
- honor `Retry-After` when present and valid
- otherwise fall back to `drain_retry_default_seconds` plus small jitter

Fail-fast example:

```python
compute_client = SolverAiClientCompute(
    computer_url,
    token,
    problem_id,
    drain_max_retries=0,
)
```

## Testing

Unit tests:

```bash
cd temp_external_code/example_APIs/Python_Client
python3 -m unittest discover -s tests
```

Local harness smoke:

```bash
docker compose -p solver-production-local-localdb \
  -f docker-compose/docker-compose-production-local-localDB.yaml up -d

SOLVERAI_TEST_TOKEN=<local testing-user token> \
  docker compose \
  -f temp_external_code/example_APIs/Python_Client_Testing/docker-compose-testing-local.yaml \
  run --rm --build python-client-testing

docker compose -p solver-production-local-localdb \
  -f docker-compose/docker-compose-production-local-localDB.yaml down
```

## Release Notes

See `CHANGELOG.md` for the current branch-local change summary.
