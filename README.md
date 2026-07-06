# LLM Cost Lens

![stack](https://img.shields.io/badge/stack-Python-4b5563?style=flat-square) ![python](https://img.shields.io/badge/python-3.11-2563eb?style=flat-square) ![license](https://img.shields.io/badge/license-MIT-16a34a?style=flat-square) ![ci](https://img.shields.io/badge/ci-GitHub%20Actions-dc2626?style=flat-square)

![LLM Cost Lens cover](assets/readme-cover.svg)

Inspect LLM API logs for cost, latency, budget, and usage anomalies.

## Use case

- quick local checks around LLM operations
- small CI jobs where a readable report is enough
- review workflows that need deterministic output
- examples based on `examples/openai_calls.jsonl`

## Local setup

```bash
git clone https://github.com/mertefekurt/llm-cost-lens.git
cd llm-cost-lens
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

## CLI

```bash
llm-cost-lens examples/openai_calls.jsonl
```

## Quality check

```bash
python -m pip install -e ".[dev]"
ruff check .
pytest
python -m llm_cost_lens --help
```
