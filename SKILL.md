---
name: vision-skill
description: Read and analyze images using an external multimodal API (OpenAI or Anthropic compatible). Use this skill whenever the user wants to view, read, analyze, describe, or interpret an image, screenshot, photo, diagram, chart, or any visual content — even if they just mention an image file path. Use when the user says "look at", "check this screenshot", "what does this image show", "read this picture", or similar visual analysis requests. This skill is essential for models without native vision capability.
---

# Vision Skill — Image Reading via Multimodal API

This skill enables image analysis by calling an external multimodal API. It reads image files, base64-encodes them, and sends them to a vision model for analysis — giving non-vision models the ability to "see."

## When to Use

- User provides an image file path and asks to view/analyze it
- User says "look at this screenshot", "what's in this image", "describe this picture"
- User wants OCR, chart reading, diagram interpretation, or any visual analysis
- Invoked as `/vision-skill <path> [prompt]`

## Configuration

The skill reads configuration from environment variables or a config file at `~/.claude/vision-config.json`.

### Environment Variables

| Variable | Default | Description |
|---|---|---|
| `VISION_API_KEY` | *(required)* | API key for the multimodal endpoint |
| `VISION_API_BASE` | `https://api.openai.com/v1` | API base URL |
| `VISION_MODEL` | `gpt-4o` | Model name to use |
| `VISION_API_FORMAT` | `openai` | API format: `openai` or `anthropic` |
| `VISION_MAX_TOKENS` | `4096` | Max tokens in the response |

### Config File (`~/.claude/vision-config.json`)

```json
{
  "api_key": "sk-...",
  "api_base": "https://api.openai.com/v1",
  "model": "gpt-4o",
  "api_format": "openai",
  "max_tokens": 4096
}
```

Environment variables take precedence over the config file.

## How to Analyze an Image

The skill bundles a launcher script `vision-skill.sh` that auto-detects a working Python 3 interpreter. Use it directly:

```bash
bash ~/.claude/skills/vision-skill/scripts/vision-skill.sh <image_path> [prompt]
```

Alternatively, invoke `vision.py` with whichever Python 3 is available on the system (`python` on Windows, `python3` on Linux/macOS):

```bash
python ~/.claude/skills/vision-skill/scripts/vision.py <image_path> [prompt]
```

### Arguments

- **image_path** (required): Local file path, or a `data:image/...;base64,...` URI. Supports PNG, JPG/JPEG, GIF, WebP, BMP, TIFF.
- **prompt** (optional): What to analyze or describe. Defaults to a detailed image description.

### Examples

```bash
# Simple description
bash ~/.claude/skills/vision-skill/scripts/vision-skill.sh screenshot.png

# Custom analysis prompt
bash ~/.claude/skills/vision-skill/scripts/vision-skill.sh diagram.png "Explain the architecture shown in this diagram"

# OCR / text extraction
bash ~/.claude/skills/vision-skill/scripts/vision-skill.sh receipt.jpg "Extract all text from this image"

# Chart reading
bash ~/.claude/skills/vision-skill/scripts/vision-skill.sh chart.png "Read the values from this bar chart"
```

## Workflow

1. Identify the image path from the user's message. If the user references a file that looks like an image (by extension or context), extract the path.
2. Determine the user's question about the image. If no specific question, omit the prompt to get a general description.
3. Run `bash ~/.claude/skills/vision-skill/scripts/vision-skill.sh <path> "<prompt>"`.
4. Present the vision model's response to the user.
5. For follow-up questions about the same image, re-run with the updated prompt.

## Error Handling

- If `VISION_API_KEY` is not set and no config file exists, the script prints a clear setup message. Relay it to the user.
- If the image file doesn't exist, the script reports the path. Ask the user to verify.
- If the API returns an error (HTTP 4xx/5xx), the script surfaces the response body. Share it with the user.

## Anthropic API Format

When `VISION_API_FORMAT=anthropic`:
- Endpoint: `{api_base}/v1/messages` (api_base default: `https://api.anthropic.com`)
- Sends as `image` content block with `source.type: "base64"`
- Uses `x-api-key` header and `anthropic-version: 2023-06-01`

## Tips

- For screenshots with text, prompt with "Extract all text" or "Read all visible text" for best OCR results.
- For diagrams, prompt with "Explain step by step" for structured analysis.
- For charts/graphs, specify what data to extract for precise readings.
- Works with any OpenAI-compatible endpoint (Azure OpenAI, OpenRouter, local LLMs) — just set `VISION_API_BASE` and `VISION_MODEL` accordingly.
- For multi-image analysis, run the script once per image and synthesize results.
