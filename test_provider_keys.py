#!/usr/bin/env python3
import json
import os
from collections import defaultdict
from datetime import datetime, timezone
from urllib import request, error

TIMEOUT = 20
LOG_DIR = 'logs'
USE_COLOR = os.getenv('NO_COLOR') is None


def color(text, kind):
    if not USE_COLOR:
        return text
    colors = {
        'green': '\033[92m',
        'red': '\033[91m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'reset': '\033[0m',
    }
    return f"{colors.get(kind, '')}{text}{colors['reset']}"


def color_result(kind):
    if kind == 'OK':
        return color(kind, 'green')
    if kind in ('RATE_LIMIT', 'QUOTA'):
        return color(kind, 'yellow')
    return color(kind, 'red')


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
    return post_json(
        'https://api.openai.com/v1/responses',
        {'model': model, 'input': 'Reply with exactly: OK'},
        {'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
    )


def test_deepseek(api_key, model):
    return post_json(
        'https://api.deepseek.com/v1/chat/completions',
        {
            'model': model,
            'messages': [{'role': 'user', 'content': 'Reply with exactly: OK'}],
            'max_tokens': 10,
            'temperature': 0,
        },
        {'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
    )


def test_together(api_key, model):
    return post_json(
        'https://api.together.xyz/v1/chat/completions',
        {
            'model': model,
            'messages': [{'role': 'user', 'content': 'Reply with exactly: OK'}],
            'max_tokens': 10,
            'temperature': 0,
        },
        {'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
    )


def test_gemini(api_key, model):
    return post_json(
        f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}',
        {'contents': [{'parts': [{'text': 'Reply with exactly: OK'}]}]},
        {'Content-Type': 'application/json'},
    )


def env_models(name, default):
    raw = os.getenv(name, '').strip()
    if not raw:
        return default
    return [x.strip() for x in raw.split(',') if x.strip()]


def classify(status, body):
    text = (body or '').lower()
    if status and 200 <= status < 300:
        return 'OK'
    if status == 401:
        return 'AUTH'
    if status == 403:
        return 'FORBIDDEN'
    if status == 404:
        return 'NOT_FOUND'
    if status == 429:
        return 'RATE_LIMIT'
    if status and 500 <= status < 600:
        return 'SERVER_ERR'
    if 'quota' in text or 'billing' in text:
        return 'QUOTA'
    if 'model' in text and ('not found' in text or 'unsupported' in text or 'unknown' in text):
        return 'MODEL_ERR'
    if status is None:
        return 'NETWORK'
    return 'ERROR'


def mask_secret_text(text):
    if not text:
        return text
    for key_name in ['OPENAI_API_KEY', 'DEEPSEEK_API_KEY', 'TOGETHER_API_KEY', 'GEMINI_API_KEY', 'GOOGLE_API_KEY']:
        val = os.getenv(key_name)
        if val:
            text = text.replace(val, f'REDACTED_{key_name}')
    return text


def print_table(results):
    headers = ['Provider', 'Model', 'HTTP', 'Result']
    rows = [[r['provider'], r['model'], str(r['status']), r['kind']] for r in results]
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))

    def fmt(row, colorize=False):
        rendered = []
        for i, cell in enumerate(row):
            value = cell.ljust(widths[i])
            if colorize and i == 3:
                value = color_result(cell).ljust(widths[i] + (9 if USE_COLOR else 0))
            rendered.append(value)
        return ' | '.join(rendered)

    print('\n=== Summary by model ===')
    print(fmt(headers))
    print('-+-'.join('-' * w for w in widths))
    for row in rows:
        print(fmt(row, colorize=True))


def print_provider_summary(results):
    grouped = defaultdict(list)
    for r in results:
        grouped[r['provider']].append(r)

    print('\n=== Summary by provider ===')
    for provider, items in grouped.items():
        kinds = [x['kind'] for x in items]
        if any(k == 'OK' for k in kinds):
            status = color('OK', 'green')
        elif any(k in ('RATE_LIMIT', 'QUOTA') for k in kinds):
            status = color('PARTIAL', 'yellow')
        else:
            status = color('FAIL', 'red')
        detail = ', '.join(f"{x['model']}={x['kind']}" for x in items)
        print(f'- {provider}: {status} ({detail})')


def write_log(results):
    os.makedirs(LOG_DIR, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    path = os.path.join(LOG_DIR, f'provider-test-{ts}.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    return path


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
        for model in env_models('TOGETHER_MODELS', [
            'moonshotai/Kimi-K2.5',
            'meta-llama/Llama-3.3-70B-Instruct-Turbo',
            'deepseek-ai/DeepSeek-V3.1',
            'deepseek-ai/DeepSeek-R1',
        ]):
            tests.append(('Together', model, lambda k=together_key, m=model: test_together(k, m)))

    gemini_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
    if gemini_key:
        for model in env_models('GEMINI_MODELS', ['gemini-3.1-pro-preview', 'gemini-2.5-pro', 'gemini-2.5-flash']):
            tests.append(('Gemini', model, lambda k=gemini_key, m=model: test_gemini(k, m)))

    if not tests:
        print('No API keys found in env/.env.')
        return 1

    results = []
    for provider, model, fn in tests:
        status, body = fn()
        body = mask_secret_text(body)
        kind = classify(status, body)
        results.append({
            'provider': provider,
            'model': model,
            'status': status,
            'kind': kind,
            'bodySnippet': (body or '')[:1200],
        })
        print(f'\n=== {provider} :: {model} ===')
        print(f'HTTP: {status} | Result: {color_result(kind)}')
        print((body or '')[:700])

    print_table(results)
    print_provider_summary(results)
    log_path = write_log(results)
    print(f'\nLog written to: {color(log_path, "blue")}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
