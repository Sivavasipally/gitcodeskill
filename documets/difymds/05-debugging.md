# Debugging

Dify provides a comprehensive set of debugging tools to help you inspect, test, and fix workflows before and after publishing.

---

## Overview of Debugging Tools

| Tool | Purpose |
|------|---------|
| **Step Run** | Test individual nodes in isolation |
| **Variable Inspector** | Inspect and modify live variable values between nodes |
| **Run History** | View full execution traces with timing and data flow |
| **Error Type Reference** | Understand and resolve specific error codes |

---

## Step Run (Individual Node Testing)

Test any single node independently without running the full workflow.

### How to Test a Node

1. Select the node on the canvas
2. Open its settings panel
3. Enter test input data
4. Click **Run** (or use `Option + R` / `Alt + R` for the full workflow)
5. View results in the **"Last run"** section of the panel

> **Limitation:** Answer and Output (End) nodes **cannot** be tested in isolation.

### What "Last Run" Shows

| Field | Description |
|-------|-------------|
| **Input** | Exact data that was passed into the node |
| **Output** | Data the node produced |
| **Duration** | Processing time in milliseconds |
| **Error** | Error message and type (if the node failed) |

### Sequential Testing with Variable Caching

Run nodes one after another in sequence. The Variable Inspector captures each node's output and caches it.

**Workflow:**
1. Run Node A → output cached in Variable Inspector
2. Edit cached value if needed
3. Run Node B → uses modified cached value (not original Node A output)
4. Continue through the chain

This eliminates the need to re-run expensive upstream nodes (like LLM calls) when exploring how downstream nodes behave with different inputs.

---

## Variable Inspector

A real-time panel showing all variable values as they flow through your workflow.

> "Captures inputs and outputs from each node after they run, so you can see what's happening and test different scenarios."

### Accessing the Inspector

The Variable Inspector panel appears at the **bottom of the screen** after any node execution.

### Viewing Variables

- Displays all output variables from executed nodes
- Click any variable to expand and examine its complete content
- Supports complex types: strings, numbers, objects, arrays, files

### Editing Variables

Click any variable value to modify it inline. When you run downstream nodes:
- They use your **modified value** instead of the original
- This allows "what-if" testing without rerunning upstream nodes

**Example:**
```
LLM produces SQL:  SELECT * FROM users WHERE id = 1
Edit to:           SELECT * FROM users WHERE id = 42
→ Rerun database node → observe different results
```

> **Note:** Editing a variable in the inspector does **not** modify the node's "Last run" record.

### Resetting Variables

| Action | How |
|--------|-----|
| Restore one variable | Click the **revert icon** next to it |
| Clear everything | Click **"Reset all"** |

---

## Run History

Dify automatically logs every workflow execution — both during development (draft testing) and after publishing (production runs).

> **Note:** Debugging sessions (Step Run) **are not** included in Run History. For production monitoring, use the Logs section in your app's Monitor tab.

### Accessing Run History

From the canvas: click the **history icon** in the top toolbar.

### Log Entry Sections

Each execution generates a complete log with three sections:

| Section | Contents |
|---------|---------|
| **Result** | The final output returned to the user; error messages if the workflow failed |
| **Detail** | Original input, final output, and system metadata (timestamps, token usage, model info) |
| **Tracing** | Execution visualization — which nodes ran, in what order, how long each took, and how data flowed between them |

### Node-Level History

Select any individual node → open its settings panel → view **"Last run"** for:
- Input data
- Output data
- Execution time

---

## Error Types Reference

### Code Node Errors

| Error Code | Cause | Fix |
|------------|-------|-----|
| `CodeNodeError` | Python/JavaScript code threw an unhandled exception | Add try/except or try/catch in your code |
| `OutputValidationError` | Return value type doesn't match declared output type | Ensure returned dict keys match declared outputs with correct types |
| `DepthLimitError` | Returned object/array exceeds 5 nesting levels | Flatten the data structure |
| `CodeExecutionError` | Sandbox service unavailable | Check sandbox service is running (`docker-compose -f docker-compose.middleware.yaml up -d`) |

### LLM Node Errors

| Error Code | Cause | Fix |
|------------|-------|-----|
| `VariableNotFoundError` | Prompt references a variable that doesn't exist in the workflow | Check variable names in your prompt match upstream node outputs |
| `InvalidContextStructureError` | Array or object passed to the Context field (strings only) | Convert the variable to a string before passing to Context |
| `NoPromptFoundError` | Prompt field is empty | Add content to the System or User prompt |
| `ModelNotExistError` | No model selected in LLM configuration | Open the node and select a model |
| `LLMModeRequiredError` | Selected model has no valid API credentials | Add or verify the API key in Settings → Model Providers |
| `InvalidVariableTypeError` | Invalid Jinja2 syntax or incorrect text formatting | Validate Jinja2 syntax; check for unclosed `{{` brackets |

### HTTP Request Node Errors

| Error Code | Cause | Fix |
|------------|-------|-----|
| `AuthorizationConfigError` | Missing or incorrect auth configuration | Verify API key or Bearer token is set correctly |
| `InvalidHttpMethodError` | HTTP method not supported | Use GET, HEAD, POST, PUT, PATCH, or DELETE |
| `ResponseSizeError` | API response exceeds 10 MB | Add query parameters to reduce response size, or process in chunks |
| `FileFetchError` | Referenced file variable is inaccessible | Ensure the file variable exists and is correctly scoped |
| `InvalidURLError` | URL is malformed or unreachable | Validate the URL format and network connectivity |

### Tool Node Errors

| Error Code | Cause | Fix |
|------------|-------|-----|
| `ToolParameterError` | Input parameters don't match the tool's schema | Review the tool's required parameter types and names |
| `ToolFileError` | File access issue within the tool | Check file variable type compatibility with the tool |
| `ToolInvokeError` | External tool API returned an error | Check the external service status; inspect the tool's error message |
| `ToolProviderNotFoundError` | Tool provider is not installed or misconfigured | Install the tool from the Marketplace; verify credentials |

### System-Level Errors

| Error Code | Cause | Fix |
|------------|-------|-----|
| `InvokeConnectionError` | Network connection failure to the AI provider | Check network; verify provider API endpoint is reachable |
| `InvokeServerUnavailableError` | AI provider returned 503 (service unavailable) | Wait and retry; check provider status page |
| `InvokeRateLimitError` | API rate limit exceeded | Reduce request frequency; add retry logic with backoff |
| `QuotaExceededError` | Usage quota has been reached | Upgrade plan or wait for quota reset |

---

## Debugging Checklist

Use this checklist before publishing a workflow:

### Workflow Structure

- [ ] All required nodes are connected
- [ ] No orphaned nodes on the canvas
- [ ] Output / Answer node is present
- [ ] Parallel branches are correctly merged at a Variable Aggregator or converging point

### Node Configuration

- [ ] All LLM nodes have a model selected
- [ ] All LLM nodes have non-empty prompts
- [ ] API keys are configured for all providers used
- [ ] HTTP Request nodes use valid URLs and correct auth
- [ ] Tool nodes have required credentials configured

### Variables

- [ ] All variable references in prompts use correct names (`{{ variable }}`)
- [ ] Context fields receive strings, not arrays or objects
- [ ] Iteration node inputs are arrays
- [ ] Variable Aggregator types match across all branches

### Error Handling

- [ ] LLM, HTTP, Code, and Tool nodes have error handling configured
- [ ] Iteration node error mode is appropriate for the use case
- [ ] Human Input node has a timeout configured

### Testing

- [ ] Step Run tested on each major node
- [ ] Edge cases tested (empty input, wrong file type, API timeout)
- [ ] Parallel branches verified to merge correctly
- [ ] Full workflow Test Run completed successfully
