# image-to-code-mcp

Give **any AI that supports MCP** the ability to see images and convert them into pixel-perfect code — even if the AI itself has no vision.

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![MCP](https://img.shields.io/badge/MCP-ready-8A2BE2)](https://modelcontextprotocol.io)

```
Screenshot → vision model sees it → code comes back → your AI works with it
         (GPT-4o / Gemini / Claude)       (HTML, React, Vue, SVG...)
```

---

## One-Prompt Install

Paste this into **Claude Code, Cursor, or any MCP-capable AI**:

```
Clone https://github.com/PriyanshuKanyal37/image-to-code-mcp.git to a folder,
install dependencies with pip install -r requirements.txt,
then add this MCP server to your settings:

For Claude Code: add to ~/.claude/settings.json under mcpServers:
"image-to-code-mcp": {
  "command": "python",
  "args": ["path/to/image-to-code-mcp/server.py"],
  "env": {
    "IMAGE_EYES_MODEL": "gemini-2.5-flash",
    "GEMINI_API_KEY": "your-free-gemini-key"
  }
}

For Cursor/VSCode: add to ~/.mcp.json under mcpServers (same structure).

Get a free Gemini API key at https://aistudio.google.com/apikey (1,500 images/day free).
Then restart and you're done. Run /mcp to verify 9 tools appear.
```

That's it. One prompt, 2 minutes.

---

## Features

- **9 MCP tools** — HTML/Tailwind, React, Vue, Bootstrap, Ionic, SVG, plain CSS, image description, Q&A chat
- **Multi-provider** — OpenAI, Google Gemini, Anthropic Claude. Auto-detected from model name
- **Free tier works** — Gemini Flash: 1,500 images/day at zero cost
- **Pixel-perfect** — exact colors, exact text, exact layout from any screenshot
- **Conversation mode** — `ask_about_image` with per-file chat history
- **Zero config needed** — drop a `.env` file or set env vars. No config files, no registrations

---

## Quick Setup

### 1. Clone & install

```bash
git clone https://github.com/PriyanshuKanyal37/image-to-code-mcp.git
cd image-to-code-mcp
pip install -r requirements.txt
```

### 2. Pick a model

| Model | Quality | Cost/image | Key from |
|-------|---------|------------|----------|
| **gemini-2.5-flash** | Good | **FREE** | [AI Studio](https://aistudio.google.com/apikey) |
| gpt-4o-mini | Great | ~$0.003 | [OpenAI](https://platform.openai.com/api-keys) |
| gpt-4.1-mini | Very Good | ~$0.002 | [OpenAI](https://platform.openai.com/api-keys) |
| claude-haiku-4-5 | Very Good | ~$0.01 | [Anthropic](https://console.anthropic.com) |
| claude-sonnet-4-6 | Excellent | ~$0.05 | [Anthropic](https://console.anthropic.com) |

### 3. Configure

**Option A — `.env` file** (simplest):

```bash
cp .env.example .env
# Edit .env — paste your model name + API key
```

**Option B — MCP config** (env vars):

Add to Claude Code (`~/.claude/settings.json`) or Cursor (`~/.mcp.json`):

```json
{
  "mcpServers": {
    "image-to-code-mcp": {
      "command": "python",
      "args": ["path/to/image-to-code-mcp/server.py"],
      "env": {
        "IMAGE_EYES_MODEL": "gemini-2.5-flash",
        "GEMINI_API_KEY": "your-key"
      }
    }
  }
}
```

### 4. Restart & verify

Run `/mcp` — you should see `image-to-code-mcp` with 9 tools.

---

## Usage

Paste any screenshot and say:

| What you say | Tool used |
|-------------|-----------|
| "Convert this to HTML/Tailwind" | `image_to_html_tailwind` |
| "Make this a React component" | `image_to_react` |
| "What data is in this chart?" | `ask_about_image` |
| "Describe this photo" | `describe_image` |
| "Turn this logo into SVG" | `image_to_svg` |

---

## All Tools

| Tool | Output | Use for |
|------|--------|---------|
| `image_to_html_tailwind` | HTML + Tailwind CSS | Web UIs, dashboards |
| `image_to_html_css` | Plain HTML + CSS | Simple pages |
| `image_to_react` | React + TypeScript + Tailwind | React projects |
| `image_to_vue` | Vue 3 + Tailwind | Vue projects |
| `image_to_bootstrap` | Bootstrap 5 | Bootstrap projects |
| `image_to_ionic` | Ionic Framework | Mobile apps |
| `image_to_svg` | SVG markup | Logos, icons, diagrams |
| `describe_image` | Text description | Photos, documents |
| `ask_about_image` | Conversational QA | Data extraction, questions |

---

## How It Works

```
You: "Convert this dashboard screenshot to HTML"
        │
Your AI (no vision) → calls MCP tool image_to_html_tailwind("dash.png")
        │
MCP server → sends image to GPT-4o / Gemini / Claude (vision model)
        │
Vision model sees image → generates pixel-perfect HTML/CSS
        │
Code returns to your AI → it reads, understands, and responds
        │
You: Get complete working HTML file with exact colors, text, layout
```

Your AI never sees the image. The vision model does the "seeing." Your AI works with the generated code.

---

## Configuration Reference

| Env Var | Required | What it does |
|---------|----------|--------------|
| `IMAGE_EYES_MODEL` | No (defaults `gpt-4o-mini`) | Vision model to use |
| `IMAGE_EYES_API_KEY` | Yes* | Universal key (any provider) |
| `OPENAI_API_KEY` | No | For `gpt-*` models |
| `GEMINI_API_KEY` | No | For `gemini-*` models |
| `ANTHROPIC_API_KEY` | No | For `claude-*` models |

*Use `IMAGE_EYES_API_KEY` (any provider) OR the provider-specific key. Provider is auto-detected from model name.*

---

## Credits

- Prompt patterns inspired by [screenshot-to-code](https://github.com/abi/screenshot-to-code)
- Built on [FastMCP](https://gofastmcp.com)

## License

MIT — use it, fork it, ship it.
