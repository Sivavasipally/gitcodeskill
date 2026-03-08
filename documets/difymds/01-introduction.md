# Introduction to Dify

## What is Dify?

Dify is an **open-source platform for building agentic workflows**. It lets you define processes visually, connect your existing tools and data sources, and deploy AI applications that solve real problems.

> The name **Dify** comes from **D**o **I**t **F**or **Y**ou.

---

## Why Dify?

| Benefit | Description |
|---------|-------------|
| **Visual Workflow Builder** | Drag-and-drop canvas to design AI pipelines without writing backend code |
| **Multi-modal Support** | Handle text, images, documents, and audio in a single workflow |
| **Production Ready** | Deploy as web apps, APIs, MCP servers, or embedded widgets instantly |
| **Open Source** | Self-host on your own infrastructure or use Dify Cloud |
| **Extensible** | Connect to any LLM provider, knowledge base, or external API |

---

## Quick Navigation

| Resource | Description |
|----------|-------------|
| Quick Start | Start shipping powerful apps in minutes |
| Concepts | Core Dify building blocks explained |
| Self Host | Deploy Dify on personal infrastructure |
| Forum | Community discussion at forum.dify.ai |
| Changelog | Release updates on GitHub |
| Tutorials | Walkthroughs including customer-service-bot examples |

---

## Quick Start: Multi-Platform Content Generator

This walkthrough demonstrates creating a workflow from scratch. The completed application accepts text, documents, and images, then transforms them into platform-specific social media posts.

### Step 1 — Create the Workflow

In Dify Studio, create a blank workflow named **"Multi-platform content generator"**.

### Step 2 — Add and Connect Nodes

| Node | Role |
|------|------|
| **User Input** | Collects draft text, files, tone preference, target platforms, and language |
| **Parameter Extractor** | Converts free-form platform text (e.g. "x and linkedIn") into `["Twitter", "LinkedIn"]` |
| **IF/ELSE** | Validates extraction; routes invalid inputs to an early-exit Output node |
| **List Operator (×2)** | Separates uploaded files by type — one for images, one for documents |
| **Doc Extractor** | Converts documents into plain text the LLM can process |
| **LLM — Integrate Info** | Combines all reference materials into a comprehensive summary (vision-enabled) |
| **Iteration** | Loops through each target platform, generating tailored content in parallel (max parallelism: 10) |
| **Template** | Formats raw iteration output into readable Markdown using Jinja2 |
| **Output** | Returns the final result to the user |

### Step 3 — Test and Publish

1. Use **Test Run** to verify the workflow
2. Review cached variables in the Variable Inspector if adjustments are needed
3. Click **Publish** to make the workflow live and shareable

---

## Dify Platform Overview

```
Dify
├── Studio          — Visual workflow builder
├── Knowledge       — Upload and manage knowledge bases (RAG)
├── Tools           — Built-in, custom, MCP, and workflow tools
└── Settings
    ├── Model Providers
    ├── Members
    ├── Plugins
    └── Billing
```

---

## Deployment Options

| Option | Description |
|--------|-------------|
| **Dify Cloud** | Managed SaaS; workspace created on first login |
| **Community Edition** | Self-hosted via Docker; one workspace created at install |
| **Enterprise** | Advanced access control, SSO, and dedicated support |

Self-hosted Docker setup:
```bash
git clone https://github.com/langgenius/dify.git
cd dify/docker
cp .env.example .env
docker compose up -d
```

---

## Next Steps

- [02 — Core Concepts](./02-core-concepts.md) — Understand app types, variables, and the DSL
- [03 — Workflow Nodes](./03-workflow-nodes.md) — Deep dive into every node type
- [04 — Building Applications](./04-building-applications.md) — Shortcuts, orchestration, and error handling
