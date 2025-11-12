### Notes for development
#### Commit syntax
* regex - `^\[[a-z]+\] [A-Z0-9]+ [a-z]+\: [a-z0-9]+`
* structure - `[<scope>] <task_id> <type-of-changes>: <msg>`
* example - `[api] TRQ-0 feat: implement dto validation`
#### Branch syntax
* regex - `[a-z]+/[a-z0-9\-]+-[a-z0-9\-]+`
* structure - `<scope>/<task-id>-<short-description>`
* example - `feat/osbc-000`

#### Set up **git hooks**
* `pre-commit install`
* `pre-commit install --install-hooks`
* `pre-commit install --hook-type commit-msg`
