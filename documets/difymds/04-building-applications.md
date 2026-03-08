# Building Applications

This section covers the tools, techniques, and best practices for constructing workflows on the Dify canvas.

---

## Keyboard Shortcuts

Working efficiently on the canvas requires knowing the shortcuts available.

### Canvas Shortcuts

| Action | Windows / Linux | macOS |
|--------|-----------------|-------|
| **Go to Anything** | `Ctrl + K` | `Cmd + K` |
| **Undo** | `Ctrl + Z` | `Cmd + Z` |
| **Redo** | `Ctrl + Y` or `Ctrl + Shift + Z` | `Cmd + Y` or `Cmd + Shift + Z` |
| **Zoom In** | `Ctrl + =` | `Cmd + =` |
| **Zoom Out** | `Ctrl + -` | `Cmd + -` |
| **Fit to View** | `Ctrl + 1` | `Cmd + 1` |
| **Pan Tool** | `H` | `H` |
| **Select Tool** | `V` | `V` |
| **Run Workflow** | `Alt + R` | `Option + R` |

### Node Shortcuts (Node Must Be Selected)

| Action | Windows / Linux | macOS |
|--------|-----------------|-------|
| **Copy** | `Ctrl + C` | `Cmd + C` |
| **Paste** | `Ctrl + V` | `Cmd + V` |
| **Duplicate** | `Ctrl + D` | `Cmd + D` |
| **Delete** | `Delete` | `Delete` |
| **Auto-arrange** | `Ctrl + O` | `Cmd + O` |
| **Show dependencies** | Hold `Shift` | Hold `Shift` |

---

## Go to Anything

A keyboard-driven universal search for navigating all Dify resources without leaving your keyboard.

**Open:** `Ctrl + K` (Windows) / `Cmd + K` (macOS)
**Close:** `Esc`

### Search Prefixes

| Prefix | Searches |
|--------|---------|
| `@app` | Applications |
| `@plugin` | Plugins (install or find) |
| `@kb` or `@knowledge` | Knowledge bases |
| `@node` | Workflow nodes (within the current workflow) |

### Slash Commands

| Command | Action |
|---------|--------|
| `/theme` | Toggle appearance (light/dark) |
| `/language` | Switch interface language |

### Example Searches

| Query | Result |
|-------|--------|
| `@app analytics` | Apps matching "analytics" |
| `@plugin slack` | Slack plugin |
| `@kb company handbook` | Knowledge base titled "company handbook" |
| `@node summary` | Workflow node named "summary" |

---

## Orchestrating Nodes

### Serial (Sequential) Execution

Connect nodes in a chain. Each node waits for the previous one to complete.

```
[User Input] → [LLM] → [Code] → [Output]
```

### Parallel Execution

Connect multiple nodes to the same source. They all run simultaneously.

```
                    ┌→ [LLM: French]  ─┐
[User Input] →  ────┤                   ├→ [Variable Aggregator] → [Output]
                    └→ [LLM: Spanish] ─┘
```

**Parallel limits:**
- Max **10 branches** per node
- Max **3 nested levels** of parallelism

### Variable Scope in Parallel Branches

| Context | Can Access |
|---------|-----------|
| Sequential flow | Outputs from all prior nodes |
| Inside a parallel branch | Outputs from before the parallel split only |
| After parallel merge | All parallel branch outputs |

### Answer Node Streaming with Parallel Outputs

When an Answer node references variables from parallel branches, content streams progressively:

> "Content streams up to the first unresolved variable. Once that variable's node completes, streaming continues to the next unresolved variable."

The streaming **order is determined by the variable order in the Answer node**, not the underlying execution order.

---

## Error Handling

Four node types support built-in error handling: **LLM, HTTP Request, Code, and Tools**.

### Strategies

| Strategy | Behavior | Best Used When |
|----------|----------|----------------|
| **None** *(default)* | Stops the entire workflow; shows original error | Testing, or when failure must halt processing |
| **Default Value** | Substitutes a fallback value; workflow continues | Graceful degradation acceptable |
| **Fail Branch** | Activates a separate error-handling sub-workflow | Robust production apps needing error logging, alerts, or recovery |

### Default Value Example

If an LLM node hits a rate limit, return a canned message instead of crashing:
```
"Sorry, I'm temporarily unavailable. Please try again in a few minutes."
```

### Fail Branch Example

On HTTP Request failure:
1. Log error details to an external system
2. Send an alert email
3. Return a safe fallback response to the user

### Error Variables

Available when using **Default Value** or **Fail Branch** strategies:

| Variable | Description |
|----------|-------------|
| `error_type` | Category of the error |
| `error_message` | Specific error details |

### Error Handling in Iteration Nodes

| Mode | Behavior |
|------|---------|
| `terminated` | Stop immediately on first failure (default) |
| `continue-on-error` | Skip failed items; output `null` for failures |
| `remove-abnormal-output` | Skip failed items; exclude from output array |

### Error Handling in Loop Nodes

Loop nodes **terminate immediately** if any child node fails.

---

## MCP Tools (Model Context Protocol)

Connect your workflow to external tools served by MCP servers.

> Dify currently supports MCP servers using **HTTP transport**.

### Adding an MCP Server

1. Navigate to **Tools → MCP**
2. Click **"Add MCP Server (HTTP)"**
3. Provide:

| Field | Notes |
|-------|-------|
| **Server URL** | Endpoint where the MCP server operates |
| **Name & Icon** | Descriptive identifier; icon auto-populated if available |
| **Server ID** | Unique, ≤ 24 chars, lowercase + numbers + `_` + `-` |

> **Critical:** Never change the Server ID after apps start using it — doing so breaks all dependent apps.

### Server Management

| Action | Description |
|--------|-------------|
| **Refresh** | Pull updated tool list from the server |
| **Re-authorize** | Fix authentication issues |
| **Edit** | Modify server details (ID excluded) |
| **Remove** | Disconnect the server |

### Tool Customization

When using MCP tools in a workflow:
- Override default tool descriptions for clarity
- Set parameters as **automatic** (AI-determined at runtime) or **fixed** (unchanging constant value)

### Deployment Note

Exported apps include MCP server IDs. To reuse an exported app elsewhere, add the same MCP server with the **same ID** in the target workspace.

---

## Version Control

Track, manage, and roll back changes to your Chatflow or Workflow applications.

### Version States

| State | Description | Editable? |
|-------|-------------|-----------|
| **Current Draft** | Your working copy; not live | Yes |
| **Latest Version** | Active version end users see | No (publish to update) |
| **Previous Versions** | Archived releases | No (can restore to draft) |

### Publishing

Navigate to **Publish → Publish Update**:
1. Current draft → becomes the new Latest Version
2. A fresh draft is automatically created

> **Warning:** Publishing immediately replaces the live app. Users see changes on their next interaction.

### Version History

Click the **history icon** to browse all versions. Filter by:
- All versions vs. your versions only
- Named versions only (hide auto-generated labels)

### Version Actions

| Action | Description |
|--------|-------------|
| **Name a version** | Add a meaningful label (e.g., "v2 — added FAQ routing") |
| **Add release notes** | Document what changed |
| **Restore to draft** | Roll back by restoring a previous version to your working draft |
| **Delete** | Remove old versions (current draft and latest version cannot be deleted) |

### Best Practices

- Always test in draft before publishing
- Use descriptive names for significant releases: `"v3 — KB integration"`, `"hotfix — rate limit handling"`
- Export DSL before major changes as an additional backup

---

## Additional App Features

Access extra capabilities via the **Features** button (top-right of the canvas).

### Workflow Apps

> File upload via Features is **deprecated** for Workflow apps. Use file variables on the User Input node instead.

**Image processing setup (Workflow):**
1. Enable **Image Upload** in Features
2. Add an LLM node with vision enabled
3. Set Vision source to `sys.files`
4. Connect to the Output node

### Chatflow Apps

| Feature | Description |
|---------|-------------|
| **Conversation Opener** | AI proactively introduces itself at session start |
| **Follow-up Suggestions** | Generates 3 contextual next questions after each response |
| **Text-to-Speech** | Converts AI responses to audio |
| **File Upload** | Allows users to attach files via paperclip icon |
| **Citation Display** | Shows knowledge source references below responses |
| **Content Moderation** | Filters inappropriate input or output |

### File Upload Details

Files uploaded by users appear in the `sys.files` variable.

| File Type | Processing Required |
|-----------|---------------------|
| Documents (PDF, DOCX, etc.) | Doc Extractor node → then LLM |
| Images | Vision-enabled LLM (direct) |
| Mixed types | List Operator node to separate, then route appropriately |
| Audio / Video | External marketplace tools |

**Constraints:**

| Limit | Value |
|-------|-------|
| Max file size | 15 MB |
| Max simultaneous uploads | 10 files |

---

## Workflow Design Patterns

### Pattern 1: RAG Chatbot

```
[User Input: query]
      ↓
[Knowledge Retrieval: search KB]
      ↓
[LLM: answer using context]
      ↓
[Answer]
```

### Pattern 2: Document Processor

```
[User Input: file upload]
      ↓
[Doc Extractor: extract text]
      ↓
[LLM: summarize / analyze]
      ↓
[Output]
```

### Pattern 3: Multi-Platform Content Generator

```
[User Input: draft + platforms + files]
      ↓
[Parameter Extractor: parse platforms → array]
      ↓
[If/Else: valid platforms?]
  YES ↓
[List Operator ×2: split files by type]
      ↓
[Doc Extractor]   [LLM with Vision]
      ↓                ↓
[LLM: integrate all info]
      ↓
[Iteration: per platform]
  └→ [LLM: generate post]
      ↓
[Template: format markdown]
      ↓
[Output]
```

### Pattern 4: Approval Workflow

```
[Trigger or User Input]
      ↓
[LLM: generate draft content]
      ↓
[Human Input: Approve / Reject / Regenerate]
  Approve ↓          Regenerate ↓         Reject ↓
[Publish Tool]     [Loop back to LLM]   [Notify Tool]
```

### Pattern 5: Branch & Merge

```
[User Input]
      ↓
[Question Classifier]
  Branch A ↓        Branch B ↓        Branch C ↓
[KB Retrieval]    [HTTP: external]  [Direct reply]
      ↓                ↓                  ↓
      └────────────────┴──────────────────┘
                       ↓
            [Variable Aggregator]
                       ↓
                   [LLM: respond]
                       ↓
                   [Answer]
```
