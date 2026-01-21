# AGENTS.md



## Setup commands
- Create a virtual environment: `uv venv create`
- Install dependencies: `uv pip install -e .`
- uv run uvicorn rentabot.main:app --reload --port 8000

## Code style
- Check code formatting with ruff: `ruff format --check .`
- Lint code with ruff: `ruff check .`
- Format code with ruff: `ruff format .`
- Don't use emojis unless specified

## Testing
- Run tests with pytest: `uv run pytest tests/`

## Documentation
- Use markdown for documentation.
- Document only when asked.
- Use emojis sparingly or when specified.
- Write clear and concise documentation.
- Follow the project's style and tone.

## Versionning
- Use semantic versioning 2.0 (https://semver.org/spec/v2.0.0.html)
