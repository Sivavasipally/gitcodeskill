# Workspace Management

A **workspace** is your team's complete AI environment in Dify. Every resource — applications, knowledge bases, models, plugins, and members — lives within a workspace.

---

## Workspace Overview

### Key Principle

> "Every resource in Dify belongs to a workspace." Resources are fully isolated between workspaces.

### Workspace Resources

```
Workspace
├── Apps           — Workflows, Chatflows, Agents, Chatbots
├── Knowledge      — Knowledge bases and pipelines
├── Tools          — Built-in, custom, MCP, and workflow tools
├── Members        — Team roles and permissions
├── Model Providers — Configured AI model credentials
├── Plugins        — Installed workspace extensions
└── Settings       — Billing, API extensions, data sources
```

### Creating a Workspace

| Method | How It's Created |
|--------|-----------------|
| **Dify Cloud** | Automatically on first login; user becomes Owner |
| **Community Edition** | Created during Docker installation setup |
| **Multiple workspaces** | Supported; switch via workspace selector (top-left) |

---

## Roles and Permissions

Five roles control what each team member can do within a workspace.

| Role | Typical Actions | Cannot Do |
|------|----------------|-----------|
| **Owner** | Everything; billing; delete workspace | — (one per workspace) |
| **Admin** | Manage members, configure models and plugins | Adjust roles; manage billing |
| **Editor** | Create, edit, delete apps and knowledge bases | Manage team |
| **Member** | Use published apps and accessible tools | Create or edit apps |
| **Dataset Operator** | Manage knowledge bases only | Create apps |

### Role Assignment Rules

- Only the **Owner** can invite new members or change roles
- Role changes take effect immediately
- Members can belong to multiple workspaces with different roles in each
- Workspace Owners/Admins/Editors can always **edit** apps in the workspace, but still need explicit access to **use** published web apps

---

## Team Members Management

### Team Capacity

| Plan | Max Members |
|------|-------------|
| Free | 1 |
| Professional | 3 |
| Team / Community / Enterprise | Unlimited |

### Inviting Members

1. Open **Settings → Members**
2. Click **Invite**
3. Enter email addresses
4. Select role
5. Send invitation

- New Dify users receive a registration email
- Existing Dify users gain immediate workspace access via the switcher

### Managing Members

| Action | Who Can Do It |
|--------|--------------|
| Invite members | Owner only |
| Remove members | Owner only |
| Change member roles | Owner only |
| View member list | Owner + Admin |

---

## Model Providers

Model providers are the AI models powering your applications — the foundation of everything in Dify.

### Provider Types

| Type | Description | Best For |
|------|-------------|----------|
| **System Providers** | Dify-managed; subscription billing; automatic updates | Rapid prototyping |
| **Custom Providers** | Your own API credentials; direct billing with provider | Production deployments |

Both types can coexist in the same workspace.

### Configuring Custom Providers

1. Navigate to **Settings → Model Providers**
2. Select a provider (OpenAI, Anthropic, Google, Cohere, Azure, Ollama, etc.)
3. Enter your API key and any additional configuration
4. Validate credentials
5. Save

### Supported Model Categories

| Category | Examples |
|----------|---------|
| **LLMs** | GPT-4o, Claude 3.5 Sonnet, Gemini 1.5 Pro, Llama 3 |
| **Embeddings** | `text-embedding-3-large`, Cohere embed, Azure OpenAI |
| **Image Generation** | DALL-E 3, Stable Diffusion |
| **Speech** | Whisper (transcription), TTS models |
| **Reranking** | Cohere Rerank, Jina Reranker |
| **Moderation** | OpenAI Moderation |

### Multiple Credentials per Provider

Maintain separate credentials for:
- Development / staging / production environments
- Cost optimization across accounts
- Testing different model tiers

> Deleting **all** credentials for a custom model removes that model from the workspace entirely.

### Load Balancing *(Paid Feature)*

Distributes requests across multiple API keys using round-robin routing:
- Prevents rate-limit disruptions
- Improves throughput and response times
- Ideal for high-traffic production applications

---

## Plugins

Plugins extend Dify's capabilities by connecting to model providers, external APIs, and custom tools.

### Access Control

| Role | Plugin Management |
|------|------------------|
| Owner / Admin | Install, configure, remove plugins |
| Editor / Member | Use installed plugins in applications |

### Installation Methods

| Method | Best For |
|--------|----------|
| **Dify Marketplace** | Vetted, community and official plugins |
| **GitHub URL + version** | Public repositories |
| **Local .zip upload** | Proprietary or private plugins |

### Plugin Capabilities

- Language model integrations (e.g., new model providers)
- Tool implementations (search, weather, databases)
- Trigger plugins for workflow automation
- Reverse invocation (plugins that call back into Dify)

### Workspace Plugin Settings

Admins configure:
- **Installation rights**: Open to all workspace members or restricted to admins
- **Debugging access**: Who can run plugin debug mode
- **Update strategy**: Auto-update or manual approval

### Custom Plugin Development

Build custom plugins using the Dify Plugin SDK:
1. Develop using the SDK
2. Package as a `.zip` file
3. Install via local upload or publish to the Marketplace

### Enterprise Restrictions

Enterprise workspaces may restrict which plugin sources are allowed. Contact your workspace admin if a plugin installation is blocked.

---

## App Management

### Key Operations

| Operation | Description |
|-----------|-------------|
| **Edit info** | Update name, description, icon, and branding |
| **Duplicate** | Create an independent copy (all config copied; original unchanged) |
| **Export DSL** | Download app as YAML for sharing or backup |
| **Import DSL** | Upload a YAML file to create an app from a saved configuration |
| **Delete** | Permanently remove (cannot be undone) |

### When to Duplicate

- Creating A/B test versions with different prompts or models
- Adapting apps for different user audiences
- Starting from a successful pattern
- Creating a backup before major refactoring

### Export / Import (DSL)

**What exports:**
- App configuration
- Workflow node settings
- Model parameters
- Knowledge base connections

**What does NOT export:**
- API keys
- Knowledge base content
- Usage logs and conversation history

**Import process:**
1. Click **Import DSL** in Studio
2. Upload the YAML file
3. Dify checks version compatibility
4. App created with all configurations intact

### Safe Deletion Checklist

> **Warning:** App deletion is **permanent and cannot be undone.**

Before deleting:
1. Consider unpublishing or duplicating instead
2. Notify all stakeholders
3. Export DSL as a backup
4. Confirm the delete action

---

## Personal Account Management

### Account Creation

| Edition | Methods |
|---------|---------|
| Dify Cloud | GitHub, Google, or email verification |
| Community Edition | Email and password only |

### Profile Settings

Customize via **Settings → Account → Profile**:
- Display name
- Profile picture
- Primary email address

> **Note:** Changing your email address affects all workspaces. For workspace-specific identity, consider using different display names.

### Multi-Workspace Access

Your account can belong to multiple workspaces simultaneously:
- Each workspace has independent role assignments
- Switch workspaces using the top-left workspace selector
- You might be Owner in one workspace and Member in another

### Language

Switch interface language via your **avatar menu**:
- English
- Simplified Chinese
- Traditional Chinese

---

## Subscription Management

### Subscription Tiers

| Plan | Members | Apps | Daily API Calls | Support |
|------|---------|------|----------------|---------|
| **Free (Sandbox)** | 1 | 5 | 5,000 | Community forum |
| **Professional** | 3 | 50 | Unlimited | Priority email |
| **Team** | 50 | 200 | Unlimited | Priority email + Slack |

### Billing Rules

- Only **Owners and Admins** can modify billing settings
- Upgrades are prorated for the current billing cycle
- Downgrades take effect immediately
- Exceeding new plan limits after downgrading results in **immediate loss of workspace access**

### Education Program

Students and educators qualify for the Professional plan at no cost:
- Requires a valid `.edu` email address
- Must confirm current academic status
- Annual renewal required to maintain eligibility

---

## API Extensions

API extensions allow you to extend Dify's built-in module capabilities with custom external services.

### Extension Types

| Type | Purpose |
|------|---------|
| **`external_data_tool`** | Inject external data into prompts at runtime |
| **`moderation`** | Filter or override user input and LLM output |

### API Requirements

All extension endpoints must:
- Accept **POST** requests
- Use `Content-Type: application/json`
- Authenticate via `Authorization: Bearer YOUR_API_KEY`

### Health Check Protocol

Dify validates your endpoint before saving by sending:
```json
{ "point": "ping" }
```

Your endpoint must respond:
```json
{ "result": "pong" }
```

---

### External Data Tool Extension

**Extension point:** `app.external_data_tool.query`

Inject real-time external data (weather, database lookups, etc.) into LLM prompts.

**Incoming request from Dify:**

```json
{
  "point": "app.external_data_tool.query",
  "params": {
    "app_id": "app-id",
    "tool_variable": "weather_retrieve",
    "inputs": {
      "location": "London"
    },
    "query": "How's the weather today?"
  }
}
```

**Your endpoint must return:**

```json
{
  "result": "City: London\nTemperature: 10°C\nConditions: Light rain"
}
```

The `result` string is injected into the LLM prompt as additional context.

---

### Moderation Extension

**Extension points:**

| Point | Reviews |
|-------|---------|
| `app.moderation.input` | User input and variable content |
| `app.moderation.output` | LLM-generated responses (100-char chunks for streaming) |

**Incoming request from Dify:**

```json
{
  "point": "app.moderation.input",
  "params": {
    "app_id": "app-id",
    "inputs": { "query": "user message here" },
    "query": "user message here"
  }
}
```

**Response — flagged content:**

```json
{
  "flagged": true,
  "action": "direct_output",
  "preset_response": "I can't help with that topic."
}
```

**Response — override content:**

```json
{
  "flagged": true,
  "action": "overridden",
  "text": "[Content removed by moderation]"
}
```

**Actions:**

| Action | Effect |
|--------|--------|
| `direct_output` | Return the `preset_response` to the user immediately |
| `overridden` | Replace the flagged content with `text` |

---

### Deploying Extensions with Cloudflare Workers

Cloudflare Workers provide a free, publicly accessible deployment option for API extensions.

**Quick start:**

```bash
git clone https://github.com/crazywoola/dify-extension-workers.git
cp wrangler.toml.example wrangler.toml
```

**Configure `wrangler.toml`:**

```toml
name = "dify-extension-example"
compatibility_date = "2023-01-01"

[vars]
TOKEN = "your-random-secure-token"
```

> Use a random string for TOKEN. Pass sensitive values through environment variables rather than hardcoding.

**Deploy:**

```bash
npm install
npm run deploy
```

**Local testing:**

```bash
npm run dev
# → Ready on http://localhost:58445
```

**Monitor deployed logs:**

```bash
wrangler tail
```

**Key implementation details:**
- Use `hono/bearer-auth` for Bearer token validation
- Use `zod` for input parameter validation
- `point` field accepts `"ping"` or `"app.external_data_tool.query"`
