# Knowledge Base

Dify's Knowledge feature integrates custom data into AI applications through **Retrieval-Augmented Generation (RAG)** — enabling accurate, grounded responses based on your own content.

---

## How RAG Works

```
User Query
    ↓
[Retrieval]   → Search knowledge base for relevant chunks
    ↓
[Augmentation] → Combine retrieved chunks with user query
    ↓
[Generation]   → LLM produces an answer grounded in your content
    ↓
Response to User
```

### Benefits

| Benefit | Description |
|---------|-------------|
| **Accuracy** | Answers drawn from verified, current content |
| **Reduced hallucination** | LLM references real documents instead of guessing |
| **Updatable** | Add or update documents without retraining the model |
| **Source attribution** | Users see exactly where information came from |

### Common Use Cases

- Customer support chatbots backed by product documentation
- Internal employee knowledge portals
- Research assistants summarizing domain-specific materials
- Content generation grounded in brand guidelines

---

## Creating a Knowledge Base

### Option A: Quick Create

1. Click **Knowledge → Create Knowledge**
2. Choose a data source (upload files, sync from Notion, sync from website, or start empty)
3. Configure chunk settings and preview the result
4. Set index method and retrieval settings
5. Wait for processing to complete

> **Important:** Once a knowledge base is created, its **data source type** cannot be changed later.

### Option B: Knowledge Pipeline

Use a visual pipeline for advanced, customizable processing workflows. See the [Knowledge Pipeline](#knowledge-pipeline) section below.

### Option C: External Knowledge Base API

Connect Dify to an independently managed knowledge system via API. See [External Knowledge Base](#external-knowledge-base) below.

---

## Data Sources

### Upload Local Files

| Limit | Value |
|-------|-------|
| Files per upload | 5 (50 on paid Dify Cloud plans) |
| File size | 15 MB max per file |
| Image auto-extraction | Images ≤ 2 MB extracted as chunk attachments |

**Supported file types:**
PDF · TXT · Markdown · HTML · DOCX · XLS/XLSX · CSV · PPT/PPTX · EML · MSG · EPUB · VTT · JSON · YAML

### Sync from Notion

1. Bind Notion during knowledge base creation (or via **Settings → Data Sources**)
2. Select pages/databases to import
3. Note: images and file attachments are **not** imported; table data converts to text
4. Click **Sync** on any document to pull latest Notion content (costs embedding tokens)

**Integration types:**
- **Internal Integration**: Workspace-owner only; configure `NOTION_INTERNAL_SECRET`
- **Public Integration**: Broader access; configure `NOTION_CLIENT_ID` and `NOTION_CLIENT_SECRET`

### Sync from Website

Requires a web crawling service (Firecrawl or Jina Reader):

| Service | Best For |
|---------|----------|
| **Firecrawl** | Advanced crawling with refined control options |
| **Jina Reader** | Fast, simple API for web content parsing |

**Setup:**
1. Configure credentials in **Settings → Data Sources**
2. In knowledge base creation: **Sync from website**
3. Choose provider, enter target URL
4. Configure: sub-page crawling, max pages, depth, path exclusions, sitemap use

---

## Chunking and Cleaning Text

Documents are split into **chunks** — the fundamental retrieval units. Chunk quality directly impacts answer quality.

> **Note:** The **chunk mode** cannot be changed after the knowledge base is created. Delimiter and max length can be adjusted at any time.

### Chunk Modes

#### General Mode

All chunks share the same settings. Matched chunks are returned directly as retrieval results.

| Setting | Description |
|---------|-------------|
| **Delimiter** | Character(s) marking split points (e.g., `\n\n` for paragraphs, `\n` for lines) |
| **Maximum chunk length** | Max characters per chunk; force-splits text that exceeds this limit |
| **Chunk overlap** | Characters repeated at the boundary between adjacent chunks (preserves context) |

#### Parent-Child Mode

Two-tier system: **child chunks** for precise matching + **parent chunks** for rich context.

When a query matches a child chunk, its parent chunk is returned — giving the LLM more context.

**Parent chunk settings:**

| Mode | Description | Best For |
|------|-------------|----------|
| **Paragraph** | Document split into multiple parent chunks by delimiter | Long, well-structured documents |
| **Full Doc** | Entire document is one parent chunk | Short, cohesive documents |

> Full Doc mode processes only the first **10,000 tokens**. Content beyond this is truncated. Parent chunks cannot be edited after creation.

**Child chunk settings:** Separate delimiter and max length for sub-dividing each parent.

#### Comparison

| Dimension | General Mode | Parent-Child Mode |
|-----------|-------------|------------------|
| Chunking | Single-tier | Two-tier |
| Retrieval | Matched chunk returned directly | Child matches → parent returned |
| Index methods | High Quality + Economical | High Quality only |
| Best for | Simple, self-contained content (FAQs, glossaries) | Dense technical or research documents |

### Text Pre-Processing Options

| Option | Effect |
|--------|--------|
| Replace consecutive spaces/newlines | Normalize whitespace (3+ newlines → 2; multiple spaces → 1) |
| Remove URLs and email addresses | Strip links and addresses from chunks |

### Summary Auto-Generation

*(Self-hosted deployments only)*

Automatically generate summaries for all chunks:
- Summaries are embedded and indexed for retrieval
- When a summary matches a query, its chunk is also returned
- Vision-capable LLMs can base summaries on both text and attached images
- Can be regenerated or manually edited per document

---

## Index Methods and Retrieval

### High-Quality Index

Converts chunks into vector embeddings for **semantic search**.

| Retrieval Strategy | Description |
|-------------------|-------------|
| **Vector Search** | Query converted to vector; nearest chunks returned |
| **Full-Text Search** | Traditional keyword indexing |
| **Hybrid Search** | Both simultaneously; configurable weighting |
| **Q&A Mode** | Question-to-question matching (self-hosted only) |

> High-Quality cannot be converted to Economical after creation.

### Economical Index

Uses 10 keywords per chunk. No embedding tokens consumed; lower accuracy.

- **Inverted indexing** only
- Adjust TopK only

### Retrieval Settings

| Parameter | Default | Description |
|-----------|---------|-------------|
| **TopK** | 3 | Maximum chunks returned |
| **Score Threshold** | 0.5 | Minimum similarity score for inclusion |
| **Rerank Model** | None | External model for re-scoring results by relevance |

**Hybrid Search Weighting:**

| Setting | Effect |
|---------|--------|
| Semantic = 1 | Semantic retrieval only (cross-lingual friendly) |
| Keyword = 1 | Keyword matching only (exact terminology) |
| Custom ratio | Balance both (e.g., 70% semantic / 30% keyword) |

---

## Knowledge Pipeline

Knowledge pipelines provide a visual workflow builder for sophisticated document processing.

### Core Flow

```
Data Source → Extractor → Chunker → Knowledge Base → (User Input)
```

### Creating a Pipeline

| Method | Description |
|--------|-------------|
| **Blank** | Build a fully custom pipeline |
| **Built-in Templates** | Start from pre-configured official templates |
| **Import DSL** | Load an exported pipeline configuration |

### Built-in Templates

| Template | Best For |
|----------|----------|
| **General Mode-ECO** | Basic paragraph division + economical indexing |
| **Parent-child-HQ** | Complex documents needing context preservation |
| **Simple Q&A** | Convert tabular data into Q&A format |
| **LLM Generated Q&A** | AI-generated structured question pairs |
| **Convert to Markdown** | Office files (DOCX, XLSX, PPTX) |

### Data Sources in Pipelines

| Source | Limits |
|--------|--------|
| File Upload | 50 files, 15 MB each |
| Notion | Workspace pages and databases |
| Jina Reader | Fast web content parsing |
| Firecrawl | Advanced web crawling |
| Google Drive / Dropbox / OneDrive | Cloud storage (OAuth) |

### Extractors

| Extractor | Description |
|-----------|-------------|
| **Doc Extractor** | Converts various formats for LLM processing |
| **Dify Extractor** | Built-in parser; extracts and stores image attachments |
| **Unstructured** | Customizable extraction strategies |

### Chunkers

| Chunker | Best For |
|---------|----------|
| **General Chunker** | Simple documents, basic structure |
| **Parent-child Chunker** | Complex documents needing rich context |
| **Q&A Processor** | Structured Q&A data from spreadsheets |

### Data Source Authorization

| Platform | API Key | OAuth |
|----------|---------|-------|
| Notion | ✅ | ✅ |
| Jina Reader | ✅ | — |
| Firecrawl | ✅ | — |
| Google Drive | — | ✅ |
| Dropbox | — | ✅ |
| OneDrive | — | ✅ |

### Publishing a Pipeline

1. Configure and debug the pipeline (use the Test Run button)
2. Click **Publish** and confirm

> **Warning:** Once published, the **chunk structure cannot be modified**.

**Post-publish options:**
- Add Documents (go directly to the document upload interface)
- Access API (view knowledge base API documentation)
- Publish as a Knowledge Pipeline template (requires paid plan)

---

## External Knowledge Base

Connect Dify to an independently managed RAG system or cloud knowledge service (e.g., AWS Bedrock, custom RAG algorithms).

### Connection Examples

**LlamaCloud (via official plugin):**
1. Find the `LlamaCloud` plugin in the Dify Marketplace
2. Install and configure with your LlamaCloud API key
3. The connected external knowledge base appears in your knowledge base list

### External Knowledge API Specification

Your external service must expose a retrieval endpoint.

**Request (POST `<your-endpoint>/retrieval`):**

```json
{
  "knowledge_id": "unique-kb-id",
  "query": "user search question",
  "retrieval_setting": {
    "top_k": 5,
    "score_threshold": 0.5
  },
  "metadata_condition": {
    "logical_operator": "and",
    "conditions": [
      {
        "name": "language",
        "comparison_operator": "is",
        "value": "English"
      }
    ]
  }
}
```

**Authentication:** Bearer token in Authorization header.

**Response (HTTP 200):**

```json
{
  "records": [
    {
      "content": "Text chunk content here...",
      "score": 0.92,
      "title": "Document Title",
      "metadata": {
        "author": "Jane Smith",
        "date": "2024-01-15"
      }
    }
  ]
}
```

**Error Codes:**

| Code | Meaning | Fix |
|------|---------|-----|
| 1001 | Invalid Authorization header format | Check Bearer token format |
| 1002 | Authorization failed | Verify API key |
| 2001 | Knowledge does not exist | Check the external repository |

---

## Managing Knowledge Documents

### Document Actions

| Action | Description |
|--------|-------------|
| **Add** | Import a new document |
| **Modify Chunk Settings** | Adjust per-document chunking (not chunk structure) |
| **Delete** | Permanently remove (cannot be undone) |
| **Enable / Disable** | Temporarily include or exclude from retrieval |
| **Archive / Unarchive** | Keep but exclude from retrieval; read-only when archived |
| **Generate Summary** | Auto-generate chunk summaries (self-hosted only) |
| **Edit** | Modify content by editing individual chunks |
| **Rename** | Change the document's display name |

**Auto-disable thresholds (Dify Cloud):**

| Plan | Inactivity Before Auto-Disable |
|------|-------------------------------|
| Sandbox | 7 days |
| Professional / Team | 30 days |

### Chunk Actions

| Action | Description |
|--------|-------------|
| **Add** | Add new chunks manually or in batch |
| **Delete** | Permanently remove (cannot be undone) |
| **Enable / Disable** | Include or exclude from retrieval |
| **Edit** | Modify content; chunk marked as **Edited** |
| **Add/Edit/Delete Keywords** | For Economical index (up to 10 keywords per chunk) |
| **Manage Image Attachments** | Add/remove images; up to 10 per chunk |
| **Add/Edit/Delete Summary** | Enhance retrievability with descriptive summaries |

---

## Metadata

Metadata allows fine-grained organization, filtering, and access control of knowledge base documents.

### Metadata Concepts

| Term | Definition | Example |
|------|-----------|---------|
| **Field** | Label for a metadata attribute | `author`, `language`, `department` |
| **Value** | Data stored in a field | `"Jane Smith"`, `"English"`, `"Engineering"` |
| **Value Type** | Data category | String · Number · Time |

### Built-in vs. Custom Metadata

| Aspect | Built-in | Custom |
|--------|----------|--------|
| Default fields | `document_name`, `uploader`, `upload_date`, `last_update_date`, `source` | None |
| Activation | Disabled by default; enable manually | Add as needed |
| Generation | Auto-extracted by the system | User-defined |
| Editing | Cannot be modified once generated | Fully editable |
| Scope | All documents (when enabled) | Manual per-document assignment |

### Creating Custom Fields

1. Navigate to your knowledge base → **Metadata** panel
2. Click **+Add Metadata**
3. Choose type: String · Number · Time
4. Name the field (lowercase, numbers, underscores only)
5. Click Save

### Bulk Editing Metadata

1. Select documents using checkboxes in the knowledge base
2. Click **Metadata** in the bottom action bar
3. Add fields, update values, or delete fields across all selected documents
4. Click Save

---

## Integrating Knowledge in Applications

### Connecting a Knowledge Base to an App

1. Open your app in Studio
2. In **Context**, click **Add** and select one or more knowledge bases
3. Configure **Retrieval Settings** in Context Settings
4. Enable **Citation and Attribution** in Add Features (optional)
5. Test in Debug and Preview
6. Publish

### Multi-Knowledge Base Retrieval Settings

When multiple knowledge bases are connected:

**Weighted Score** (no extra cost):

| Setting | Effect |
|---------|--------|
| Semantic = 1 | Semantic retrieval only |
| Keyword = 1 | Keyword retrieval only |
| Custom | Balance both |

**Rerank Model** (higher accuracy, additional cost):
Configure in **Settings → Model Providers** (Cohere, Jina AI, etc.)

### Metadata Filtering in Workflows

In a **Knowledge Retrieval** node, set the filter mode:

| Mode | Description |
|------|-------------|
| **Disabled** | No filtering (default) |
| **Automatic** | Auto-configure filters from query variables |
| **Manual** | Configure filters explicitly |

**Manual filter operators by field type:**

| Type | Operators |
|------|-----------|
| String | `is`, `is not`, `is empty`, `is not empty`, `contains`, `not contains`, `starts with`, `ends with` |
| Number | `=`, `≠`, `>`, `<`, `≥`, `≤`, `is empty`, `is not empty` |
| Date | `is`, `before`, `after`, `is empty`, `is not empty` |

> Filter values are **case-sensitive** — `"App"` will not match `"app"`.

**Logic operators:** `AND` (all conditions must match) · `OR` (any condition can match)

---

## Best Practices for Chunk Quality

### Check Chunk Quality After Processing

Review each chunk after creation:

| Issue | Symptom | Fix |
|-------|---------|-----|
| **Too short** | Lacks context; vague answers | Increase max chunk length or reduce delimiters |
| **Too long** | Includes irrelevant content; imprecise retrieval | Decrease max chunk length; add more delimiters |
| **Semantically incomplete** | Sentence/paragraph cut mid-thought | Adjust delimiter to respect sentence/paragraph boundaries |

### Use Child Chunks as Retrieval Hooks

For Parent-child mode, rewrite child chunks as semantic anchors:

**Original child chunk:**
> "The LED indicator light blinks red when..."

**Rewritten as a retrieval hook:**
> "blinking red light, power error, connection failure, LED status indicator"

### Use Summaries to Bridge Query-Content Gaps

Add summaries when:
- Users ask in different language/terminology than the document uses
- Content is implicit, highly technical, or non-textual (code, tables, logs)
- Multiple related chunks should be retrieved together (use identical summaries)

### Recall Testing

Use the **Recall Test** feature in your knowledge base to validate retrieval with real user queries before connecting to an application.

---

## Knowledge Base API

Manage knowledge bases programmatically via the Knowledge Base API.

> A single Knowledge Base API token has authority over **all visible knowledge bases** in the account. Treat it accordingly.

### Core API Operations

| Category | Operations |
|----------|-----------|
| **Knowledge Bases** | Create, list (paginated), delete |
| **Documents** | Create (text or file), update, delete, list, check embedding status |
| **Chunks (Segments)** | Add, retrieve, update, delete; search knowledge base |
| **Metadata** | Add/update/delete fields; enable/disable built-in fields; assign values to documents |

**Common error codes:**
- `no_file_uploaded`
- `file_too_large`
- `unsupported_file_type`

---

## Rate Limits

| Plan | Requests per Minute |
|------|---------------------|
| Sandbox | 10 |
| Professional | 100 |
| Team | 1,000 |

Requests exceeding the limit are temporarily blocked for one minute.

**Actions that count toward the rate limit:**
- Dataset creation, deletion, settings updates
- Document uploads, deletions, modifications
- Chunk operations
- Hit tests
- Knowledge queries from applications or workflows

> Multi-path recall operations count as a **single** request.
