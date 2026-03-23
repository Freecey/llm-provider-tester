#!/usr/bin/env python3
import json
import os
import sys
from urllib import request, error

TIMEOUT = 20


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


def test_openai(api_key):
    url = 'https://api.openai.com/v1/responses'
    payload = {
        'model': 'gpt-4.1-mini',
        'input': 'Reply with exactly: OK'
    }
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    return post_json(url, payload, headers)


def test_deepseek(api_key):
    url = 'https://api.deepseek.com/v1/chat/completions'
    payload = {
        'model': 'deepseek-chat',
        'messages': [
            {'role': 'user', 'content': 'Reply with exactly: OK'}
        ],
        'max_tokens': 10,
        'temperature': 0
    }
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    return post_json(url, payload, headers)


def test_together(api_key):
    url = 'https://api.together.xyz/v1/chat/completions'
    payload = {
        'model': 'moonshotai/Kimi-K2.5',
        'messages': [
            {'role': 'user', 'content': 'Reply with exactly: OK'}
        ],
        'max_tokens': 10,
        'temperature': 0
    }
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    return post_json(url, payload, headers)


def test_gemini(api_key):
    model = 'gemini-3.1-pro-preview'
    url = f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}'
    payload = {
        'contents': [
            {
                'parts': [
                    {'text': 'Reply with exactly: OK'}
                ]
            }
        ]
    }
    headers = {
        'Content-Type': 'application/json'
    }
    return post_json(url, payload, headers)


def summarize(name, status, body):
    print(f'\n=== {name} ===')
    print(f'status: {status}')
    if body is None:
        print('body: <none>')
        return
    snippet = body[:1200]
    print(snippet)


def main():
    providers = []

    openai_key = os.getenv('OPENAI_API_KEY')
    if openai_key:
        providers.append(('OpenAI', test_openai, openai_key))

    deepseek_key = os.getenv('DEEPSEEK_API_KEY')
    if deepseek_key:
        providers.append(('DeepSeek', test_deepseek, deepseek_key))

    together_key = os.getenv('TOGETHER_API_KEY')
    if together_key:
        providers.append(('Together', test_together, together_key))

    gemini_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
    if gemini_key:
        providers.append(('Gemini', test_gemini, gemini_key))

    if not providers:
        print('No API keys found in env. Set one or more of:')
        print('  OPENAI_API_KEY')
        print('  DEEPSEEK_API_KEY')
        print('  TOGETHER_API_KEY')
        print('  GEMINI_API_KEY or GOOGLE_API_KEY')
        sys.exit(1)

    for name, fn, key in providers:
        status, body = fn(key)
        summarize(name, status, body)


if __name__ == '__main__':
    main()
