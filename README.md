# llm-provider-tester

Small Python smoke-test utility for checking API keys and basic model connectivity for multiple LLM providers.

## Supported providers
- OpenAI
- DeepSeek
- Together
- Google Gemini

## Usage
Set one or more environment variables, then run:

```bash
python3 test_provider_keys.py
```

Supported env vars:
- `OPENAI_API_KEY`
- `DEEPSEEK_API_KEY`
- `TOGETHER_API_KEY`
- `GEMINI_API_KEY` or `GOOGLE_API_KEY`

## Notes
- Keep secrets in environment variables; do not hardcode them in the script.
- This tool performs a minimal API call to validate connectivity/auth/model access.
