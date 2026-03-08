# Tutorials

Step-by-step guides for building real applications with Dify. Each tutorial introduces new concepts and builds practical skills.

---

## Tutorial 1: Simple Chatbot with Structured Output

**Difficulty:** Beginner | **Time:** ~15 minutes
**Concepts covered:** Workflow basics, LLM node, Code node, Answer node, Structured output, Variable referencing

### What You'll Build

A geography chatbot that:
1. Accepts a user question about any country
2. Uses an LLM to produce a structured JSON answer (country name, rephrased question, answer)
3. Runs Python code to retrieve a pre-defined fun fact about that country
4. Returns a formatted combined response

### Step 1 — Create the Workflow

In Dify Studio:
1. Click **+ Create App**
2. Select **Chatflow** → **Create from Blank**
3. Name it: `Geography Chatbot`

### Step 2 — Configure the LLM Node

Connect an **LLM node** to the User Input node.

**System prompt:**
```
You are a geography assistant. When the user asks about a country, extract:
1. The country name
2. A cleaner rephrasing of the question
3. A factual answer

Always respond in valid JSON with keys: country, question, answer.
```

**Enable Structured Output:**
- Click **Output Format → JSON Schema**
- Define the schema:
```json
{
  "type": "object",
  "properties": {
    "country": { "type": "string" },
    "question": { "type": "string" },
    "answer": { "type": "string" }
  },
  "required": ["country", "question", "answer"]
}
```

### Step 3 — Configure the Code Node

Connect a **Code node** to the LLM node.

**Input variable:** `country` (from `llm_1.country`)

**Python code:**
```python
def main(country: str) -> dict:
    fun_facts = {
        "France": "France has the most visited tourist attraction in the world — the Eiffel Tower.",
        "Japan": "Japan has over 6,800 islands, though most are uninhabited.",
        "Brazil": "Brazil is the only country in South America where Portuguese is the official language.",
        "Australia": "Australia is the only continent that is also a single country.",
        "Egypt": "Egypt is home to the only remaining ancient wonder of the world — the Great Pyramid of Giza."
    }
    fact = fun_facts.get(country, "This is a fascinating country with a rich history!")
    return { "fun_fact": fact }
```

### Step 4 — Configure the Answer Node

Connect an **Answer node** to the Code node.

**Content:**
```
{{ llm_1.answer }}

**Fun fact about {{ llm_1.country }}:** {{ code_1.fun_fact }}
```

### Step 5 — Test

Click **Test Run** (or `Alt+R`/`Option+R`) and ask:
- "What is the capital of France?"
- "How big is Australia?"

Verify the response includes both the LLM answer and the fun fact.

### Step 6 — Publish

Click **Publish** → copy the web app URL → share with users.

---

## Tutorial 2: Twitter / X Account Analyzer

**Difficulty:** Intermediate | **Time:** ~30 minutes
**Concepts covered:** Chatflow, Code node for URL construction, HTTP Request node, Environment variables, LLM analysis

### What You'll Build

A chatflow that:
1. Accepts a Twitter/X username
2. Uses Crawlbase to scrape the profile page (bypasses Twitter's API restrictions)
3. Passes the scraped content to an LLM for analysis

### Prerequisites

- Crawlbase account with API key
- Dify deployment (cloud or local Docker)
- Configured LLM provider

**Local Docker setup (if needed):**
```bash
git clone https://github.com/langgenius/dify.git
cd dify/docker
cp .env.example .env
docker compose up -d
```

### Step 1 — Create a Chatflow

In Studio: **+ Create App → Chatflow → Create from Blank** → name it `Twitter Analyzer`

### Step 2 — Store the API Key Securely

In the workflow canvas:
1. Click **Environment Variables** (top toolbar)
2. Add variable: `CRAWLBASE_API_KEY` = `your-key-here`

> Never paste API keys directly into node inputs — use environment variables.

### Step 3 — Code Node: Build the Profile URL

**Input:** `username` (from `userinput.query`)

**Python code:**
```python
def main(username: str) -> dict:
    # Clean the username (remove @ if present)
    clean = username.strip().lstrip('@')
    url = f"https://twitter.com/{clean}"
    return { "profile_url": url }
```

### Step 4 — HTTP Request Node: Scrape with Crawlbase

**Method:** GET

**URL:**
```
https://api.crawlbase.com/?token={{ env.CRAWLBASE_API_KEY }}&url={{ code_1.profile_url }}&scraper=twitter-profile
```

**No authentication** (API key is in the URL parameter).

**Output:** Use `body` (the scraped HTML/JSON content).

### Step 5 — LLM Node: Analyze the Profile

**System prompt:**
```
You are a social media analyst. Analyze the following Twitter/X profile data and provide:
1. A summary of the account's main topics and interests
2. The typical posting style and tone
3. Estimated audience and engagement level
4. Three notable observations about this account

Be concise, insightful, and professional.
```

**User prompt:**
```
Profile data:
{{ http_1.body }}

Analyze this Twitter/X account.
```

### Step 6 — Answer Node

```
## Twitter/X Profile Analysis

{{ llm_1.text }}
```

### Step 7 — Test and Publish

1. Open **Preview** mode
2. Enter a public Twitter username (e.g., `elonmusk`)
3. Verify the analysis is generated
4. Click **Publish**

---

## Tutorial 3: Customer Service Bot with Knowledge Base

**Difficulty:** Intermediate | **Time:** ~45 minutes
**Concepts covered:** Chatflow, Knowledge base creation, Question Classifier, Knowledge Retrieval, Multi-path routing, Direct Reply

### What You'll Build

A customer service chatbot that:
1. Classifies incoming questions into categories
2. Routes product questions to a knowledge base for accurate answers
3. Routes irrelevant questions to a polite direct response
4. Cites knowledge sources in its answers

### Step 1 — Create the Knowledge Base

1. Navigate to **Knowledge → Create Knowledge**
2. Upload your product documentation (PDF, DOCX, or HTML)
3. **Chunk settings:** General Mode, `\n\n` delimiter, 500 char max, 50 char overlap
4. **Index method:** High Quality + Hybrid Search
5. Wait for processing to complete
6. Use **Recall Test** to verify retrieval with sample queries

> **Tip:** Review chunks after processing. Disable any that are irrelevant or poorly structured.

### Step 2 — Create a Chatflow

In Studio: **+ Create App → Chatflow → Create from Blank** → name it `Customer Service Bot`

### Step 3 — Question Classifier Node

**Input variable:** `sys.query`

**Categories:**

| Category | Description |
|----------|-------------|
| Product questions | Questions about features, pricing, specifications, how to use |
| Technical support | Bug reports, error messages, troubleshooting |
| Account/billing | Account management, subscription, payment issues |
| Other | General questions, small talk, anything else |

**Model:** Use a capable model (GPT-4o, Claude 3.5 Sonnet)

### Step 4 — Route Each Category

**For Product questions:**

1. Add a **Knowledge Retrieval node**
   - Query source: `sys.query`
   - Knowledge base: select your product docs KB
   - Top K: 3, Score Threshold: 0.5

2. Add an **LLM node**
   - System prompt:
     ```
     You are a helpful product expert. Use the provided knowledge base content to answer
     the customer's question accurately and concisely. If the answer isn't in the context,
     say so honestly rather than guessing.
     ```
   - Context: `knowledge_retrieval_1.result`
   - User prompt: `{{ sys.query }}`

3. Add an **Answer node**:
   ```
   {{ llm_1.text }}
   ```
   Enable **Citation and Attribution** in Features.

**For Technical support:**

1. Add a **Knowledge Retrieval node** (search troubleshooting docs)
2. Add an **LLM node** (technical tone system prompt)
3. Add an **Answer node**

**For Account/billing:**

Add a **Direct Reply Answer node**:
```
For account and billing questions, please contact our support team directly:

📧 support@yourcompany.com
📞 1-800-SUPPORT (Mon–Fri, 9AM–6PM EST)

We aim to respond within one business day.
```

**For Other:**

Add a **Direct Reply Answer node**:
```
I'm specialized in product questions and technical support.
For other inquiries, please visit our [Help Center](https://help.yourcompany.com)
or contact our team at support@yourcompany.com.
```

### Step 5 — Enable Features

1. Click **Features** (top-right)
2. Enable:
   - **Citation and Attribution** — users see source references
   - **Follow-up Suggestions** — auto-generates 3 next questions
   - **Conversation Opener** — AI introduces itself

### Step 6 — Debug and Publish

1. Use **Debug and Preview** to test each category
2. Check that citations appear for knowledge-based answers
3. Verify direct replies work for non-product questions
4. Click **Publish**
5. Embed on your website using the chat bubble widget

---

## Tutorial 4: AI Image Generation App

**Difficulty:** Beginner | **Time:** ~20 minutes
**Concepts covered:** Agent app type, Tool authorization, Prompt engineering, Agent instructions

### What You'll Build

An AI image generation assistant that:
1. Accepts natural language descriptions from users
2. Uses the Stability AI tool to generate images
3. Applies optional style preferences automatically

### Prerequisites

- Stability AI API key (register at stability.ai)
- LLM provider with free credits (e.g., Groq's Llama models)

### Step 1 — Authorize the Stability Tool

1. In Dify: **Tools → Stability**
2. Click **Authorize**
3. Paste your Stability API key
4. Click **Save**

### Step 2 — Configure a Free LLM (Optional)

Using Groq for free Llama access:
1. Register at console.groq.com and generate an API key
2. In Dify: **Settings → Model Providers → Groq**
3. Add your API key
4. Use `llama-3.1-70b-versatile` in your agent

### Step 3 — Create an Agent App

1. Studio → **+ Create App → Agent → Create from Blank**
2. Name it: `AI Image Generator`

### Step 4 — Configure the Agent

**Model:** Select your preferred LLM (Groq Llama, GPT-4o, Claude, etc.)

**Tools:** Click **Add Tool → Stability → stability_text2image**

**Basic Instructions:**
```
You are an AI image generation assistant. When the user describes an image they want,
use the stability_text2image tool to create it. Generate exactly what they describe.
```

**Style-enhanced Instructions:**
```
You are an AI image generation assistant specializing in anime-style artwork.
When the user describes an image they want, use the stability_text2image tool to create it.
Always apply an anime artistic style to every image unless the user specifically requests
a different style.
```

### Step 5 — Add Content Moderation (Optional)

Add constraints to prevent inappropriate requests:
```
Do not generate images that are:
- Violent, disturbing, or graphic
- Sexually explicit
- Related to real, identifiable people without their consent
- Promoting illegal activities

If the user requests such content, politely explain you cannot generate it
and offer to help with an appropriate alternative.
```

### Step 6 — Test and Publish

1. Click **Test** in the preview
2. Try prompts like:
   - "A mountain landscape at sunset with a lake reflection"
   - "A futuristic city skyline at night"
3. Verify images are generated
4. Click **Publish → Run App** to get the shareable web app URL

### Advanced: Auto-Generate Instructions

Click **Generate** above the Instructions field, describe your agent's purpose, and let the AI suggest a system prompt. Review and refine it to match your needs.

---

## Tutorial 5: Article Reader with Q&A Generation

**Difficulty:** Intermediate | **Time:** ~30 minutes
**Concepts covered:** Chatflow, File upload, Doc Extractor, Iteration node, List Operator, Multi-LLM pipeline

### What You'll Build

An article reading assistant that:
1. Accepts one or more uploaded documents
2. Extracts the text from each document
3. Analyzes the article structure
4. Generates insightful questions to help users engage with the content

### Step 1 — Create a Chatflow

Studio → **+ Create App → Chatflow → Create from Blank** → name it `Article Reader`

### Step 2 — Configure the Start Node (User Input)

In the User Input node:
1. Add a custom **File List** variable named `articles`
2. Set accepted file types: PDF, DOCX, TXT, Markdown
3. This creates a variable `userinput.articles` of type `array[file]`

**Enable File Upload in Features:**
1. Click **Features → File Upload → Enable**
2. This shows the paperclip icon in the chat interface

### Step 3 — List Operator Node (Filter Files)

Add a **List Operator** node:
- **Input:** `userinput.articles`
- **Filter:** Keep files where type = document (exclude images)
- **Sort:** By filename (ascending)

This ensures only document files proceed to processing.

### Step 4 — Iteration Node

Add an **Iteration** node:
- **Input array:** `list_operator_1.result`
- **Error handling:** Continue on Error (so one bad file doesn't stop all others)

Inside the Iteration, add:

**4a. Doc Extractor node:**
- Input: `items` (current iteration element)
- Output: text string of the extracted document content

**4b. LLM Node — Structure Analysis:**
- Input: `doc_extractor_1.text`
- System prompt:
```
You are a reading assistant. Analyze the structure of the following article and identify:
1. The main topic and thesis
2. Key sections or arguments (list them)
3. The intended audience
4. The overall conclusion

Be concise and organized.
```
- Output: structured analysis

**4c. LLM Node — Question Generation:**
- Input: `llm_structure.text`
- System prompt:
```
Based on the article structure analysis provided, generate 5 thought-provoking questions
that will help a reader engage more deeply with this content.

Include:
- 2 comprehension questions (understanding the content)
- 2 critical thinking questions (evaluating the arguments)
- 1 application question (applying ideas to real life)

Format each question on a new line, numbered 1–5.
```

### Step 5 — Template Node (Format Output)

After the Iteration node, add a **Template node** to combine results:

```jinja
# Article Analysis and Reading Questions

{% for i in range(articles | length) %}
---

## Article {{ loop.index }}: {{ articles[i].name }}

### Structure Analysis
{{ analyses[i] }}

### Questions for Deeper Engagement
{{ questions[i] }}

{% endfor %}
```

Adjust variable names to match your actual Iteration output variable names.

### Step 6 — Answer Node

```
{{ template_1.output }}
```

### Step 7 — Test

1. In **Preview** mode, upload 1–2 sample articles (PDF or DOCX)
2. The assistant should analyze structure and generate questions for each
3. Verify the iteration processes each file independently

### Step 8 — Publish and Share

Click **Publish**. The chat interface will show a paperclip icon for file uploads.

---

## Tips Across All Tutorials

### Variable Referencing Quick Reference

| Where | Syntax |
|-------|--------|
| In LLM prompts | `{{ node_id.output_variable }}` |
| In Template nodes | `{{ variable }}` with full Jinja2 support |
| In Code node inputs | Declared in the input variable list, accessed by name |
| In If/Else conditions | Via the variable selector dropdown |

### Common Mistakes to Avoid

| Mistake | Fix |
|---------|-----|
| LLM returns unstructured text when you need data | Enable Structured Output with a JSON Schema |
| Iteration fails on the whole array when one item errors | Set error handling to "Continue on Error" |
| Context field receives an array instead of a string | Use a Template node to convert the Knowledge Retrieval result to a string |
| API key exposed in node configuration | Store in Environment Variables; reference as `{{ env.VAR_NAME }}` |
| File variable not parsed | Always use a Doc Extractor node before passing files to an LLM |

### Performance Tips

| Tip | When to Apply |
|-----|--------------|
| Enable Iteration parallel mode | When items are independent and order doesn't matter |
| Use cheaper models for classification | Question Classifier, Parameter Extractor don't need GPT-4 |
| Set Score Threshold in Knowledge Retrieval | Prevents low-quality chunks from polluting LLM context |
| Cache frequent patterns with Annotation Reply | Repeated questions that always need the same answer |
| Use the Variable Inspector for debugging | Instead of re-running the full workflow for every tweak |
