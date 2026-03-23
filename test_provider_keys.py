#!/usr/bin/env python3
import json
import os
from urllib import request, error

TIMEOUT = 20


def load_dotenv(path='.env'):
    if not os.path.exists(path):
        return
    for raw in open(path, 'r', encoding='utf-8'):
        line = raw.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, value = line.split('=', 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def post_json(url, payload, headers):
    data = json.dumps(payload).encode('utf-8')
    req = request.Request(url, data=data, headers=headers, method='POST')
    try:
        with request.urlopen(req, timeout=TIMEOUT) as resp:
            body = resp.read().decode('utf-8', errors='replace')
            return resp.status, body
    except error.HTTPError as e:
        body = e.read().decode('utf-8', errors='replace')
        return e.code, body
    except Exception as e:
        return None, str(e)


def test_openai(api_key, model):
    url = 'https://api.openai.com/v1/responses'
    payload = {'model': model, 'input': 'Reply with exactly: OK'}
    headers = {'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'}
    return post_json(url, payload, headers)


def test_deepseek(api_key, model):
    url = 'https://api.deepseek.com/v1/chat/completions'
    payload = {
        'model': model,
        'messages': [{'role': 'user', 'content': 'Reply with exactly: OK'}],
        'max_tokens': 10,
        'temperature': 0,
    }
    headers = {'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'}
    return post_json(url, payload, headers)


def test_together(api_key, model):
    url = 'https://api.together.xyz/v1/chat/completions'
    payload = {
        'model': model,
        'messages': [{'role': 'user', 'content': 'Reply with exactly: OK'}],
        'max_tokens': 10,
        'temperature': 0,
    }
    headers = {'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'}
    return post_json(url, payload, headers)


def test_gemini(api_key, model):
    url = f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}'
    payload = {'contents': [{'parts': [{'text': 'Reply with exactly: OK'}]}]}
    headers = {'Content-Type': 'application/json'}
    return post_json(url, payload, headers)


def summarize(provider, model, status, body):
    print(f'\n=== {provider} :: {model} ===')
    print(f'status: {status}')
    snippet = (body or '')[:1000]
    print(snippet)


def env_models(name, default):
    raw = os.getenv(name, '').strip()
    if not raw:
        return default
    return [x.strip() for x in raw.split(',') if x.strip()]


def main():
    load_dotenv()

    tests = []

    openai_key = os.getenv('OPENAI_API_KEY')
    if openai_key:
        for model in env_models('OPENAI_MODELS', ['gpt-4.1-mini', 'gpt-5.4']):
            tests.append(('OpenAI', model, lambda k=openai_key, m=model: test_openai(k, m)))

    deepseek_key = os.getenv('DEEPSEEK_API_KEY')
    if deepseek_key:
        for model in env_models('DEEPSEEK_MODELS', ['deepseek-chat']):
            tests.append(('DeepSeek', model, lambda k=deepseek_key, m=model: test_deepseek(k, m)))

    together_key = os.getenv('TOGETHER_API_KEY')
    if together_key:
        for model in env_models('TOGETHER_MODELS', ['moonshotai/Kimi-K2.5']):
            tests.append(('Together', model, lambda k=together_key, m=model: test_together(k, m)))

    gemini_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
    if gemini_key:
        for model in env_models('GEMINI_MODELS', ['gemini-3.1-pro-preview', 'gemini-2.5-pro', 'gemini-2.5-flash']):
            tests.append(('Gemini', model, lambda k=gemini_key, m=model: test_gemini(k, m)))

    if not tests:
        print('No API keys found in env/.env. Supported vars:')
        print('  OPENAI_API_KEY')
        print('  DEEPSEEK_API_KEY')
        print('  TOGETHER_API_KEY')
        print('  GEMINI_API_KEY or GOOGLE_API_KEY')
        return 1

    for provider, model, fn in tests:
        status, body = fn()
        summarize(provider, model, status, body)

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
