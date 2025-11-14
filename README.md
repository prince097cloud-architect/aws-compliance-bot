# 🚀 Intelligent AWS Multi‑Agent System

Building a self-healing, DRY_RUN‑enabled, intelligent AWS audit engine powered by **LangGraph**, **OpenAI**, **LangChain**, and **FastAPI**.

This repository contains the full implementation of my multi-agent cloud audit system, capable of:

* Understanding natural-language audit requests
* Running secure, modular MCP‑based tasks
* Performing cross-service AWS compliance checks
* Acting safely with DRY_RUN support
* Providing real-time explanations, traces, and audit logs

---

## 📘 **Architecture Overview**

Below are the visuals that represent the overall system. (Add your diagrams in the `diagrams/` folder later.)

### **1. High-Level Block Diagram**

```
User → FastAPI Router → LangGraph Orchestrator → Multi‑Agent System
       |                                            ↓
       |                                   AWS Compliance Tools
       |                                            ↓
       └────────────→ DRY_RUN / EXECUTE Engine ←────┘
```

### **2. Multi-Agent System Workflow**

```
[Master Agent]
      ↓
[Router Agent] —→ (Decides which skill/tool to invoke)
      ↓
[Service Agents: S3, KMS, EC2, IAM ...]
      ↓
[Audit Engine + Summary Generator]
```

---

## 🧠 **Core Components**

### **✔ LangGraph Orchestration**

Coordinates multiple agents with deterministic routing.

### **✔ FastAPI Backend**

Provides REST endpoints for teams and automation workflows.

### **✔ MCP Servers**

Each AWS service has its own secure MCP server with DRY_RUN support.

### **✔ OpenAI + LangChain**

Natural language understanding, intent routing, structured outputs.

### **✔ Audit History + Governance**

All tasks logged for compliance and traceability.

---

## 📦 **Folder Structure**

```
aws-multi-agent-system/
├── agents/
├── mcp_servers/
├── router/
├── fastapi_app/
├── utils/
├── diagrams/
└── README.md
```

---

## 📝 **Blog Posts & Publications**

### 🔗 **Medium**

**Building an Intelligent AWS Multi-Agent System Using LangGraph, OpenAI, LangChain, and FastAPI**
https://medium.com/@prince2025akash/building-an-intelligent-aws-multi-agent-system-using-langgraph-openai-langchain-and-fastapi-aed0bc6f1fcb

### 🔗 **Hashnode**

[https://aws-multi-agent-system.hashnode.dev/building-an-intelligent-aws-multi-agent-system-using-langgraph-openai-langchain-and-fastapi-a-real-time-self-healing-cloud-compliance-eng](https://aws-multi-agent-system.hashnode.dev/building-an-intelligent-aws-multi-agent-system-using-langgraph-openai-langchain-and-fastapi-a-real-time-self-healing-cloud-compliance-eng)

### 🔗 **LinkedIn**

[https://www.linkedin.com/in/prince97/](https://www.linkedin.com/in/prince97/)

---

## 🧭 **How It Works (Short Summary)**

1. User sends natural-language request.
2. Router determines audit type (S3/KMS/EC2/etc.).
3. Appropriate MCP server runs checks.
4. DRY_RUN ensures safety.
5. System auto-heals violations.
6. Final audit summary returned.

---

## 🧪 **Running Locally**

```bash
git clone <repo-url>
cd aws-multi-agent-system
pip install -r requirements.txt
uvicorn fastapi_app.main:app --reload
```

---

## 🌱 **Upcoming Enhancements**

* Cost utilization + LLM token analysis
* Extended MCP server library
* RAG model for rules/policies
* LangSmith tracing + Prometheus metrics
* Multi-account deployment examples

---

## 🤝 **Contributions**

PRs are welcome! Feel free to open an issue for ideas, bugs, or improvements.

---

## ⭐ If you like this project

Please star ⭐ the repo — it helps a lot!

---
