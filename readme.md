# 🛡️ LogRAG Sentinel

**LogRAG Sentinel** is an autonomous microservice diagnostic engine. It ingests raw, distributed system logs, generates local dense vector embeddings, and utilizes a Retrieval-Augmented Generation (RAG) pipeline to provide engineers with instant, grounded root-cause analysis of server failures.

Built as a proof-of-concept for enterprise AI observability, this system specifically addresses the "black box" problem of AI by enforcing strict context-grounding and PII-masking guardrails.

## ✨ Key Features
* **Regex-Based Ingestion & Chunking:** Parses un-sanitized, multi-line microservice logs (tested on the OpenStack Loghub dataset) using sliding-window chunking to preserve stack-trace context.
* **Zero-Latency Local Embeddings:** Utilizes `FastEmbed` (`BAAI/bge-small-en-v1.5`) via the ONNX runtime to generate 384-dimensional vectors locally, avoiding cloud API latency and costs.
* **In-Memory Vector Indexing:** Implements `FAISS` ($L_2$ distance) for sub-millisecond similarity search across log chunks.
* **Responsible AI Guardrails:** Automatically intercepts and redacts PII (IP addresses and Emails) before context is passed to the LLM.
* **Grounded UI/UX:** React dashboard that displays the AI's diagnostic summary alongside the raw, retrieved log snippets for engineering auditability and trust.

## 🏗️ System Architecture

```text
[ Unstructured .log Files ] 
       │
       ▼
[ FastAPI Ingestor ] ──( Regex Parsing & Sliding Window Chunking )──► [ Text Chunks ]
                                                                             │
[ React Dashboard ] ◄──( REST API )── [ FastEmbed ONNX Runtime ] ◄───────────┘
       │                                        │
       │ Query                                  ▼
       ▼                             [ FAISS In-Memory Vector DB ]
[ RAG Prompt Pipeline ] ◄──( Context )──────────┘
       │
       ▼
[ PII Guardrail Masking ]
       │
       ▼
[ Groq LLM (Llama-3.3-70b-versatile) ]
