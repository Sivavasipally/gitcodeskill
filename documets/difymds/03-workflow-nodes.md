# Workflow Nodes

Every node in Dify performs a specific function. Nodes are connected on the canvas to form workflows. This reference covers all available node types.

---

## Node Categories

| Category | Nodes |
|----------|-------|
| **Start** | User Input, Schedule Trigger, Plugin Trigger, Webhook Trigger |
| **AI** | LLM, Agent, Question Classifier, Parameter Extractor |
| **Data** | Knowledge Retrieval, Doc Extractor, Variable Aggregator, Variable Assigner, List Operator, Template, Code |
| **Control** | If/Else, Iteration, Loop, Human Input |
| **Integration** | HTTP Request, Tools |
| **End** | Answer (Chatflow), Output (Workflow) |

---

## Start Nodes

### User Input Node

The User Input node initiates a workflow through direct user interaction or an API call. Each canvas supports **only one** User Input node.

**Publishing targets:** Web apps · MCP servers · Backend APIs · Tools inside other Dify apps

#### Preset Variables

| Variable | Description |
|----------|-------------|
| `userinput.files` | Uploaded files (legacy; prefer custom file inputs for new workflows) |
| `userinput.query` | Latest chat message in Chatflows (auto-populated) |

#### Custom Input Field Types

**Text**

| Type | Limit |
|------|-------|
| Short Text | 256 characters max |
| Paragraph | Unlimited multi-line |

**Structured Data**

| Type | Output |
|------|--------|
| Select | Chosen option from predefined list |
| Number | Numeric value |
| Checkbox | `true` / `false` |
| JSON Code | Structured object with optional schema validation |

**File Uploads**

| Type | Description |
|------|-------------|
| Single File | One file from device or URL |
| File List | Multiple simultaneous uploads |

> **Important:** The User Input node collects files but does not parse them. Downstream nodes (Doc Extractor, vision LLM, Code node) must handle file content.

---

### Schedule Trigger

Runs a workflow at specified times or intervals. Available **only for Workflow** apps. Maximum **one** per workflow.

#### Configuration Methods

| Method | Best For |
|--------|----------|
| **Visual Picker** | Simple schedules: hourly, daily, weekly, monthly |
| **Cron Expression** | Complex patterns (e.g., every 15 min, 9 AM–5 PM, weekdays) |

**Common Cron Examples:**

| Expression | Meaning |
|------------|---------|
| `0 9 * * 1-5` | 9:00 AM every weekday |
| `*/15 9-17 * * 1-5` | Every 15 min, 9 AM–5 PM, weekdays |
| `0 0 1 * *` | Midnight on the 1st of every month |
| `@daily` | Once a day at midnight |

> Schedule triggers update `sys.timestamp` at each execution but produce no output variables.

---

### Plugin Trigger

Fires automatically when specific events occur in external systems. Available **only for Workflow** apps.

**Example:** Subscribe to GitHub "Pull Request" events — the workflow runs whenever a PR is opened.

#### Setup Process

1. Right-click the canvas → **Add Node > Start**
2. Select a trigger plugin or search the Dify Marketplace
3. Select an existing subscription or create a new one
4. Configure additional settings

> Output variables are **defined by the plugin** and cannot be modified.

#### Subscription Creation Methods

| Method | How It Works |
|--------|-------------|
| **OAuth** | Dify auto-creates webhooks via OAuth; pre-configured clients available on Dify Cloud |
| **API Key** | Provide credentials; Dify establishes the webhook automatically |
| **Manual** | Create the webhook yourself using the provided callback URL |

**Limit:** Up to **10 subscriptions** per trigger plugin per workspace.

---

### Webhook Trigger

Fires when an external system sends an HTTP request to a generated unique URL.

#### Configuration

| Setting | Description |
|---------|-------------|
| **HTTP Method** | Expected request method |
| **Content-Type** | Determines which data types are extractable |
| **Data Extraction** | Query parameters, header parameters, or request body |
| **Response** | Customizable status code (200–399) and response body |

Each extracted parameter becomes an output variable available in the workflow.

> Before testing an unpublished trigger, activate the listening state by clicking **Run this step** or running a full workflow test.

---

## AI Nodes

### LLM Node

The core AI node. Sends prompts to a configured language model and captures its response. Supports text, images, documents, structured outputs, and streaming.

> **Prerequisite:** Configure at least one model provider in **System Settings → Model Providers**.

#### Model Parameters

| Parameter | Range | Effect |
|-----------|-------|--------|
| **Temperature** | 0–1 | 0 = deterministic; 1 = creative |
| **Top P** | 0–1 | Limits word choices by cumulative probability |
| **Frequency Penalty** | — | Reduces repetition of words |
| **Presence Penalty** | — | Encourages introducing new topics |

**Presets:** Precise · Balanced · Creative

#### Prompt Configuration

Chat models use **message roles**:

| Role | Purpose |
|------|---------|
| System | Define model behavior and persona |
| User | Represent the user's input |
| Assistant | Provide example responses (few-shot) |

Reference variables in prompts:
```
The user asked: {{userinput.query}}
Context: {{knowledge.result}}
```

#### Context Variables (RAG)

Connect a Knowledge Retrieval node's output to the LLM node's **Context** field to enable RAG. Dify automatically tracks citations so users see information sources.

#### Structured Outputs

Force the model to return a specific format:

| Method | Description |
|--------|-------------|
| **Visual Editor** | GUI for defining simple schemas |
| **JSON Schema** | Write schema directly for complex structures |
| **AI Generation** | Describe your needs in plain language |

> Models with native JSON support (GPT-4, Claude) handle structured outputs reliably. For others, Dify injects the schema into the prompt.

#### Memory (Chatflow Only)

Enable **Memory** to include prior conversation turns in each LLM call, maintaining context across a multi-turn chat.

#### Vision / File Processing

| File Type | Handling |
|-----------|---------|
| Images | Vision-capable models (GPT-4V, Claude) analyze directly |
| PDFs | Claude processes directly; others need Doc Extractor first |
| Other docs | Use Doc Extractor to convert to text |

**Vision detail levels:**
- `High detail` — Better accuracy, more tokens
- `Low detail` — Faster, fewer tokens

#### Error Handling

Configure retries and fallback strategies for failed LLM calls:
- Maximum retry attempts
- Interval between retries
- Backoff multiplier
- Fallback: default value · error routing · alternative model

---

### Agent Node

Empowers an LLM with autonomous tool control. The agent dynamically reasons through a problem and invokes tools as needed, rather than following a fixed path.

#### Reasoning Strategies

| Strategy | How It Works | Best For |
|----------|-------------|----------|
| **Function Calling** | Leverages native LLM tool-calling capabilities | GPT-4, Claude 3.5, and similar |
| **ReAct** | Structured Thought → Action → Observation loop | Models without native function calling |

#### Configuration

| Setting | Guidance |
|---------|----------|
| **Model** | Choose a capable model; more powerful = better reasoning |
| **Tools** | Add tools with clear descriptions and validated parameters |
| **Instructions** | Define role, goals, constraints (Jinja2 supported) |
| **Max Iterations** | 3–5 for simple tasks; 10–15 for complex research |

#### Outputs

- Final answer text
- Tool call outputs
- Step-by-step reasoning trace
- Iteration count and success indicator
- Structured debug logs

---

### Question Classifier Node

Categorizes user input using an LLM and routes the workflow to the appropriate branch — without building complex conditional logic.

#### Setup

1. **Input Variable** — Select the text to classify (commonly `sys.query` or `userinput.query`)
2. **Model** — Simpler models for obvious categories; powerful models for nuanced distinctions
3. **Categories** — Define clear, unambiguous labels with descriptions

Each category generates a distinct output branch.

#### Customer Service Example

| Category | Routes To |
|----------|----------|
| After-sales service | Warranty/returns/repair knowledge base |
| Product usage | Installation guide knowledge base |
| Other questions | Generic LLM response |

**Instructions Field:** Add detailed guidance to handle edge cases, ambiguous inputs, and organizational nuances.

---

### Parameter Extractor Node

Uses an LLM to convert unstructured text into structured, typed parameters — bridging natural language and downstream nodes that expect specific data formats.

#### Configuration

| Setting | Description |
|---------|-------------|
| **Input** | Text variable to extract from |
| **Model** | Model with strong structured output support |
| **Parameters** | Name, type, description, required flag for each field |

**Parameter types:** `string` · `number` · `boolean` · `array` · `object`

#### Extraction Methods

| Method | When to Use |
|--------|-------------|
| **Function/Tool Calling** | Reliable; for models supporting it |
| **Prompt-based** | Fallback for models without function calling |

#### Output Variables

| Variable | Description |
|----------|-------------|
| Extracted parameters | One variable per defined parameter |
| `__is_success` | `1` if extraction succeeded, `0` if not |
| `__reason` | Failure reason (when extraction fails) |

---

## Data Nodes

### Knowledge Retrieval Node

Searches one or more knowledge bases and returns relevant document chunks as context for downstream LLM nodes.

#### Typical RAG Flow

```
[User Input] → [Knowledge Retrieval] → [LLM] → [Answer]
```

#### Configuration

| Setting | Description |
|---------|-------------|
| **Query source** | Text variable (e.g., `userinput.query`) or image variable (≤ 2 MB) |
| **Knowledge sources** | One or more existing knowledge bases |
| **Retrieval settings** | Node-level reranking and refinement |

#### Retrieval Options

| Option | Description |
|--------|-------------|
| **Weighted Score** | Balance semantic similarity vs. keyword matching (no extra cost) |
| **Rerank Model** | External model re-scores results by relevance |
| **Top K** | Maximum number of chunks returned |
| **Score Threshold** | Minimum similarity score for inclusion (default: 0.5) |
| **Metadata Filtering** | Restrict search to documents matching specific metadata conditions |

#### Output

A `result` variable — an array of document chunks, each containing:
- `content` — Text of the chunk
- `score` — Relevance score
- `title` — Document name
- `metadata` — Source attributes
- File information for any image attachments

---

### Doc Extractor Node

Converts uploaded files into plain text that language models can process.

#### Supported Formats

| Category | Formats |
|----------|---------|
| Text | TXT, Markdown, HTML |
| Office | DOCX, XLS/XLSX (→ Markdown table), CSV |
| PDF | Text-based PDFs (via pypdfium2) |
| Legacy Office | DOC, PPT/PPTX (require Unstructured API) |
| Email | EML, MSG |
| Other | EPUB, VTT, JSON, YAML, Properties |

> **Binary files** (images, audio) require specialized tools — not this node.

#### Input / Output

| Input | Output |
|-------|--------|
| Single file variable | `text` string |
| Array of file variables | `array[string]` — one string per file |

#### Processing Details

- Encoding detected via chardet (UTF-8 fallback)
- Spreadsheets converted to Markdown tables
- DOCX maintains paragraph and table ordering
- VTT merges consecutive utterances by speaker

**External dependency (Unstructured API):**
Set `UNSTRUCTURED_API_URL` and `UNSTRUCTURED_API_KEY` env vars for DOC, PPT/PPTX, EPUB support.

---

### Variable Aggregator Node

Merges variables from multiple conditional branches into a single unified variable for downstream use.

**Problem it solves:** When an If/Else node routes to different branches that each produce a similar output, the Aggregator eliminates duplicate downstream processing by combining those branch outputs into one variable.

#### Configuration

- All aggregated variables **must be the same data type**
- Supported types: `String` · `Number` · `Object` · `Boolean` · `Array`
- Outputs the value from whichever branch actually executes

**Multiple Aggregation Groups** (v0.6.10+): Define independent groups within a single node to aggregate different data types simultaneously.

---

### Variable Assigner Node

Writes values to **conversation variables** — variables that persist across multiple turns within a Chatflow session.

> **Chatflow only.** Workflow variables reset after each run; conversation variables survive the session.

#### Configuration

| Setting | Description |
|---------|-------------|
| **Variable** | Target conversation variable to update |
| **Set Variable** | Source data from an upstream node |
| **Operation Mode** | How to apply the update |

#### Operation Modes by Type

| Type | Available Operations |
|------|---------------------|
| `String` | Overwrite · Clear · Assign |
| `Number` | Overwrite · Clear · Assign · Add · Subtract · Multiply · Divide |
| `Boolean` | Overwrite · Clear · Assign |
| `Object` | Overwrite · Clear · Custom structure |
| `Array` | Overwrite · Clear · Append · Extend · Remove first · Remove last |

**Common use cases:** Smart memory systems · User preference storage · Progressive checklists

---

### List Operator Node

Filters, sorts, and selects elements from arrays.

**Supported types:** `array[string]` · `array[number]` · `array[file]` · `array[boolean]`

#### Operations

| Operation | Description |
|-----------|-------------|
| **Filter** | Keep elements matching conditions (by type, MIME type, name, size, etc.) |
| **Sort** | Order elements ascending or descending by any attribute |
| **Select** | Return first N items, the first record, or the last record |

#### Output Variables

| Variable | Description |
|----------|-------------|
| `result` | Full filtered and sorted array |
| `first_record` | First element of the result |
| `last_record` | Last element of the result |

**Typical use:** Separate a mixed `array[file]` into images and documents, routing each to the appropriate processor.

---

### Template Node

Uses **Jinja2 templating** to combine and format data from multiple sources into structured text output.

#### Features

**Variable substitution:**
```jinja
Hello, {{ user_name }}! Your score is {{ score | round(2) }}.
```

**Conditionals:**
```jinja
{% if score >= 90 %}
Excellent work!
{% else %}
Keep practicing.
{% endif %}
```

**Loops:**
```jinja
{% for item in items %}
{{ loop.index }}. {{ item }}
{% endfor %}
```

**Useful filters:**

| Filter | Effect |
|--------|--------|
| `upper` | Convert to uppercase |
| `lower` | Convert to lowercase |
| `round(n)` | Round to n decimal places |
| `replace(old, new)` | String substitution |
| `default(value)` | Fallback for missing data |
| `join(sep)` | Join array elements with separator |
| `strftime(fmt)` | Format dates |

**Output limit:** 80,000 characters

---

### Code Node

Executes custom **Python** or **JavaScript** code for transformations that preset nodes cannot handle.

#### Configuration

```python
# Example Python code node
def main(input_text: str, count: int) -> dict:
    words = input_text.split()[:count]
    return {
        "result": " ".join(words),
        "word_count": len(words)
    }
```

```javascript
// Example JavaScript code node
async function main({ input_text, count }) {
  const words = input_text.split(" ").slice(0, count);
  return {
    result: words.join(" "),
    word_count: words.length
  };
}
```

#### Available Libraries

| Language | Available |
|----------|-----------|
| Python | `json`, `math`, `datetime`, `re` (and pre-installed sandbox packages) |
| JavaScript | Standard built-in objects and methods |

#### Output Limits

| Type | Limit |
|------|-------|
| String | 80,000 characters |
| Number | −999,999,999 to 999,999,999 (10 decimal places for floats) |
| Object/Array | 5 levels of nesting |

#### Security Sandbox

Code runs in a **strict sandbox** — no file system access, no network requests, no system commands.

#### Error Handling

- Automatic retries: up to 10 attempts, intervals up to 5000 ms
- Define fallback strategies for persistent failures

**Self-hosted:** Start the sandbox service:
```bash
docker-compose -f docker-compose.middleware.yaml up -d
```

---

## Control Nodes

### If/Else Node

Evaluates conditions and routes the workflow to different branches.

#### Branch Types

| Branch | Condition |
|--------|-----------|
| **IF** | Primary condition is true |
| **ELIF** | Additional conditions checked when IF is false (multiple supported) |
| **ELSE** | Default fallback when no conditions match |

#### Available Condition Operators

**Text:**

| Operator | Description |
|----------|-------------|
| `contains` / `not contains` | Substring check |
| `starts with` / `ends with` | Prefix / suffix check |
| `is` / `is not` | Exact match |
| `is empty` / `is not empty` | Null/blank check |

**Numbers & Dates:**

| Operator | Description |
|----------|-------------|
| `greater than` / `less than` | Numeric comparison |
| `equals` / `not equals` | Exact match |
| `is empty` / `is not empty` | Null check |

#### Combining Conditions

| Logic | Behavior |
|-------|---------|
| **AND** | All conditions must be true |
| **OR** | Any one condition may be true |

---

### Iteration Node

Applies the same workflow steps to every element in an array — either sequentially or in parallel.

#### Built-in Variables (Inside the Iteration)

| Variable | Type | Description |
|----------|------|-------------|
| `items` | object | The current element being processed |
| `index` | number | Zero-based position of the current element |

#### Processing Modes

| Mode | Max Concurrent | Best For |
|------|----------------|----------|
| **Sequential** | 1 at a time | Order-dependent tasks, progressive streaming |
| **Parallel** | Up to 10 | Independent operations, batch processing |

#### Error Handling Options

| Strategy | Behavior |
|----------|---------|
| **Terminate** | Stop immediately; return the error |
| **Continue on Error** | Skip failed items; output `null` for failures |
| **Remove Failed Results** | Skip failed items; exclude from output array |

#### Converting Array Output to Text

```python
# Code node approach
return { "result": "\n".join(items) }
```

```jinja
{# Template node approach #}
{{ items | join("\n") }}
```

---

### Loop Node

Creates **state-dependent** repeated cycles where each iteration builds on the previous result — unlike Iteration, which processes items independently.

| Aspect | Loop | Iteration |
|--------|------|-----------|
| Dependency | Each cycle uses previous output | Each item processed independently |
| Parallelism | Sequential only | Sequential or parallel |
| Best for | Refinement, convergence | Batch processing |

#### Configuration

| Control | Purpose |
|---------|---------|
| **Termination Condition** | Expression evaluated after each cycle; exits when true |
| **Maximum Loop Count** | Safety limit to prevent infinite loops |
| **Exit Loop Node** | Explicit node to break out of the loop early |

#### Example: Iterative Poem Refinement

```
[LLM: Generate draft] → [LLM: Improve draft] → [Counter: increment]
        ↑                                              |
        └──────────────── Loop back ──────────────────┘
                    (until count == 4)
```

---

### Human Input Node

Pauses the workflow and requests input or a decision from a human before continuing.

#### Delivery Methods

| Method | Description |
|--------|-------------|
| **Web app** | Request appears in the web app interface; user responds directly |
| **Email** | Request link is sent to one or more recipients |

> The request closes after the **first response**, regardless of delivery method.

#### Form Configuration

- Markdown formatting for clear context presentation
- Dynamic variables to display relevant workflow data
- Custom input fields that become downstream variables

#### Action Buttons

Define multiple action buttons (e.g., **Approve** / **Reject** / **Regenerate**), each routing the workflow to a different downstream path.

#### Timeout

Set a response deadline. If no response occurs within the time limit, the workflow either ends or follows a configured fallback path (notification, retry, etc.).

---

## End Nodes

### Answer Node *(Chatflow only)*

Delivers the workflow's response to the user in a Chatflow. Supports streaming, multimodal content, and markdown formatting.

> **Chatflow only.** Workflow apps use the Output node instead.

#### Features

- Fixed text combined with `{{ variable_name }}` references
- Multimodal: text + images + file downloads in a single stream
- Multiple Answer nodes throughout a chatflow for staged delivery
- Streaming order determined by the **variable order in the Answer node**, not upstream execution order

---

### Output Node *(Workflow only)*

Marks the end of a Workflow and defines what data is returned to the caller.

> **Optional** in a workflow — but without it, no data is returned to users or API callers.

**Add output variables** to specify which upstream node outputs should be returned.

> Workflows used as backend APIs **must** have an Output node to return values to API callers.

---

## Integration Nodes

### HTTP Request Node

Connects the workflow to any external API or web service.

#### Supported Methods

| Method | Use Case |
|--------|---------|
| `GET` | Retrieve data without side effects |
| `HEAD` | Fetch headers only |
| `POST` | Submit data; create resources |
| `PUT` | Create or fully replace a resource |
| `PATCH` | Partially update an existing resource |
| `DELETE` | Remove a resource |

#### Configuration

**Variable substitution in URL and body:**
```
https://api.example.com/users/{{ user_id }}
```

**Authentication options:**
- None
- API Key (Basic, Bearer, or custom header)

**Request body formats:** JSON · Form data · Binary · Raw text

**Timeout settings:** Connection · Read · Write (prevents workflow hangs)

#### File Handling

- Downloads auto-detected by MIME type and byte-sampling → available as file variables
- Uploads: use Binary body type

#### Response Variables

| Variable | Description |
|----------|-------------|
| `body` | Response body content |
| `status_code` | HTTP status code |
| `headers` | Response headers |
| `files` | Downloaded files |
| `size` | Response size in bytes |

#### Error Handling

- Automatic retries: up to 10 attempts
- Define alternative execution paths for persistent failures

---

### Tools Node

Integrates with external services via pre-built tool interfaces.

#### Tool Categories

| Category | Description |
|----------|-------------|
| **Built-in Tools** | Pre-configured integrations (Google Search, weather, etc.) |
| **Custom Tools** | User-imported via OpenAPI/Swagger spec |
| **Workflow Tools** | Published Dify workflows exposed as tools |
| **MCP Tools** | External Model Context Protocol server tools |

#### Advantages over HTTP Request

- Form-based configuration with built-in validation
- Centralized authentication management (workspace Settings)
- Automatic retry logic (up to 10 attempts, ≤ 5-second intervals)
- Type-safe outputs for seamless downstream node compatibility

---

## Node Quick Reference

| Node | Type | App Support |
|------|------|-------------|
| User Input | Start | Workflow + Chatflow |
| Schedule Trigger | Start | Workflow only |
| Plugin Trigger | Start | Workflow only |
| Webhook Trigger | Start | Workflow only |
| LLM | AI | Both |
| Agent | AI | Both |
| Question Classifier | AI | Both |
| Parameter Extractor | AI | Both |
| Knowledge Retrieval | Data | Both |
| Doc Extractor | Data | Both |
| Variable Aggregator | Data | Both |
| Variable Assigner | Data | Chatflow only |
| List Operator | Data | Both |
| Template | Data | Both |
| Code | Data | Both |
| If/Else | Control | Both |
| Iteration | Control | Both |
| Loop | Control | Both |
| Human Input | Control | Both |
| HTTP Request | Integration | Both |
| Tools | Integration | Both |
| Answer | End | Chatflow only |
| Output | End | Workflow only |
