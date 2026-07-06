# LLM Cost Lens

| Field | Value |
| --- | --- |
| Category | model quality |
| Command | `llm-cost-lens` |
| Inputs | `examples/openai_calls.jsonl` |

Inspect LLM API logs for cost, latency, budget, and usage anomalies. This repo keeps the work close to the terminal: clear input, predictable output, and no service to babysit.

## Cover

![LLM Cost Lens cover](assets/readme-cover.svg)

## Run path

```bash
git clone https://github.com/mertefekurt/llm-cost-lens.git
cd llm-cost-lens
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
llm-cost-lens examples/openai_calls.jsonl
```

## Repository notes

```text
.github/        CI workflow
examples/       sample inputs
src/            package source
tests/          test coverage
.gitignore      project file
pyproject.toml  package metadata
```
