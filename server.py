"""
image-to-code-mcp
==============
Give ANY non-vision LLM (DeepSeek, etc.) the ability to see images.
Converts screenshots, UIs, photos, documents, and diagrams into code or text.

Just set model name + API key. Auto-detects provider from model name.

Models (April 2026): gpt-5.4-mini ($0.75/$4.50) | gpt-4o-mini ($0.15/$0.60)
Free: gemini-2.5-flash | Best code: claude-sonnet-4-6 ($3/$15)
"""

import base64
import os
import re
import httpx
from pathlib import Path
from mcp.server.fastmcp import FastMCP

# Load .env file if present (works without manual env var setup)
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass

mcp = FastMCP("image-to-code-mcp")

# ═══════════════════════════════════════════════════════════════
# CONFIG — User only needs: IMAGE_EYES_MODEL + IMAGE_EYES_API_KEY
# ═════════════════════════════════════════════════════════════

_PROVIDER_DEFAULTS = {"openai": "gpt-4o-mini", "gemini": "gemini-2.5-flash", "anthropic": "claude-sonnet-4-6"}

def _resolve_model() -> str:
    model = os.environ.get("IMAGE_EYES_MODEL", "")
    if model:
        return model
    provider = os.environ.get("IMAGE_EYES_PROVIDER", "")
    if provider in _PROVIDER_DEFAULTS:
        return _PROVIDER_DEFAULTS[provider]
    if provider:
        return provider
    return "gpt-4o-mini"

MODEL = _resolve_model()

def _detect_provider(model: str) -> str:
    """Auto-detect provider from model name."""
    m = model.lower()
    if "gpt" in m or "o1" in m or "o3" in m or "o4" in m:
        return "openai"
    if "gemini" in m:
        return "gemini"
    if "claude" in m:
        return "anthropic"
    if "glm" in m:
        return "openai"  # GLM uses OpenAI-compatible API via OpenRouter
    return "openai"  # default

def _get_api_key(provider: str) -> str:
    """Get API key: IMAGE_EYES_API_KEY (universal) or provider-specific."""
    universal = os.environ.get("IMAGE_EYES_API_KEY", "")
    if universal:
        return universal
    keys = {"openai": "OPENAI_API_KEY", "gemini": "GEMINI_API_KEY", "anthropic": "ANTHROPIC_API_KEY"}
    return os.environ.get(keys[provider], "")

# In-memory caches
_image_cache: dict[str, tuple[str, str]] = {}
_conversation_history: dict[str, list[dict]] = {}

# ═══════════════════════════════════════════════════════════════
# SYSTEM PROMPT — CARE Framework
# ═══════════════════════════════════════════════════════════════

SYSTEM_PROMPT = """You are an expert frontend developer who converts visual designs into production-ready code with pixel-perfect accuracy.

# Tone and styles

- Be extremely concise. Do not chat or explain — just generate code.
- Output ONLY the complete code inside a single markdown code block. No text before or after.
- Always respond in the language the user used.

# Replication requirements

- Make sure the app looks EXACTLY like the screenshot.
- Use the EXACT text from the screenshot. Do not paraphrase, summarize, or rewrite any text.
- Match ALL colors EXACTLY using hex values extracted from the screenshot. Never guess colors.
- Match layout precisely — use the same flexbox/grid structure, spacing, and alignment.
- Include EVERY visible element: buttons, inputs, icons, text, images, charts, dividers, badges.
- For mobile screenshots, do NOT include device frames or browser chrome — only render the UI.
- Do NOT add elements that aren't in the screenshot.
- Do NOT skip decorative elements — include everything visible.

# Multiple screenshots

If multiple screenshots are provided, organize them meaningfully:
- If they appear to be different pages in a website, make them distinct pages and link them.
- If they look like different tabs or views in an app, connect them with appropriate navigation.
- If they appear unrelated, create a scaffold that separates them into "Screenshot 1", "Screenshot 2", etc. so it is easy to navigate.

# Stack-specific instructions

## html_tailwind
- Use this script to include Tailwind: <script src="https://cdn.tailwindcss.com"></script>
- Use Tailwind arbitrary values for exact hex colors: bg-[#1a1a1a], text-[#6366F1]
- For dark backgrounds: use bg-[#hex], NOT Tailwind gray classes unless they match exactly
- <!DOCTYPE html> with full <html><head><body> structure

## html_css
- Only use HTML, CSS and JS.
- Do not use Tailwind or any CSS framework.
- Embed all CSS in a <style> block in <head>. Use CSS custom properties for colors.
- Use Flexbox and CSS Grid for layout. Semantic HTML5 elements.

## react_tailwind
- Use these scripts to include React so that it can run on a standalone page:
    <script src="https://cdn.jsdelivr.net/npm/react@18.0.0/umd/react.development.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/react-dom@18.0.0/umd/react-dom.development.js"></script>
    <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
- For babel, make sure to use https://unpkg.com/@babel/standalone/babel.min.js. DO NOT use https://cdn.babeljs.io/babel.min.js — it is not the correct version and will cause errors.
- Use this script to include Tailwind: <script src="https://cdn.tailwindcss.com"></script>
- Use TypeScript interfaces for props. Extract repeating patterns into components.
- Render via ReactDOM.createRoot. Use className (not class) for Tailwind.

## vue_tailwind
- Use these scripts to include Vue so that it can run on a standalone page:
    <script src="https://registry.npmmirror.com/vue/3.3.11/files/dist/vue.global.js"></script>
- Use this script to include Tailwind: <script src="https://cdn.tailwindcss.com"></script>
- Use Vue via the global build:
    <div id="app">{{ message }}</div>
    <script>
      const { createApp, ref } = Vue
      createApp({ setup() { const message = ref('Hello vue!'); return { message } } }).mount('#app')
    </script>

## bootstrap
- Use this script to include Bootstrap: <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
- Include Bootstrap JS bundle before closing </body>

## ionic_tailwind
- Use these scripts to include Ionic so that it can run on a standalone page:
    <script type="module" src="https://cdn.jsdelivr.net/npm/@ionic/core/dist/ionic/ionic.esm.js"></script>
    <script nomodule src="https://cdn.jsdelivr.net/npm/@ionic/core/dist/ionic/ionic.js"></script>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@ionic/core/css/ionic.bundle.css" />
- Use this script to include Tailwind: <script src="https://cdn.tailwindcss.com"></script>
- For ionicons, add these script tags near the end of the page, right before the closing </body> tag:
    <script type="module">
        import ionicons from 'https://cdn.jsdelivr.net/npm/ionicons/+esm'
    </script>
    <script nomodule src="https://cdn.jsdelivr.net/npm/ionicons/dist/esm/ionicons.min.js"></script>
    <link href="https://cdn.jsdelivr.net/npm/ionicons/dist/collection/components/icon/icon.min.css" rel="stylesheet">

## svg
- Output only the SVG markup — no HTML wrapper, no <!DOCTYPE>.
- Match all shapes, paths, colors, and text exactly as shown. Use semantic SVG elements.
- Include viewBox for responsive scaling. Inline all styles.

## description
- Not a code stack. Describe the image in extreme detail as instructed.

# General instructions for all stacks

- You can use Google Fonts or other publicly accessible fonts. Default to Inter (weights 400,500,600,700).
- Except for Ionic, use Font Awesome 6.5.1 for icons: <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
- For brand logos, recreate with simple inline SVG or Font Awesome brand icons.
- For charts and graphs: use pure CSS/HTML (divs with backgrounds, borders, heights). Do not use charting libraries.
- Make sure the output is responsive.
"""

# ═══════════════════════════════════════════════════════════════
# STACK INSTRUCTIONS (lean — injected into user prompt)
# ═══════════════════════════════════════════════════════════════

STACK_INSTRUCTIONS = {
    "html_tailwind": "Selected stack: html_tailwind.",
    "html_css": "Selected stack: html_css. Only use HTML, CSS and JS. Do not use Tailwind.",
    "react_tailwind": "Selected stack: react_tailwind.",
    "vue_tailwind": "Selected stack: vue_tailwind.",
    "bootstrap": "Selected stack: bootstrap.",
    "ionic_tailwind": "Selected stack: ionic_tailwind.",
    "svg": "Selected stack: svg.",
    "description": "Task: Describe this image in extreme detail. See instructions below.",
}

# ═══════════════════════════════════════════════════════════════
# CONVERSATION PROMPT
# ═══════════════════════════════════════════════════════════════

CONVERSATION_SYSTEM = """You are an expert image analyst. Answer questions about the provided image with precision and detail.

## Rules
- Be specific — quote exact text, name exact hex colors, describe exact positions
- If UI: reference specific elements, their text, colors, and layout
- If photo: describe subjects, setting, lighting, composition, mood
- If document/diagram: extract all text, structure, and relationships
- If chart/graph: extract all data points, labels, axes, and trends
- Answer ONLY what was asked — don't describe the whole image unless asked
- Be concise but complete — answer the question, then stop
- When citing text from the image, put it in quotes"""

# ═══════════════════════════════════════════════════════════════
# Image handling
# ═══════════════════════════════════════════════════════════════

def _image_to_base64(file_path: str) -> tuple[str, str]:
    with open(file_path, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    ext = file_path.rsplit(".", 1)[-1].lower()
    mime_map = {
        "png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
        "gif": "image/gif", "webp": "image/webp", "bmp": "image/bmp"
    }
    return data, mime_map.get(ext, "image/png")

def _load_image(file_path: str) -> tuple[str, str]:
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"Image not found: {file_path}")
    if file_path not in _image_cache:
        _image_cache[file_path] = _image_to_base64(file_path)
    return _image_cache[file_path]

def _extract_code(text: str) -> str:
    """Extract code from model response.
    Tiered approach inspired by screenshot-to-code's codegen/utils.py.
    1. <file> tags (some models wrap code this way)
    2. Markdown code fences with language tag
    3. Bare markdown code fences
    4. DOCTYPE + html tag detection
    5. SVG tag detection
    6. Fallback: raw text"""
    # Tier 1: <file path="...">...</file> wrappers
    file_match = re.search(r"<file\s+path\s*=\s*[\"'][^\"']+[\"']\s*>\s*(.*?)</file>", text, re.DOTALL)
    if file_match:
        return _extract_code(file_match.group(1))  # recurse in case nested
    # Tier 2: Markdown code fences with language
    match = re.search(r"```(?:html|svg|xml|jsx|tsx|vue)\s*\n(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    # Tier 3: Bare code fences
    match = re.search(r"```\s*\n(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    # Tier 4: DOCTYPE + html
    if re.search(r"<[!]DOCTYPE\s+html", text, re.IGNORECASE):
        return text.strip()
    # Tier 5: SVG
    if re.search(r"<svg\s", text, re.IGNORECASE):
        return text.strip()
    # Tier 6: raw text
    return text.strip()

# ═══════════════════════════════════════════════════════════════
# Unified API caller — auto-detects provider from model name
# ═══════════════════════════════════════════════════════════════

def _call_vision_api(
    system_prompt: str = "",
    user_prompt: str = "",
    image_paths: list[str] | None = None,
    messages: list[dict] | None = None,
    max_tokens: int = 16384,
    temperature: float = 0.2
) -> str:
    """Single entry point. Detects provider from MODEL env var, routes accordingly."""
    provider = _detect_provider(MODEL)
    api_key = _get_api_key(provider)

    if not api_key:
        key_names = {"openai": "OPENAI_API_KEY", "gemini": "GEMINI_API_KEY", "anthropic": "ANTHROPIC_API_KEY"}
        return f"ERROR: Set IMAGE_EYES_API_KEY or {key_names.get(provider, 'API key')} env var."

    if provider == "openai":
        return _call_openai(api_key, system_prompt, user_prompt, image_paths, messages, max_tokens, temperature)
    elif provider == "anthropic":
        return _call_anthropic(api_key, system_prompt, user_prompt, image_paths, messages, max_tokens)
    else:
        return _call_gemini(api_key, system_prompt, user_prompt, image_paths, messages, max_tokens, temperature)

def _call_openai(api_key, system_prompt, user_prompt, image_paths, messages, max_tokens, temperature):
    if messages is None:
        content = []
        if image_paths:
            for fp in image_paths:
                b64, mime = _load_image(fp)
                content.append({"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}", "detail": "high"}})
        content.append({"type": "text", "text": user_prompt})
        messages = [{"role": "user", "content": content}]

    try:
        resp = httpx.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": MODEL,
                "messages": ([{"role": "system", "content": system_prompt}] if system_prompt else []) + messages,
                "max_completion_tokens": max_tokens,
                "temperature": temperature
            },
            timeout=120
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            return "ERROR: Invalid OpenAI API key. Check your key at https://platform.openai.com/api-keys"
        if e.response.status_code == 429:
            return "ERROR: OpenAI rate limit exceeded. Check your usage/billing at https://platform.openai.com"
        if e.response.status_code == 404:
            return f"ERROR: Model '{MODEL}' not found or not accessible with your key"
        return f"ERROR: OpenAI API error ({e.response.status_code}): {e.response.text[:300]}"

def _call_anthropic(api_key, system_prompt, user_prompt, image_paths, messages, max_tokens):
    if messages is None:
        content = []
        if image_paths:
            for fp in image_paths:
                b64, mime = _load_image(fp)
                content.append({"type": "image", "source": {"type": "base64", "media_type": mime, "data": b64}})
        content.append({"type": "text", "text": user_prompt})
        messages = [{"role": "user", "content": content}]

    try:
        resp = httpx.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": api_key, "anthropic-version": "2023-06-01"},
            json={"model": MODEL, "max_tokens": max_tokens, "system": system_prompt, "messages": messages},
            timeout=120
        )
        resp.raise_for_status()
        return resp.json()["content"][0]["text"]
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            return "ERROR: Invalid Anthropic API key. Check at https://console.anthropic.com"
        if e.response.status_code == 429:
            return "ERROR: Anthropic rate limit exceeded. Check your plan."
        if e.response.status_code == 404:
            return f"ERROR: Model '{MODEL}' not found or not accessible"
        return f"ERROR: Anthropic API error ({e.response.status_code})"

def _call_gemini(api_key, system_prompt, user_prompt, image_paths, messages, max_tokens, temperature):
    if messages is None:
        parts = []
        if system_prompt:
            parts.append({"text": system_prompt})
        if image_paths:
            for fp in image_paths:
                b64, mime = _load_image(fp)
                parts.append({"inlineData": {"mimeType": mime, "data": b64}})
        parts.append({"text": user_prompt})
        contents = [{"parts": parts}]
    else:
        contents = messages

    try:
        resp = httpx.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent",
            params={"key": api_key},
            json={"contents": contents, "generationConfig": {"maxOutputTokens": max_tokens, "temperature": temperature}},
            timeout=120
        )
        resp.raise_for_status()
        body = resp.json()
        if "candidates" not in body or not body["candidates"]:
            if "error" in body:
                return f"ERROR: Gemini API error: {body['error']['message']}"
            return f"ERROR: Gemini returned no content. Check if model '{MODEL}' supports vision."
        parts = body["candidates"][0]["content"]["parts"]
        return "".join(p.get("text", "") for p in parts)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401 or e.response.status_code == 403:
            return "ERROR: Invalid Gemini API key. Get free key: https://aistudio.google.com/apikey"
        if e.response.status_code == 429:
            return "ERROR: Gemini rate limit exceeded. Free tier: 1,500/day. Try again later."
        return f"ERROR: Gemini API error ({e.response.status_code})"

# ═══════════════════════════════════════════════════════════════
# Core generation
# ═══════════════════════════════════════════════════════════════

def _generate(file_paths: list[str], stack: str, extra: str = "") -> str:
    stack_block = STACK_INSTRUCTIONS.get(stack, STACK_INSTRUCTIONS["html_tailwind"])

    user_prompt = f"""Generate code for a web page that looks exactly like the provided screenshot(s).

{stack_block}

# Replication instructions

- Make sure the app looks exactly like the screenshot.
- Use the exact text from the screenshot.
- Pay close attention to the background color, text color, font sizes, font weights, spacing, shadows, and borders.
- Get the code to match the screenshot as close as possible — pixel perfect.

# Multiple screenshots

If multiple screenshots are provided, organize them meaningfully:
- If they appear to be different pages in a website, make them distinct pages and link them.
- If they look like different tabs or views in an app, connect them with appropriate navigation.
- If they appear unrelated, create a scaffold that separates them into "Screenshot 1", "Screenshot 2", "Screenshot 3", etc. so it is easy to navigate.
- For mobile screenshots, do not include the device frame or browser chrome; focus only on the actual UI mockups."""

    if extra.strip():
        user_prompt = f"{user_prompt}\n\n# Additional instructions: {extra}"

    result = _call_vision_api(SYSTEM_PROMPT, user_prompt, image_paths=file_paths, max_tokens=16384, temperature=0.2)
    return _extract_code(result)

def _ask(file_path: str, question: str) -> str:
    b64, mime = _load_image(file_path)
    provider = _detect_provider(MODEL)

    if provider == "openai":
        messages = []
        for h in _conversation_history.get(file_path, [])[-10:]:
            messages.append({"role": h["role"], "content": h["text"]})
        messages.append({"role": "user", "content": [
            {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}", "detail": "high"}},
            {"type": "text", "text": question}
        ]})
        answer = _call_vision_api(system_prompt=CONVERSATION_SYSTEM, messages=messages, max_tokens=8192)

    elif provider == "anthropic":
        messages = []
        for h in _conversation_history.get(file_path, [])[-10:]:
            messages.append({"role": h["role"], "content": [{"type": "text", "text": h["text"]}]})
        messages.append({"role": "user", "content": [
            {"type": "image", "source": {"type": "base64", "media_type": mime, "data": b64}},
            {"type": "text", "text": question}
        ]})
        answer = _call_vision_api(system_prompt=CONVERSATION_SYSTEM, messages=messages, max_tokens=8192)

    else:  # gemini
        contents = []
        for h in _conversation_history.get(file_path, [])[-12:]:
            role = "model" if h["role"] == "assistant" else "user"
            contents.append({"role": role, "parts": [{"text": h["text"]}]})
        contents.append({"role": "user", "parts": [
            {"inlineData": {"mimeType": mime, "data": b64}},
            {"text": f"{CONVERSATION_SYSTEM}\n\n{question}"}
        ]})
        answer = _call_vision_api(messages=contents, max_tokens=8192, temperature=0.1)

    _conversation_history.setdefault(file_path, []).append({"role": "user", "text": question})
    _conversation_history[file_path].append({"role": "assistant", "text": answer})
    return answer

# ═══════════════════════════════════════════════════════════════
# MCP Tools
# ═══════════════════════════════════════════════════════════════

@mcp.tool()
def image_to_html_tailwind(file_path: str, extra_instructions: str = "") -> str:
    """Convert UI screenshot to HTML + Tailwind CSS. Pixel-perfect replication.
    Args: file_path (absolute path to image), extra_instructions (optional modifications)"""
    return _generate([file_path], "html_tailwind", extra_instructions)

@mcp.tool()
def image_to_html_css(file_path: str, extra_instructions: str = "") -> str:
    """Convert UI screenshot to plain HTML + CSS. No frameworks.
    Args: file_path (absolute path), extra_instructions (optional)"""
    return _generate([file_path], "html_css", extra_instructions)

@mcp.tool()
def image_to_react(file_path: str, extra_instructions: str = "") -> str:
    """Convert UI screenshot to React + TypeScript + Tailwind component.
    Args: file_path (absolute path), extra_instructions (optional)"""
    return _generate([file_path], "react_tailwind", extra_instructions)

@mcp.tool()
def image_to_vue(file_path: str, extra_instructions: str = "") -> str:
    """Convert UI screenshot to Vue 3 + Tailwind single-file app.
    Args: file_path (absolute path), extra_instructions (optional)"""
    return _generate([file_path], "vue_tailwind", extra_instructions)

@mcp.tool()
def image_to_bootstrap(file_path: str, extra_instructions: str = "") -> str:
    """Convert UI screenshot to Bootstrap 5 page.
    Args: file_path (absolute path), extra_instructions (optional)"""
    return _generate([file_path], "bootstrap", extra_instructions)

@mcp.tool()
def image_to_ionic(file_path: str, extra_instructions: str = "") -> str:
    """Convert UI screenshot to Ionic Framework mobile app page.
    Args: file_path (absolute path), extra_instructions (optional)"""
    return _generate([file_path], "ionic_tailwind", extra_instructions)

@mcp.tool()
def image_to_svg(file_path: str, extra_instructions: str = "") -> str:
    """Convert any image (logo, icon, diagram) to SVG markup.
    Args: file_path (absolute path), extra_instructions (optional)"""
    return _generate([file_path], "svg", extra_instructions)

@mcp.tool()
def describe_image(file_path: str) -> str:
    """Describe any image in extreme detail. For photos, documents, diagrams — not UIs.
    Args: file_path (absolute path to image)"""
    return _generate([file_path], "description")

@mcp.tool()
def ask_about_image(file_path: str, question: str) -> str:
    """Ask questions about an image. Back-and-forth conversation supported.
    Image cached in memory, conversation history preserved per file.
    Args: file_path (absolute path), question (e.g. "What text is in the header?")"""
    return _ask(file_path, question)


if __name__ == "__main__":
    mcp.run()
