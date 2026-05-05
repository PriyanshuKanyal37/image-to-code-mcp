# image-to-code-mcp

Give **any AI that supports MCP** the ability to see images and convert them into pixel-perfect code — even if the AI itself has no vision.

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![MCP](https://img.shields.io/badge/MCP-ready-8A2BE2)](https://modelcontextprotocol.io)

---

## CRITICAL — You MUST Provide the Image FILE PATH

**This tool reads images from disk. It does NOT see images pasted into chat.**

```
WRONG:  "Convert this to HTML" [pastes screenshot into chat]
RIGHT:  "Convert C:/Users/you/Desktop/screenshot.png to HTML"
```

Your AI (Claude, DeepSeek, GPT text-only) cannot see pasted images. You must save the screenshot/photo to your computer first, then give the **full file path** to the tool. The vision model on the backend will read the file and generate the code.

**This is the #1 mistake new users make. Remember: file path, not paste.**

---

## Why This Exists

**Models like DeepSeek V4 Pro, GPT-4 (text), and many others have ZERO vision capability.** They literally cannot see images. When you paste a screenshot, they get nothing.

This MCP server solves that problem:

```
You paste a screenshot path
        │
Your AI (no vision — DeepSeek, etc.)
  → calls MCP tool: image_to_html_tailwind("C:/path/to/screenshot.png")
        │
MCP server reads the image file from disk
  → sends it to GPT-4o / Gemini / Claude (vision model)
        │
Vision model sees the image → generates pixel-perfect code
        │
Code returns to your AI → it reads, understands, and responds
        │
You get complete working code with exact colors, text, layout
```

**Your AI never sees the image. The vision model does the "seeing." Your AI works with the generated code.**

| Your AI model | Vision? | With this MCP |
|---------------|---------|---------------|
| DeepSeek V4 Pro | None | Full vision via Gemini/GPT-4o/Claude |
| Claude Opus 4.7 (text mode) | None | Full vision via plugin |
| GPT-4 (text) | None | Full vision via plugin |
| Any MCP-capable AI | None | Full vision via plugin |

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

## Update Your CLAUDE.md for Auto Tool Selection

After installing, add this to your `CLAUDE.md` (or equivalent AI config) so the AI automatically uses the right tool:

```markdown
## Image Handling (image-to-code-mcp)

I have NO vision. I cannot see pasted images. Always ask the user for the file path.

When user provides an image FILE PATH (not pasted image):
- "convert/make/build/code this" → use image_to_html_tailwind
- "make this React" → use image_to_react
- "make this Vue" → use image_to_vue
- "make this Bootstrap" → use image_to_bootstrap
- "make this Ionic" → use image_to_ionic
- "plain HTML CSS" → use image_to_html_css
- "convert to SVG" → use image_to_svg
- "what is/describe/explain this image" → use ask_about_image or describe_image
- Just a file path with no clear instruction → use ask_about_image first to understand the image, then suggest the best tool

Remember: these tools need the ABSOLUTE FILE PATH. Copy-pasted images are invisible to me.
```

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
