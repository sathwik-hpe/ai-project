# K8s AI Agent 🤖

Intelligent Kubernetes troubleshooting agent powered by LLMs and the ReAct pattern.

## 🎯 Overview

An AI-powered agent that automatically diagnoses and troubleshoots Kubernetes pod issues using natural language. Simply ask "What's wrong in my cluster?" and the agent will:

1. **Discover** - Scan your cluster for pods
2. **Investigate** - Use kubectl tools to gather information
3. **Reason** - Apply AI reasoning through the ReAct pattern
4. **Diagnose** - Provide root cause analysis and fixes

## ✨ Features

- 🧠 **ReAct Pattern** - Shows step-by-step AI reasoning
- 🛠️ **Kubectl Tools** - Integrates with your Kubernetes cluster
- 🌐 **Chat Interface** - Simple web UI for natural language queries
- 🚀 **One Command Setup** - `./start.sh` and you're running
- 🔑 **Free LLM** - Uses Groq (no local model setup needed)
- 🐳 **Fully Dockerized** - Portable and consistent environment

## 🏗️ Architecture

```
┌─────────────────┐
│   Chat UI       │ (Port 3000 - Simple HTML/JS)
│  User Input     │
└────────┬────────┘
         │ HTTP POST
         ▼
┌─────────────────┐
│  API Service    │ (Port 8000 - FastAPI)
│  ReAct Agent    │
└────────┬────────┘
         │
         ├─→ Groq LLM (llama-3.3-70b)
         │
         └─→ Kubectl Tools:
             • list_all_pods
             • get_pod_status  
             • get_pod_logs
             • describe_pod
         │
         ▼
┌─────────────────┐
│  Kubernetes     │
│   Cluster       │
└─────────────────┘
```

## � Quick Start

### Prerequisites

- Docker & Docker Compose
- kubectl configured
- Kubernetes cluster running (Docker Desktop, minikube, kind, etc.)
- Free Groq API key ([Get one here](https://console.groq.com))

### Installation

1. **Clone the repository**
   ```bash
   git clone git@github.com:sathwik-hpe/ai-project.git
   cd ai-project
   ```

2. **Run the start script**
   ```bash
   ./start.sh
   ```

   The script will:
   - Check prerequisites
   - Prompt for your Groq API key (not stored)
   - Build Docker images
   - Start all services
   - Open the chat UI in your browser

3. **Start chatting!**
   - UI: http://localhost:3000
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## 💬 Example Queries

Try these in the chat interface:

- "What's wrong in my cluster?"
- "List all pods"
- "Why is my pod crashing?"
- "Show me pods that are failing"
- "Diagnose pod xyz-123"

## 🧪 Testing (Optional)

Want to test with real issues? Deploy sample problematic pods:

```bash
./scripts/deploy-test-pods.sh
```

This creates:
- ✅ Healthy nginx pod
- ❌ CrashLoopBackOff pod (database connection failure)
- ❌ ImagePullBackOff pod (nonexistent image)

Then ask the agent: "What's wrong in my cluster?"

Clean up test pods:
```bash
kubectl delete deployment nginx-healthy crashloop-app imagepull-fail
```

## 🛠️ Development

### Project Structure

```
ai-project/
├── start.sh                 # Main startup script
├── docker-compose.yml       # Container orchestration
├── api/
│   ├── Dockerfile          # API container definition
│   ├── agent_service.py    # FastAPI + ReAct agent
│   └── requirements.txt    # Python dependencies
├── ui/
│   ├── Dockerfile          # UI container definition
│   └── index.html          # Chat interface
├── scripts/
│   └── deploy-test-pods.sh # Optional test deployments
└── README.md
```

### Manual Setup (Without Docker)

1. **API Service**
   ```bash
   cd api
   pip install -r requirements.txt
   export GROQ_API_KEY='your-key-here'
   python agent_service.py
   ```

2. **UI** 
   ```bash
   cd ui
   python3 -m http.server 3000
   ```

## 📋 Commands

```bash
# Start everything
./start.sh

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# Restart a service
docker-compose restart api
docker-compose restart ui

# Deploy test pods
./scripts/deploy-test-pods.sh
```

## 🧠 How It Works - ReAct Pattern

The agent uses the **ReAct (Reasoning + Acting)** pattern:

1. **Thought**: "I should list all pods to see what's happening"
2. **Action**: `list_all_pods`
3. **Observation**: "Found pod 'crashloop-app' in CrashLoopBackOff state"
4. **Thought**: "I need to check why it's crashing"
5. **Action**: `get_pod_logs`
6. **Observation**: "Error: Failed to connect to database"
7. **Thought**: "I now understand the issue"
8. **Final Answer**: "The pod is crashing because it cannot connect to the database..."

This reasoning is visible in the chat UI!

## 🔑 API Key Setup

The Groq API key is:
- **Prompted** at startup by `start.sh`
- **Not stored** in any files (security best practice)
- **Free tier** available at https://console.groq.com
- **Passed** as environment variable to Docker container

## 🤝 Contributing

This is a demo/POC project. Feel free to:
- Add more kubectl tools
- Improve the UI
- Add support for other LLM providers
- Extend to other cloud resources (AWS, Azure, etc.)

## 📝 License

MIT

## 🙏 Acknowledgments

- LangChain for the ReAct framework
- Groq for fast, free LLM inference
- Kubernetes community

---

Built with ❤️ for intelligent infrastructure troubleshooting
