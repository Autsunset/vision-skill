# vision-skill

一个 [Claude Code](https://docs.claude.com/en/docs/claude-code) 技能（Skill），让**没有原生视觉能力的模型**也能通过外部多模态 API「看懂」图片：截图、照片、图表、示意图、OCR 文字识别等都能分析。

兼容 OpenAI、Anthropic，以及任意 OpenAI / Anthropic 兼容的视觉端点（Azure OpenAI、OpenRouter、本地多模态模型、第三方中转 API 等）。

## 功能

- 读取本地图片（PNG / JPG / JPEG / GIF / WebP / BMP / TIFF），也支持 `data:image/...;base64,...` URI
- 自动 base64 编码后调用视觉模型
- 同时支持 OpenAI 与 Anthropic 两种 API 格式
- 自定义分析 prompt（不传则给出详细描述）
- 修复了 Windows 下中文输出的乱码问题（强制 UTF-8）

## 安装

把 `SKILL.md` 与 `scripts/` 放进 Claude Code 的 skills 目录：

```
~/.claude/skills/vision-skill/
├── SKILL.md
└── scripts/
    ├── vision-skill.sh
    └── vision.py
```

一键安装：

```bash
mkdir -p ~/.claude/skills/vision-skill
cp -r SKILL.md scripts ~/.claude/skills/vision-skill/
cp .env.example ~/.claude/skills/vision-skill/.env
# 编辑 .env 填入你的配置
```

## 配置

三种方式，优先级：**环境变量 > .env 文件 > 配置文件**

### 方式一：.env 文件（推荐）

在 skill 目录创建 `.env` 文件：

```bash
cp .env.example ~/.claude/skills/vision-skill/.env
# 编辑 .env，填入真实配置
```

```env
VISION_API_KEY=sk-your-key-here
VISION_API_BASE=https://api.openai.com/v1
VISION_MODEL=gpt-4o
VISION_API_FORMAT=openai
VISION_MAX_TOKENS=4096
```

### 方式二：配置文件

复制示例并填入你的密钥：

```bash
cp vision-config.example.json ~/.claude/vision-config.json
# 编辑 ~/.claude/vision-config.json，填入真实 api_key
```

```json
{
  "api_key": "sk-your-key-here",
  "api_base": "https://api.openai.com/v1",
  "model": "gpt-4o",
  "api_format": "openai",
  "max_tokens": 4096
}
```

### 方式三：环境变量

| 变量 | 默认值 | 说明 |
|---|---|---|
| `VISION_API_KEY` | *(必填)* | API 密钥 |
| `VISION_API_BASE` | `https://api.openai.com/v1` | API 地址 |
| `VISION_MODEL` | `gpt-4o` | 模型名 |
| `VISION_API_FORMAT` | `openai` | `openai` 或 `anthropic` |
| `VISION_MAX_TOKENS` | `4096` | 返回最大 token 数 |

环境变量优先级最高，适合 CI/CD 或临时覆盖。

### Anthropic 格式

设 `VISION_API_FORMAT=anthropic`，默认走 `https://api.anthropic.com/v1/messages`，用 `x-api-key` 头与 `anthropic-version: 2023-06-01`。

## 使用

在 Claude Code 里直接说「看一下这张图 /xxx.png」「这张截图里有什么」即可自动触发；也可显式调用 `/vision-skill <路径> [prompt]`。

命令行直接跑：

```bash
# 默认详细描述
bash ~/.claude/skills/vision-skill/scripts/vision-skill.sh photo.jpg

# 自定义分析
bash ~/.claude/skills/vision-skill/scripts/vision-skill.sh chart.png "读出柱状图里的数值"

# OCR
bash ~/.claude/skills/vision-skill/scripts/vision-skill.sh receipt.jpg "提取图片里所有文字"
```

## 安全

`.env` 和 `~/.claude/vision-config.json` 含 API 密钥，**切勿提交到仓库**——已在 `.gitignore` 中排除，仓库只提供 `.env.example` 和 `vision-config.example.json` 占位模板。
