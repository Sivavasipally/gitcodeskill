# Publishing

Once your application is built and tested, Dify offers multiple ways to get it into users' hands.

---

## Publishing Overview

Every Dify application is automatically available through multiple channels when you click **Publish**.

| Channel | Best For |
|---------|---------|
| **Web App** | Instant shareable link; no setup required |
| **API** | Integrate AI into your own product or backend |
| **Embed on Website** | Add as a chat widget or inline iframe |
| **MCP Server** | Connect to Claude Desktop, Cursor, and other AI tools |

> **Note:** All publishing methods use the same app configuration. Set it once, publish everywhere.

> **Warning:** Publishing immediately replaces your live app. Users see changes on their very next interaction.

### Pre-Publish Checklist

Before sharing your app, confirm:
- [ ] App description is clear and helpful
- [ ] Icon and branding are set
- [ ] Access controls are configured
- [ ] Rate limits are set (especially for API access)

---

## Web Apps

### Workflow Web App

Workflow web apps present a **form-based interface** for single runs and batch processing.

#### How It Works

Published workflows automatically generate a web interface that:
- Collects input parameters through forms based on workflow start variables
- Processes requests using the complete workflow logic
- Returns results with built-in copy, save, and feedback actions
- Scales from single runs to hundreds of batch items

> Workflow apps are designed for **discrete tasks** that produce specific outputs — not ongoing conversation.

#### Single Execution

User experience:
1. Fill the input form
2. Click **Run**
3. View results
4. Copy / save / rate / generate variations

#### Batch Processing

Process hundreds of inputs simultaneously via CSV:

1. Switch to the **"Run Batch"** tab
2. Download the CSV template (column structure matches your input variables)
3. Fill the template (each row = one execution)
4. Upload the completed file
5. Monitor parallel processing with progress tracking
6. Export all results when complete

> CSV files must use **Unicode encoding** to prevent import failures.

#### Result Management

- Save important outputs in dedicated result tabs
- Saved results persist across sessions
- Use **"More like this"** to generate variations of a result

---

### Chatflow Web App

Chatflow web apps present a **conversational interface** with persistent memory.

#### How It Works

Your chatflow becomes a web app automatically when published:
- Maintains conversation context across user sessions
- Adapts to any screen size (mobile to desktop)
- Inherits all orchestration settings from your chatflow
- Applies access controls if configured

> Unlike single-use generators, chat apps maintain conversation memory and let users build on previous exchanges.

#### Interactive Features

| Feature | Description |
|---------|-------------|
| **Pre-conversation Forms** | Collect context (variables) before chatting begins |
| **Conversation Openers** | AI proactively introduces itself and its capabilities |
| **Follow-up Suggestions** | Generates 3 contextual next questions after each response |
| **Voice Input** | Speech-to-text; users talk instead of type |
| **Source Citations** | Shows exactly which knowledge base chunks were referenced |
| **Response Feedback** | Like/dislike rating on each AI response |

#### Pre-Conversation Forms

When your chatflow uses variables:
1. User sees a clean form on arrival
2. After filling required fields, the **"Start Conversation"** button activates
3. AI has full context for the entire session

> **Tip:** Every form field adds friction. Only ask for information that meaningfully improves responses.

#### Voice Input

1. Enable speech-to-text in Features
2. Microphone icon appears in the chat input
3. Users click → speak → text appears in real-time
4. They can edit before sending

> Users must grant microphone permissions in their browser on first use.

#### Session Management

| Action | Description |
|--------|-------------|
| Start new conversation | Opens a fresh thread without losing prior sessions |
| Pin conversation | Keep important threads at the top of the list |
| Delete conversation | Remove finished sessions |

Each conversation thread maintains its own independent memory and context.

---

## Web App Settings

Configure your published web app through **Settings** (accessible from the Publish panel).

### Branding

| Setting | Description |
|---------|-------------|
| App name | Shown in the browser tab and app header |
| Description | Explains what your app does; shown on the landing page |
| Icon | Custom emoji, uploaded image, or image URL |
| Language | Default interface language |
| Legal pages | Privacy policy, terms of service links |

### Feature Inheritance

Web apps automatically incorporate all features enabled in the parent application:
- Conversation tools (follow-ups, openers)
- Voice capabilities
- Citations and feedback

Disabling a feature in the app configuration immediately removes it from the published web app.

---

## Access Control

Control who can access your published web app.

### Access Levels (Dify Enterprise)

| Level | Description |
|-------|-------------|
| **All Members Within Platform** | Any workspace member; requires authentication |
| **Specific Members Within Platform** | Default; selected groups or individuals only |
| **Authenticated External Users** | Non-workspace users via third-party SSO |
| **Anyone** | Public; no authentication required |

> **Important:** "Without any groups or members selected under Specific Members, nobody can access your app — including you."

> Workspace Owners, Admins, and Editors can **always edit** any app in the workspace. But they still need to be explicitly added to the access list to **use** the published web app.

### Configuration

- Changes take effect **immediately** without republishing
- Group-based access auto-grants/revokes when members join or leave the group
- Web app permissions are **independent** of API key access controls

### Finding Apps

Team members discover accessible applications through the workspace **Explorer** page, which shows only apps they have permission to access.

---

## Embedding in Websites

Deploy your published web app directly into an existing website.

> Your web app must be **published** before embedding.

### Method 1: Chat Bubble Widget

A floating button that opens the full chat interface when clicked. Ideal for support apps and sitewide access.

```html
<script>
  window.difyChatbotConfig = {
    token: 'YOUR_APP_TOKEN',

    // Optional: environment (default: production)
    // isDev: false,

    // Optional: draggable along specified axes
    draggable: true,
    dragAxis: 'xy',

    // Optional: pre-filled inputs
    inputs: {
      user_name: 'John'
    },

    // Optional: CSS styling overrides
    containerProps: {
      style: {
        backgroundColor: '#1C64F2',
        borderRadius: '50%'
      }
    }
  }
</script>
<script
  src="https://udify.app/embed.min.js"
  id="YOUR_APP_TOKEN"
  defer>
</script>
```

**CSS Variables for Customization:**

| Variable | Controls |
|----------|---------|
| `--dify-chatbot-bubble-button-bg-color` | Button background color |
| `--dify-chatbot-bubble-button-right` | Right offset position |
| `--dify-chatbot-bubble-button-bottom` | Bottom offset position |
| `--dify-chatbot-bubble-button-width` | Button width |
| `--dify-chatbot-bubble-button-height` | Button height |
| `--dify-chatbot-bubble-button-border-radius` | Button corner radius |
| `--dify-chatbot-bubble-button-box-shadow` | Button shadow |

### Method 2: Iframe Integration

Embed the web app inline — always visible in your page. Ideal for form/workflow apps and product demos.

```html
<iframe
  src="https://udify.app/chatbot/YOUR_APP_TOKEN"
  width="100%"
  height="600"
  frameborder="0"
  allow="microphone">
</iframe>
```

**Advantages:**
- Always visible — no click to open
- Full functionality preserved
- Minimal setup
- Works for both chat and workflow apps

### Use Case Recommendations

| Scenario | Recommended Method |
|----------|--------------------|
| Customer support | Chat Bubble (non-intrusive) |
| Form / workflow app | Iframe (primary content area) |
| Product demo | Iframe (immediate engagement) |
| Sitewide access on multiple pages | Chat Bubble |

### Troubleshooting Embeds

| Issue | Check |
|-------|-------|
| Widget not appearing | Verify token; check browser console for script errors |
| Iframe not loading | Confirm app is published; check Content Security Policy headers; ensure HTTPS |
| Pre-filled inputs not working | Inputs are GZIP-compressed and base64-encoded; verify the encoding |

---

## MCP Server

Publish your Dify app as an MCP (Model Context Protocol) server so AI tools like Claude Desktop and Cursor can use it as a native extension.

### Setup

1. Open your app in Dify Studio
2. Find the **MCP Server** module in the configuration panel
3. Enable it — a unique server URL is generated

> **Security Warning:** Your MCP Server URL contains authentication credentials. Treat it like an API key. If compromised, regenerate it immediately to invalidate the old URL.

### Connect Claude Desktop

1. Open Claude → Profile → Settings → Integrations
2. Click **Add integration**
3. Paste your Dify app's Server URL as the Integration URL

### Connect Cursor

Create or edit `.cursor/mcp.json` in your project root:

```json
{
  "mcpServers": {
    "my-dify-app": {
      "url": "YOUR_DIFY_MCP_SERVER_URL"
    },
    "another-dify-app": {
      "url": "YOUR_SECOND_DIFY_APP_MCP_URL"
    }
  }
}
```

Multiple Dify apps can be added as separate entries.

### Best Practices

- **Write descriptive tool descriptions.** AI tools use these to decide when to call your app. Be specific: instead of "processes user data," write "accepts a JSON object with required fields: name (string), email (string), preferences (array of strings)."
- **Minimize latency.** MCP handles communication, but your app's processing time affects the client experience. For long operations, decompose into smaller, faster workflows or add progress indicators.

---

## Developing with APIs

Use your Dify application as a backend AI service — your code calls the API, Dify handles all AI processing.

### Setup

1. Build your app in Dify Studio
2. Navigate to your app's **API** page (sidebar)
3. Generate API credentials
4. Review the auto-generated API documentation

> **Security:** Never expose API keys in frontend code or client-side requests. Always call Dify APIs from your backend server.

### Text Generation API

```bash
curl -X POST 'https://api.dify.ai/v1/completion-messages' \
  -H 'Authorization: Bearer YOUR_API_KEY' \
  -H 'Content-Type: application/json' \
  -d '{
    "inputs": {
      "topic": "renewable energy"
    },
    "response_mode": "blocking",
    "user": "user-123"
  }'
```

**Python example:**
```python
import requests

response = requests.post(
    'https://api.dify.ai/v1/completion-messages',
    headers={
        'Authorization': 'Bearer YOUR_API_KEY',
        'Content-Type': 'application/json'
    },
    json={
        'inputs': {'topic': 'renewable energy'},
        'response_mode': 'blocking',
        'user': 'user-123'
    }
)
print(response.json())
```

### Conversational (Chat) API

```bash
# Start a new conversation (empty conversation_id)
curl -X POST 'https://api.dify.ai/v1/chat-messages' \
  -H 'Authorization: Bearer YOUR_API_KEY' \
  -H 'Content-Type: application/json' \
  -d '{
    "inputs": {},
    "query": "Hello! What can you help me with?",
    "conversation_id": "",
    "response_mode": "blocking",
    "user": "user-123"
  }'

# Continue the conversation (use conversation_id from previous response)
curl -X POST 'https://api.dify.ai/v1/chat-messages' \
  -H 'Authorization: Bearer YOUR_API_KEY' \
  -H 'Content-Type: application/json' \
  -d '{
    "inputs": {},
    "query": "Tell me more about that.",
    "conversation_id": "RETURNED_CONVERSATION_ID",
    "response_mode": "blocking",
    "user": "user-123"
  }'
```

### Key API Concepts

| Concept | Detail |
|---------|--------|
| `conversation_id` | Send empty string `""` to start a new conversation; reuse the returned ID for follow-up messages |
| `response_mode` | `blocking` waits for full response; `streaming` returns chunks in real-time |
| `user` | Your system's user identifier (for session tracking and logging) |
| Session variables | Pass via `inputs` to dynamically adjust app behavior mid-conversation |

> API conversations are **separate** from WebApp conversations — they do not share history.

### Streaming Responses

```python
response = requests.post(
    'https://api.dify.ai/v1/chat-messages',
    headers={'Authorization': 'Bearer YOUR_API_KEY'},
    json={
        'inputs': {},
        'query': 'Tell me a story',
        'conversation_id': '',
        'response_mode': 'streaming',
        'user': 'user-123'
    },
    stream=True
)

for line in response.iter_lines():
    if line:
        print(line.decode('utf-8'))
```
