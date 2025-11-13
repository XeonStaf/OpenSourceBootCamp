### Notes for development
#### Commit syntax
* regex - `^\[[a-z]+\] [A-Za-z]+ [a-z]+\: [a-z0-9]+`
* structure - `[<scope>] <feature-name> <type-of-changes>: <msg>`
* example - `[api] tavily-search feat: implement tool calling`
#### Branch syntax
* regex - `[a-z]+/[a-z0-9\-]+-[a-z0-9\-]+`
* structure - `<scope>/<feature-name>-<short-description>`
* example - `feat/<feature-name>`

### Backend setup & run
1. Install dependencies:
   ```bash
   cd backend
   poetry install
   ```
2. Start the backend service:
   ```bash
   poetry run uvicorn src.main:app --reload
   ```

#### Set up **git hooks**
* `pre-commit install`
* `pre-commit install --install-hooks`
* `pre-commit install --hook-type commit-msg`
