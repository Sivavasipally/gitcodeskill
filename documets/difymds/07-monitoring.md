# Monitoring

After publishing, Dify provides built-in analytics, conversation logs, annotation tools, and integrations with external observability platforms to help you understand and improve your applications.

---

## Analysis Dashboard

The built-in analytics dashboard gives you an at-a-glance view of application performance, usage, and costs.

### Key Metrics

| Metric | Definition |
|--------|-----------|
| **Total Messages** | Total conversation volume across your application |
| **Active Users** | Users who engaged in meaningful interactions (more than one message exchange) |
| **Average User Interactions** | Average number of exchanges per active user session |
| **Token Usage** | Total tokens consumed; proxy for operational cost |

### Time Range

Use the **time selector** to view trends over different periods (day, week, month, custom range).

### External Observability

Click **"Tracing app performance"** to configure integrations with platforms like Langfuse, LangSmith, and others for deeper analytics.

---

## Logs

The Logs section provides a complete record of every real-world conversation through your published application.

### What Gets Logged

| Logged | Not Logged |
|--------|-----------|
| All conversations via web app or API | Debug/test sessions (Step Run) |
| Complete input and output history | Prompt testing |
| User feedback ratings and comments | — |
| Model selection, token usage, response times | — |

### Key Capabilities

**Monitoring:**
- Full conversation timelines
- Message details with complete context
- Performance metrics per conversation
- User feedback ratings alongside responses

**Debugging:**
- Identify problematic conversations causing errors or bad outputs
- Detect performance bottlenecks (high latency, token spikes)
- Trace individual user journeys across multiple conversations

**Feedback Management:**
- View user ratings (thumbs up/down)
- Add internal notes to conversations
- Write improved responses directly in the interface for annotation

### Data Retention

| Plan | Retention Period |
|------|-----------------|
| Sandbox | 30 days |
| Professional | Unlimited (during active subscription) |
| Team | Unlimited (during active subscription) |
| Self-hosted | Unlimited by default (configurable via env vars) |

> **Privacy Note:** Logs contain complete user conversations including potentially sensitive data. Establish appropriate access controls and comply with applicable data protection regulations (GDPR, CCPA, etc.).

---

## Annotation Reply

The Annotation system lets you build a **curated response library** — a "fast path" that bypasses LLM generation for known questions, improving consistency and eliminating hallucinations.

### How It Works

When annotation replies are enabled:
1. User submits a query
2. System performs **semantic search** over your annotation library
3. If a match is found above the similarity threshold → return the pre-written answer
4. If no match → proceed with normal LLM generation

### Primary Use Cases

| Use Case | Example |
|----------|---------|
| **Enterprise consistency** | Policy, compliance, and product questions always return approved answers |
| **Rapid development** | Improve demo apps without retraining models |
| **Quality control** | Sensitive topics receive reviewed, approved responses |

### Setup

1. Navigate to your app → **Monitor → Annotation Reply**
2. Enable annotation replies
3. Set the **similarity threshold** (how close a query must match)
4. Select an **embedding model** for semantic matching
5. Add annotations via:
   - **Import from logs** — Promote good answers from real conversations
   - **Bulk import** — Upload Q&A pairs as CSV
   - **Manual entry** — Write question-answer pairs directly

### Performance Monitoring

The annotations dashboard tracks:
- Which annotations were matched (and how often)
- Similarity scores for each match
- Unanswered question patterns → candidates for new annotations

---

## Monitoring Integrations

Connect Dify to external observability platforms for richer tracing, evaluation, and debugging.

### What Gets Traced

All integrations receive the same categories of trace data:

| Trace Category | Data Included |
|----------------|--------------|
| **Workflows / Chatflows** | Run IDs, execution times, inputs, outputs, token usage, errors |
| **Messages** | LLM conversation details, token counts, model info, user metadata |
| **Moderation** | Content flagging events and actions taken |
| **Suggested Questions** | Generated follow-up questions with metadata |
| **Dataset Retrieval** | Knowledge base search queries and retrieved chunks |
| **Tool Invocations** | Tool name, parameters, outputs, execution time |
| **Conversation Titles** | Auto-generated conversation naming operations |

---

### LangSmith

LangSmith is a platform for building, testing, and monitoring production-grade LLM applications.

**Setup:**
1. Register at [smith.langchain.com](https://smith.langchain.com)
2. Create a project
3. Generate a **Personal Access Token** (Settings → API Keys)
4. In Dify: **Monitor → Tracing → LangSmith**
5. Enter your API key and project name

> **Note:** Project names must match exactly between LangSmith and Dify. If they don't match, a new project will be auto-created in LangSmith.

**Data Mapping:**

| Dify | LangSmith |
|------|-----------|
| Workflow / Chatflow | Chain |
| LLM call | LLM |
| Tool invocation | Tool |
| Knowledge retrieval | Retriever |

---

### Langfuse

Langfuse is an open-source LLM engineering platform for debugging, analyzing, and iterating on LLM applications.

**Setup:**
1. Register at [langfuse.com](https://langfuse.com)
2. Create a project
3. From project Settings → generate: **Secret Key**, **Public Key**, **Host URL**
4. In Dify: **Monitor → Tracing → Langfuse**
5. Enter the three credentials

**Advanced: Prompt Management Plugin**

A community-maintained Langfuse plugin enables version control of prompts within Dify:
- Fetch prompts from Langfuse by name/version
- Search the prompt library
- Sync prompt updates

---

### Opik (by Comet)

Open-source platform for evaluating, testing, and monitoring LLM applications.

**Setup:**
1. Register at Comet / Opik
2. Retrieve your **API Key** from the user menu
3. In Dify: **Monitor → Tracing → Opik**
4. Enter API key and project name

---

### W&B Weave

Weights & Biases Weave helps track, experiment with, evaluate, deploy, and improve LLM-based applications.

**Setup:**
1. Register at [wandb.ai](https://wandb.ai)
2. Obtain API key from the authorization page
3. In Dify: **Monitor → Tracing → Weave**
4. Enter API key, project name, and optional W&B entity (team/organization)

---

### Arize

Enterprise-grade LLM observability powered by OpenTelemetry.

**Setup:**
1. Register at [arize.com](https://arize.com)
2. Retrieve **API Key** and **Space ID** from the user menu
3. In Dify: **Monitor → Tracing → Arize**
4. Enter API key, Space ID, and project name

---

### Phoenix (by Arize)

Open-source, OpenTelemetry-based observability, evaluation, and prompt engineering platform.

**Setup (Phoenix Cloud):**
1. Create a Phoenix Space (note the unique URL identifier)
2. Go to **Settings → System Key** → generate API key
3. In Dify: **Monitor → Tracing → Phoenix**
4. Enter API key, project name, and **Space Hostname**

**Setup (Self-hosted Phoenix):**
1. Obtain API key from your Phoenix instance
2. In Dify: enter API key and project name (no Space Hostname needed)

**Span Type Mapping:**

| Dify | Phoenix |
|------|---------|
| LLM call | LLM span |
| Tool invocation | Tool span |
| Knowledge retrieval | Retriever span |

---

### Alibaba Cloud ARMS

Enterprise LLM observability via Alibaba Cloud Application Real-Time Monitoring Service.

**Requirements:** Dify version **1.6.0+**

**Setup:**
1. Log into the ARMS console
2. Navigate to **Integration Center**
3. Select **OpenTelemetry** with **gRPC protocol**
4. Copy **Public Endpoint** and **Authentication Token**
5. In Dify: **Monitor → Tracing → ARMS**
6. Enter License Key, Endpoint, and a custom App Name

**Multi-Component Support:**

| Component | Agent Type |
|-----------|-----------|
| Nginx | OpenTelemetry Agent |
| API server | LoongSuite-Python Agent |
| Sandbox | LoongSuite-Go Agent |
| Plugin-Daemon | LoongSuite-Go Agent |

Trace data is viewable both from the Dify console and from the ARMS console's LLM Application Monitoring section.

---

## Choosing an Observability Integration

| Need | Recommended Platform |
|------|---------------------|
| Open-source + self-hostable | **Langfuse** or **Phoenix** |
| Deep evaluation + experiment tracking | **LangSmith** |
| ML experiment tracking + LLM | **W&B Weave** |
| Enterprise OpenTelemetry | **Arize** or **Alibaba ARMS** |
| Comet ecosystem | **Opik** |
