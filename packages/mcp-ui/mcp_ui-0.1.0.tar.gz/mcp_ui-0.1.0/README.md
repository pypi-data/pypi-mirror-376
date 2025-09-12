
# MCP-UI Python SDK

This library is a Python port of the MCP-UI TypeScript SDK.  
It provides strongly typed helpers for creating UI resources and UI actions in MCP servers, with good DX (developer experience), type safety, and MCP-compatible JSON output.

---

## 📦 Installation

\`\`\`bash
pip install mcp-ui
\`\`\`

---

## 🚀 Core Concepts

### What is a UI Resource?
A **UI resource** is a unit of UI data (e.g., an HTML snippet, iframe, or Remote DOM script) that MCP clients can render.  
This SDK helps you create them consistently with correct metadata and encodings.

### What is a UI Action?
A **UI action result** represents an action the MCP client should take (e.g., open a link, show a prompt, call a tool).

---

## 🔧 Usage

### 1. Creating a UI Resource

#### Raw HTML

\`\`\`python
from mcp_ui import RawHtmlContent, CreateUIResourceOptions, create_ui_resource

options = CreateUIResourceOptions(
    uri="ui://demo/html",
    content=RawHtmlContent(type="rawHtml", htmlString="<h1>Hello MCP</h1>"),
    encoding="text"
)

resource = create_ui_resource(options)
print(resource)
\`\`\`

**Output:**

\`\`\`json
{
  "type": "resource",
  "resource": {
    "uri": "ui://demo/html",
    "mimeType": "text/html",
    "text": "<h1>Hello MCP</h1>",
    "blob": null,
    "_meta": null
  }
}
\`\`\`

#### External URL (iframe)

\`\`\`python
from mcp_ui import ExternalUrlContent, CreateUIResourceOptions, create_ui_resource

options = CreateUIResourceOptions(
    uri="ui://demo/frame",
    content=ExternalUrlContent(type="externalUrl", iframeUrl="https://example.com"),
    encoding="text"
)

iframe_res = create_ui_resource(options)
\`\`\`

**Output:**

\`\`\`json
{
  "type": "resource",
  "resource": {
    "uri": "ui://demo/frame",
    "mimeType": "text/uri-list",
    "text": "https://example.com",
    "blob": null,
    "_meta": null
  }
}
\`\`\`

#### Remote DOM (React)

\`\`\`python
from mcp_ui import RemoteDomContent, CreateUIResourceOptions, create_ui_resource

options = CreateUIResourceOptions(
    uri="ui://demo/react",
    content=RemoteDomContent(type="remoteDom", script="console.log('Hello')", framework="react"),
    encoding="blob"
)

remote_res = create_ui_resource(options)
\`\`\`

**Output (blob is Base64-encoded):**

\`\`\`json
{
  "type": "resource",
  "resource": {
    "uri": "ui://demo/react",
    "mimeType": "application/vnd.mcp-ui.remote-dom+javascript; framework=react",
    "blob": "Y29uc29sZS5sb2coJ0hlbGxvJyk=",
    "text": null,
    "_meta": null
  }
}
\`\`\`

---

### 2. Adding Metadata

You can attach metadata to resources. Keys are automatically prefixed with \`mcpui.dev/ui-\`.

\`\`\`python
options = CreateUIResourceOptions(
    uri="ui://demo/meta",
    content=RawHtmlContent(type="rawHtml", htmlString="<p>Meta Example</p>"),
    encoding="text",
    uiMetadata={"PREFERRED_FRAME_SIZE": {"width": 500, "height": 300}}
)

meta_res = create_ui_resource(options)
\`\`\`

**Output includes \`_meta\`:**

\`\`\`json
{
  "type": "resource",
  "resource": {
    "uri": "ui://demo/meta",
    "mimeType": "text/html",
    "text": "<p>Meta Example</p>",
    "blob": null,
    "_meta": {
      "mcpui.dev/ui-preferred-frame-size": { "width": 500, "height": 300 }
    }
  }
}
\`\`\`

---

### 3. UI Action Results

#### Tool Call

\`\`\`python
from mcp_ui import ui_action_result_tool_call
action = ui_action_result_tool_call("searchTool", {"query": "MCP SDK"})
\`\`\`

**Output:**

\`\`\`json
{
  "type": "tool",
  "payload": {
    "toolName": "searchTool",
    "params": { "query": "MCP SDK" }
  }
}
\`\`\`

#### Prompt

\`\`\`python
from mcp_ui import ui_action_result_prompt
action = ui_action_result_prompt("Please confirm your choice")
\`\`\`

**Output:**

\`\`\`json
{
  "type": "prompt",
  "payload": { "prompt": "Please confirm your choice" }
}
\`\`\`

#### Link

\`\`\`python
from mcp_ui import ui_action_result_link
action = ui_action_result_link("https://example.com")
\`\`\`

**Output:**

\`\`\`json
{
  "type": "link",
  "payload": { "url": "https://example.com" }
}
\`\`\`

#### Intent

\`\`\`python
from mcp_ui import ui_action_result_intent
action = ui_action_result_intent("share", {"platform": "twitter"})
\`\`\`

**Output:**

\`\`\`json
{
  "type": "intent",
  "payload": {
    "intent": "share",
    "params": { "platform": "twitter" }
  }
}
\`\`\`

#### Notification

\`\`\`python
from mcp_ui import ui_action_result_notification
action = ui_action_result_notification("Saved successfully!")
\`\`\`

**Output:**

\`\`\`json
{
  "type": "notify",
  "payload": { "message": "Saved successfully!" }
}
\`\`\`

---

## 📖 API Reference

### create_ui_resource(options: CreateUIResourceOptions) → Dict[str, Any]
Creates a UI resource for MCP. Returns a JSON-serializable dict.

**Parameters:**
- \`uri\`: must start with \`ui://\`
- \`content\`: one of \`RawHtmlContent\`, \`ExternalUrlContent\`, \`RemoteDomContent\`
- \`encoding\`: \`"text"\` or \`"blob"\`
- \`uiMetadata\`: UI-specific metadata (auto-prefixed)
- \`metadata\`: General metadata
- \`resourceProps\`: Extra resource fields

**Type System:**
- **Content payloads**:
  - RawHtmlContent(htmlString)
  - ExternalUrlContent(iframeUrl)
  - RemoteDomContent(script, framework)
- **Resource encodings**:
  - HTMLTextContent (text string)
  - Base64BlobContent (blob string, base64)
- **UI Action Results**:
  - tool, prompt, link, intent, notify

---

## ⚙️ Notes

- Internally uses dataclasses for type safety, but always returns dicts (via \`asdict()\`) for MCP compatibility.
- Enforces URI format (\`ui://\` prefix).
- Auto-encodes blob resources in Base64.

---

## 📄 License

MIT – same as the original MCP-UI SDK.
