"""
K8s AI Agent - ReAct Pattern with Groq
Intelligent Kubernetes troubleshooting using LLMs and kubectl tools
"""

# ============================================================================
# SSL/TLS WORKAROUNDS FOR DOCKER DESKTOP MAC
# ============================================================================
# Docker Desktop for Mac has issues with SSL certificate verification when
# accessing external APIs (like Groq) from containers. These workarounds
# disable SSL verification to allow the agent to function properly.
#
# WARNING: Only use in development/demo environments with trusted APIs.
# For production, configure proper SSL certificates.
# ============================================================================

# MUST be set before any imports - configures Python's SSL behavior
import os
os.environ['PYTHONHTTPSVERIFY'] = '0'  # Disable SSL verification globally
os.environ['CURL_CA_BUNDLE'] = ''       # Prevent curl from using CA bundle
os.environ['REQUESTS_CA_BUNDLE'] = ''   # Prevent requests library from using CA bundle

import ssl
import warnings
import urllib3

# Disable SSL verification warnings to clean up logs
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings('ignore', message='Unverified HTTPS request')

# Override Python's default SSL context to not verify certificates
ssl._create_default_https_context = ssl._create_unverified_context

# ============================================================================
# HTTPX MONKEYPATCH - CRITICAL FOR GROQ API
# ============================================================================
# The Groq Python SDK uses httpx (not requests) for HTTP connections.
# We must monkeypatch httpx.Client to disable SSL verification.
# This is done by intercepting the __init__ method and forcing verify=False.
# ============================================================================
import httpx
_original_client_init = httpx.Client.__init__

def _patched_client_init(self, *args, **kwargs):
    """Patched httpx.Client.__init__ that forces SSL verification off"""
    kwargs['verify'] = False  # Disable SSL verification
    return _original_client_init(self, *args, **kwargs)

httpx.Client.__init__ = _patched_client_init  # Apply the monkey patch

# ============================================================================
# NOW SAFE TO IMPORT OTHER MODULES
# ============================================================================
httpx.Client.__init__ = _patched_client_init

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain.agents import create_react_agent, AgentExecutor
from langchain.prompts import PromptTemplate  
from langchain.tools import tool
from langchain_groq import ChatGroq
import subprocess
import json as json_module
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="K8s AI Agent", version="1.0.0")

# Enable CORS for UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== MODELS ====================

class ChatRequest(BaseModel):
    message: str
    namespace: str = "default"

class ChatResponse(BaseModel):
    response: str
    tools_used: list[str] = []
    reasoning_steps: list[dict] = []

# ==================== KUBECTL TOOLS ====================

def parse_tool_input(input_data):
    """Parse tool input - handle both dict and JSON string"""
    if isinstance(input_data, dict):
        return input_data
    if isinstance(input_data, str):
        try:
            return json_module.loads(input_data)
        except:
            return {"pod_name": input_data}
    return {}

@tool
def list_all_pods(input_data: str) -> str:
    """List all pods in namespace. Input: {\"namespace\": \"default\"}"""
    try:
        args = parse_tool_input(input_data)
        namespace = args.get("namespace", "default")
        
        result = subprocess.run(
            ["kubectl", "get", "pods", "-n", namespace, "-o", "json"],
            capture_output=True, text=True, timeout=10
        )
        
        if result.returncode != 0:
            return f"Error: {result.stderr}"
        
        pods_data = json_module.loads(result.stdout)
        pods = pods_data.get("items", [])
        
        if not pods:
            return f"No pods found in namespace '{namespace}'"
        
        output = f"Pods in namespace '{namespace}':\n"
        for pod in pods:
            name = pod["metadata"]["name"]
            phase = pod["status"].get("phase", "Unknown")
            
            # Check container statuses
            issues = []
            for cs in pod["status"].get("containerStatuses", []):
                state = cs.get("state", {})
                if "waiting" in state:
                    reason = state["waiting"].get("reason")
                    issues.append(f"{reason}")
                elif "terminated" in state:
                    reason = state["terminated"].get("reason")
                    issues.append(f"Terminated: {reason}")
            
            status = f" - Issues: {', '.join(issues)}" if issues else " - Healthy"
            output += f"  • {name}: {phase}{status}\n"
        
        return output
    except Exception as e:
        return f"Error: {str(e)}"

@tool
def get_pod_status(input_data: str) -> str:
    """Get pod status. Input: {\"pod_name\": \"name\", \"namespace\": \"default\"}"""
    try:
        args = parse_tool_input(input_data)
        pod_name = args.get("pod_name", args.get("input_data", ""))
        namespace = args.get("namespace", "default")
        
        result = subprocess.run(
            ["kubectl", "get", "pod", pod_name, "-n", namespace, "-o", "json"],
            capture_output=True, text=True, timeout=10
        )
        
        if result.returncode != 0:
            return f"Error: {result.stderr}"
        
        pod_data = json_module.loads(result.stdout)
        status = pod_data.get("status", {})
        phase = status.get("phase", "Unknown")
        
        output = f"Pod: {pod_name}\nPhase: {phase}\nRestarts: "
        
        for cs in status.get("containerStatuses", []):
            name = cs.get("name")
            restarts = cs.get("restartCount", 0)
            state = cs.get("state", {})
            
            output += f"{restarts} "
            
            if "waiting" in state:
                reason = state["waiting"].get("reason")
                message = state["waiting"].get("message", "")
                output += f"\nContainer '{name}': Waiting - {reason}\n  {message[:200]}"
            elif "terminated" in state:
                reason = state["terminated"].get("reason")
                exit_code = state["terminated"].get("exitCode")
                output += f"\nContainer '{name}': Terminated - {reason} (exit code: {exit_code})"
            elif "running" in state:
                output += f"\nContainer '{name}': Running"
        
        return output
    except Exception as e:
        return f"Error: {str(e)}"

@tool  
def get_pod_logs(input_data: str) -> str:
    """Get pod logs. Input: {\"pod_name\": \"name\", \"namespace\": \"default\"}"""
    try:
        args = parse_tool_input(input_data)
        pod_name = args.get("pod_name", args.get("input_data", ""))
        namespace = args.get("namespace", "default")
        
        # Try current logs first
        result = subprocess.run(
            ["kubectl", "logs", pod_name, "-n", namespace, "--tail=50"],
            capture_output=True, text=True, timeout=10
        )
        
        if result.returncode != 0:
            # Try previous container logs
            result = subprocess.run(
                ["kubectl", "logs", pod_name, "-n", namespace, "--previous", "--tail=50"],
                capture_output=True, text=True, timeout=10
            )
        
        if result.returncode != 0:
            return f"Error getting logs: {result.stderr}"
        
        logs = result.stdout[:2000]
        return f"Logs for {pod_name}:\n{logs}" if logs else "No logs available"
    except Exception as e:
        return f"Error: {str(e)}"

@tool
def describe_pod(input_data: str) -> str:
    """Get pod events and details. Input: {\"pod_name\": \"name\", \"namespace\": \"default\"}"""
    try:
        args = parse_tool_input(input_data)
        pod_name = args.get("pod_name", args.get("input_data", ""))
        namespace = args.get("namespace", "default")
        
        result = subprocess.run(
            ["kubectl", "describe", "pod", pod_name, "-n", namespace],
            capture_output=True, text=True, timeout=10
        )
        
        if result.returncode != 0:
            return f"Error: {result.stderr}"
        
        output = result.stdout
        if "Events:" in output:
            events = output.split("Events:")[1][:1500]
            return f"Events for {pod_name}:{events}"
        return "No events found"
    except Exception as e:
        return f"Error: {str(e)}"

tools = [list_all_pods, get_pod_status, get_pod_logs, describe_pod]

# ==================== AGENT SETUP ====================

REACT_PROMPT = """Answer the following questions as best you can. You have access to the following tools:

{tools}

Use the following format:

Question: the input question
Thought: think about what to do
Action: the action to take, one of [{tool_names}]
Action Input: {{"pod_name": "exact-name", "namespace": "default"}}
Observation: the result
... (repeat Thought/Action/Observation as needed)
Thought: I now know the final answer
Final Answer: clear diagnosis with root cause and fix steps

IMPORTANT: 
- Action Input must be valid JSON with double quotes!
- If user asks about "cluster" or "all pods", use list_all_pods first
- Be concise and actionable in Final Answer

Begin!

Question: {input}
Thought:{agent_scratchpad}"""

# Initialize LLM and agent
def create_agent():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable not set")
    
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0.0,
        api_key=api_key
    )
    
    prompt = PromptTemplate.from_template(REACT_PROMPT)
    agent = create_react_agent(llm=llm, tools=tools, prompt=prompt)
    
    return AgentExecutor(
        agent=agent,
        tools=tools,
        max_iterations=10,
        handle_parsing_errors=True,
        verbose=True,
        return_intermediate_steps=True
    )

# Global agent instance
agent_executor = None

# ==================== API ENDPOINTS ====================

@app.on_event("startup")
async def startup_event():
    global agent_executor
    try:
        agent_executor = create_agent()
        logger.info("✅ Agent initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize agent: {e}")
        raise

@app.get("/")
def root():
    return {
        "name": "K8s AI Agent",
        "version": "1.0.0",
        "model": "llama-3.3-70b (Groq)",
        "pattern": "ReAct",
        "tools": [t.name for t in tools]
    }

@app.get("/health")
def health():
    return {"status": "healthy", "agent_ready": agent_executor is not None}

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """Main chat endpoint - handles natural language queries"""
    
    if not agent_executor:
        raise HTTPException(status_code=500, detail="Agent not initialized")
    
    logger.info(f"Chat request: {request.message}")
    
    try:
        result = agent_executor.invoke({
            "input": f"{request.message} (namespace: {request.namespace})"
        })
        
        # Extract tools used and reasoning
        tools_used = []
        reasoning_steps = []
        
        for step in result.get("intermediate_steps", []):
            action, observation = step
            tools_used.append(action.tool)
            reasoning_steps.append({
                "thought": action.log.split("Action:")[0].replace("Thought:", "").strip() if "Thought:" in action.log else "",
                "action": action.tool,
                "observation": observation[:200] + "..." if len(observation) > 200 else observation
            })
        
        return ChatResponse(
            response=result.get("output", "No response generated"),
            tools_used=list(set(tools_used)),
            reasoning_steps=reasoning_steps
        )
        
    except Exception as e:
        logger.error(f"Error during chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    
    if not os.getenv("GROQ_API_KEY"):
        print("❌ Error: GROQ_API_KEY environment variable not set!")
        exit(1)
    
    print("=" * 60)
    print("🚀 K8s AI Agent - ReAct Pattern")
    print("=" * 60)
    print("📡 API: http://0.0.0.0:8000")
    print("📚 Docs: http://0.0.0.0:8000/docs")
    print("🤖 Model: Groq llama-3.3-70b")
    print("=" * 60)
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
