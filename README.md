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
- 💻 **Cross-Platform** - Works on macOS, Linux, and Windows

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

## 🚀 Quick Start

### Prerequisites

- **Docker & Docker Compose** installed
- **kubectl** configured and working
- **Kubernetes cluster** running (Docker Desktop, minikube, kind, etc.)
- **Free Groq API key** ([Get one here](https://console.groq.com))

#### Platform-Specific Notes

**macOS (Docker Desktop)**:
- Uses Docker Desktop for Mac
- Automatically handles `host.docker.internal` mapping
- SSL certificate workarounds are built-in

**Linux**:
- If using Docker directly, the networking is more efficient
- If using minikube/kind, ensure kubectl context is set correctly
- May need to adjust `host.docker.internal` to `172.17.0.1` in docker-compose.yml

**Windows (Docker Desktop)**:
- Ensure WSL2 backend is enabled
- kubectl should be installed in WSL2
- Run `start.sh` from Git Bash or WSL2 terminal

### Installation

1. **Clone the repository**
   ```bash
   git clone git@github.com:sathwik-hpe/ai-project.git
   cd ai-project
   ```

2. **Ensure your Kubernetes cluster is running**
   ```bash
   # Test kubectl access
   kubectl get nodes
   
   # If using kind:
   kind create cluster --name k8s-agent-demo
   
   # If using minikube:
   minikube start
   
   # If using Docker Desktop:
   # Enable Kubernetes in Docker Desktop settings
   ```

3. **Run the start script**
   ```bash
   chmod +x start.sh
   ./start.sh
   ```

   The script will:
   - ✅ Check prerequisites (Docker, kubectl, K8s cluster)
   - 🔑 Prompt for your Groq API key (not stored)
   - 🏗️ Build Docker images
   - 🚀 Start all services
   - 🌐 Open the chat UI in your browser

4. **Start chatting!**
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
- "Check the logs for the crashloop-app pod"

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
│   ├── agent_service.py    # FastAPI + ReAct agent (with SSL workarounds)
│   └── requirements.txt    # Python dependencies
├── ui/
│   ├── Dockerfile          # UI container definition
│   └── index.html          # Chat interface
├── scripts/
│   └── deploy-test-pods.sh # Optional test deployments
├── k8s-tests/              # Sample K8s manifests
│   ├── nginx-healthy.yaml
│   ├── crashloop-app.yaml
│   └── imagepull-fail.yaml
└── README.md
```

### Manual Setup (Without Docker)

1. **API Service**
   ```bash
   cd api
   pip install -r requirements.txt
   export GROQ_API_KEY='your-key-here'
   export KUBECONFIG=~/.kube/config
   python agent_service.py
   ```

2. **UI** 
   ```bash
   cd ui
   python3 -m http.server 3000
   ```

3. **Open browser**
   - Navigate to http://localhost:3000

## 📋 Commands

```bash
# Start everything
./start.sh

# Stop services
docker-compose down

# View logs
docker-compose logs -f api
docker-compose logs -f ui

# Restart a service
docker-compose restart api
docker-compose restart ui

# Rebuild after code changes
docker-compose build api
docker-compose up -d

# Deploy test pods
./scripts/deploy-test-pods.sh

# Check container status
docker ps

# Shell into API container
docker exec -it k8s-ai-agent-api bash

# Test kubectl from container
docker exec k8s-ai-agent-api kubectl get nodes
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

## 🔧 Troubleshooting

### Docker Desktop for Mac Limitations

This project includes workarounds for Docker Desktop on macOS:

1. **Network Mode**: Uses `bridge` networking instead of `host` (which doesn't work on Mac)
2. **SSL Certificates**: Includes httpx monkeypatch to disable SSL verification for Groq API
3. **kubectl Access**: Modifies kubeconfig to use `host.docker.internal` and skip TLS verification

These workarounds are automatically applied and work seamlessly.

### Common Issues

**"Connection refused" when accessing the API:**
```bash
# Check if containers are running
docker ps

# Check API logs
docker-compose logs api

# Verify API is accessible
curl http://localhost:8000/health
```

**"kubectl: command not found" in container:**
```bash
# Rebuild the API container
docker-compose build api
docker-compose up -d
```

**"SSL certificate verification failed":**
- This is normal on Docker Desktop for Mac
- The agent_service.py includes automatic SSL workarounds
- If issues persist, check the API logs: `docker-compose logs api`

**"Cannot connect to Kubernetes cluster":**
```bash
# Verify kubectl works on host
kubectl get nodes

# Check if kubeconfig is mounted
docker exec k8s-ai-agent-api ls -la /root/.kube/config

# Test kubectl from container
docker exec k8s-ai-agent-api kubectl get nodes
```

**"Groq API key not working":**
- Ensure you're using a valid key from https://console.groq.com
- The key should start with `gsk_`
- Don't add quotes when pasting into the prompt

### Linux-Specific Configuration

For better performance on Linux, you can modify `docker-compose.yml`:

```yaml
services:
  api:
    # Change from bridge to host networking (Linux only)
    network_mode: "host"
    # Comment out the ports mapping (not needed with host mode)
    # ports:
    #   - "8000:8000"
```

Then update `ui/index.html`:
```javascript
// Line 35 - keep as localhost since browser makes the request
const API_URL = 'http://localhost:8000';
```

## 🔑 API Key Setup

The Groq API key is:
- **Prompted** at startup by `start.sh`
- **Not stored** in any files (security best practice)
- **Free tier** available at https://console.groq.com
- **Passed** as environment variable to Docker container
- **Never committed** to git (see .gitignore)

To get a Groq API key:
1. Visit https://console.groq.com
2. Sign up (free)
3. Go to API Keys section
4. Create a new key
5. Copy it (starts with `gsk_`)

## 🔒 Security Notes

- API keys are never stored in files
- `.gitignore` prevents accidental key commits
- SSL verification is disabled only for development/demo purposes
- For production, use proper SSL certificates
- kubectl TLS verification is skipped for local kind/minikube clusters

## 🤝 Contributing

This is a demo/POC project. Feel free to:
- Add more kubectl tools (get deployments, services, etc.)
- Improve the UI (add dark mode, export chat, etc.)
- Add support for other LLM providers (OpenAI, Anthropic, etc.)
- Extend to other cloud resources (AWS, Azure, GCP)
- Add unit tests and integration tests
- Improve error handling

## 📚 Technical Details

### SSL Workarounds (macOS Docker Desktop)

The `api/agent_service.py` includes several SSL workarounds:

1. **Environment Variables** - Set before imports
2. **SSL Context** - Override default HTTPS context
3. **httpx Monkeypatch** - Disable verification for Groq SDK
4. **urllib3 Warnings** - Suppress SSL warnings

These are necessary because Docker Desktop for Mac has certificate trust issues with external APIs.

### kubectl Configuration

The `api/Dockerfile` entrypoint script:

1. Copies `~/.kube/config` from host
2. Replaces `127.0.0.1` with `host.docker.internal`
3. Adds `insecure-skip-tls-verify: true` for local clusters
4. Sets `KUBECONFIG` environment variable

This allows kubectl to work from inside the container.

## 📝 License

MIT

## �� Acknowledgments

- LangChain for the ReAct framework
- Groq for fast, free LLM inference
- Kubernetes community
- FastAPI framework
- Docker Desktop team

---

Built with ❤️ for intelligent infrastructure troubleshooting

**Questions or issues?** Open a GitHub issue or PR!
