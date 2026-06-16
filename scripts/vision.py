#!/usr/bin/env python3
"""Vision proxy: read an image via a multimodal API (OpenAI or Anthropic format)."""

import base64
import json
import mimetypes
import os
import sys
import urllib.error
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

SUPPORTED_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tiff", ".tif"}
CONFIG_FILE = os.path.expanduser("~/.claude/vision-config.json")
DEFAULT_PROMPT = "Describe this image in detail. Include any visible text, objects, people, layout, colors, and notable visual elements."

OPENAI_DEFAULTS = {
    "api_base": "https://api.openai.com/v1",
    "model": "gpt-4o",
}
ANTHROPIC_DEFAULTS = {
    "api_base": "https://api.anthropic.com",
    "model": "claude-sonnet-4-6",
}


def load_config():
    cfg = {}
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            cfg = json.load(f)

    api_key = os.environ.get("VISION_API_KEY") or cfg.get("api_key", "")
    api_base = os.environ.get("VISION_API_BASE") or cfg.get("api_base", "")
    model = os.environ.get("VISION_MODEL") or cfg.get("model", "")
    api_format = os.environ.get("VISION_API_FORMAT") or cfg.get("api_format", "openai")
    api_format = api_format.lower().strip()
    max_tokens = os.environ.get("VISION_MAX_TOKENS") or cfg.get("max_tokens", 4096)
    try:
        max_tokens = int(max_tokens)
    except (TypeError, ValueError):
        max_tokens = 4096

    if not api_key:
        print(
            "ERROR: No API key configured.\n"
            "Set VISION_API_KEY environment variable or create ~/.claude/vision-config.json with:\n"
            '  {"api_key": "sk-...", "api_base": "https://api.openai.com/v1", "model": "gpt-4o"}',
            file=sys.stderr,
        )
        sys.exit(2)

    if api_format == "openai":
        api_base = api_base or OPENAI_DEFAULTS["api_base"]
        model = model or OPENAI_DEFAULTS["model"]
    elif api_format == "anthropic":
        api_base = api_base or ANTHROPIC_DEFAULTS["api_base"]
        model = model or ANTHROPIC_DEFAULTS["model"]
    else:
        print(f"ERROR: Unknown VISION_API_FORMAT '{api_format}'. Use 'openai' or 'anthropic'.", file=sys.stderr)
        sys.exit(2)

    return {
        "api_key": api_key,
        "api_base": api_base.rstrip("/"),
        "model": model,
        "api_format": api_format,
        "max_tokens": max_tokens,
    }


def load_image(path):
    path = os.path.expanduser(path)

    if path.startswith("data:image/"):
        header, _, b64data = path.partition(",")
        media_type = header.split(":")[1].split(";")[0]
        return b64data, media_type

    if not os.path.exists(path):
        print(f"ERROR: Image file not found: {path}", file=sys.stderr)
        sys.exit(1)

    ext = os.path.splitext(path)[1].lower()
    if ext not in SUPPORTED_EXTS:
        print(f"ERROR: Unsupported image format '{ext}'. Supported: {', '.join(sorted(SUPPORTED_EXTS))}", file=sys.stderr)
        sys.exit(1)

    with open(path, "rb") as f:
        raw = f.read()

    b64data = base64.b64encode(raw).decode("ascii")
    media_type = mimetypes.guess_type(path)[0] or "image/png"
    return b64data, media_type


def post_json(url, headers, payload):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"ERROR: API request failed (HTTP {e.code}):\n{body}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"ERROR: Could not reach API at {url}:\n{e.reason}", file=sys.stderr)
        sys.exit(1)


def call_openai(cfg, b64data, media_type, prompt):
    url = cfg["api_base"] + "/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {cfg['api_key']}",
    }
    payload = {
        "model": cfg["model"],
        "max_tokens": cfg["max_tokens"],
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{media_type};base64,{b64data}"},
                    },
                ],
            }
        ],
    }
    result = post_json(url, headers, payload)
    content = result["choices"][0]["message"]["content"]
    if isinstance(content, list):
        return "\n".join(p.get("text", "") for p in content if p.get("type") == "text")
    return content


def call_anthropic(cfg, b64data, media_type, prompt):
    url = cfg["api_base"] + "/v1/messages"
    headers = {
        "Content-Type": "application/json",
        "x-api-key": cfg["api_key"],
        "anthropic-version": "2023-06-01",
    }
    payload = {
        "model": cfg["model"],
        "max_tokens": cfg["max_tokens"],
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": b64data,
                        },
                    },
                    {"type": "text", "text": prompt},
                ],
            }
        ],
    }
    result = post_json(url, headers, payload)
    return "\n".join(
        block.get("text", "") for block in result.get("content", []) if block.get("type") == "text"
    )


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        print(
            "\nUsage:\n"
            "  vision.py <image_path> [prompt]\n\n"
            "Configuration via environment variables or ~/.claude/vision-config.json:\n"
            "  VISION_API_KEY       API key (required)\n"
            "  VISION_API_BASE      API base URL\n"
            "  VISION_MODEL         Model name\n"
            "  VISION_API_FORMAT    'openai' (default) or 'anthropic'\n"
            "  VISION_MAX_TOKENS    Max response tokens (default 4096)"
        )
        sys.exit(0)

    image_path = args[0]
    prompt = " ".join(args[1:]).strip() or DEFAULT_PROMPT

    cfg = load_config()
    b64data, media_type = load_image(image_path)

    if cfg["api_format"] == "openai":
        result = call_openai(cfg, b64data, media_type, prompt)
    else:
        result = call_anthropic(cfg, b64data, media_type, prompt)

    print(result)


if __name__ == "__main__":
    main()
