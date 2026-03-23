# llm-provider-tester

Small Python smoke-test utility for checking API keys and basic model connectivity for multiple LLM providers.

## Supported providers
- OpenAI
- DeepSeek
- Together
- Google Gemini

## Features
- Reads secrets from environment variables or a local `.env`
- Tests multiple models per provider
- Prints HTTP status + response snippet for quick diagnosis
- Prints a summary table in the terminal
- Writes a JSON log file under `logs/`
- Classifies common failures (`AUTH`, `NOT_FOUND`, `RATE_LIMIT`, `QUOTA`, etc.)

## Setup
Copy the example file and fill in only what you need:

```bash
cp .env.example .env
```

## Usage
Run:

```bash
python3 test_provider_keys.py
```

## Supported env vars
- `OPENAI_API_KEY`
- `DEEPSEEK_API_KEY`
- `TOGETHER_API_KEY`
- `GEMINI_API_KEY` or `GOOGLE_API_KEY`

## Optional model lists
Use comma-separated values:
- `OPENAI_MODELS`
- `DEEPSEEK_MODELS`
- `TOGETHER_MODELS`
- `GEMINI_MODELS`

## Output
- Detailed per-test output
- Summary table in terminal
- JSON log file written to `logs/provider-test-<timestamp>.json`

## Notes
- Keep secrets in `.env` or environment variables; do not hardcode them in the script.
- This tool performs minimal API calls to validate connectivity/auth/model access.
