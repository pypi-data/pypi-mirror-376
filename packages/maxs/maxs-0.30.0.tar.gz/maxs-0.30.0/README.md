# maxs

**Build AI tools while talking to them**

Stop writing configs. Stop restarting servers. Just speak:

*"max, create a tool that monitors our Kubernetes cluster"*  
→ Tool created, tested, and running in 30 seconds

## 🚀 Try it now (2 minutes)

```bash
pipx install maxs && maxs
```

Then just speak:
- *"max, what time is it?"* → Instant response  
- *"max, create a weather tool"* → Tool appears in ./tools/
- *"max, use the weather tool for Tokyo"* → Working immediately

**No configuration. No API keys. No YAML files.**

## 💡 How it works

```
Voice Command → Hot Reload Tool Creation → Instant Usage
     ↓                    ↓                    ↓
"max, create X"    ./tools/X.py saved    Tool ready to use
```

**Three revolutionary features:**

🎙️ **Voice-First Development** - Build tools by talking  
🔥 **Instant Hot Reload** - Tools work immediately, no restart  
📡 **P2P Agent Network** - Agents communicate over encrypted mesh

## ⚡ Setup (choose one)

**Option 1: Local AI (recommended for privacy)**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull qwen3:4b
maxs
```

**Option 2: Cloud AI (recommended for power)**
```bash
# Anthropic Claude (best for development)
export ANTHROPIC_API_KEY="your-key"
MODEL_PROVIDER=anthropic maxs

# OpenAI GPT (good for general tasks)  
export OPENAI_API_KEY="your-key"
MODEL_PROVIDER=openai maxs

# Other: bedrock, github, litellm, llamaapi, mistral
```

## 🔥 Key Features

### 🎙️ **Voice-Powered Development**
```bash
maxs
> listen(action="start", trigger_keyword="max")

# Then just speak naturally:
"max, analyze the server logs"     → Creates monitoring tools
"max, deploy to staging"          → Runs deployment scripts  
"max, create a backup system"     → Builds automation instantly
```

### 🔄 **Instant Hot Reload**
Create tools while maxs is running:
```python
# Save this to ./tools/weather.py
from strands import tool

@tool
def weather(city: str) -> str:
    return f"Weather for {city}: 72°F, sunny"
```

Then immediately use it:
```bash
maxs "get weather for Tokyo"  # Tool works instantly!
```

### 📡 **P2P Agent Network**
Agents communicate over encrypted Bluetooth mesh:
```bash
# Agent Alice says:
"max, analyze the server performance"

# Agent Bob automatically responds:
"Performance analysis complete. CPU at 85%, recommend scaling."

# No internet required - direct agent-to-agent communication
```

### 🧠 **Intelligent Memory**
Remembers everything across sessions:
```bash
maxs "remember: we're using PostgreSQL for user data"
# Later...
maxs "create a user analytics tool"  # Uses PostgreSQL context
```

## 🛠️ Common Workflows

### Development & Automation
```bash
maxs "analyze this codebase and suggest improvements"
maxs "create deployment script for our Docker app"  
maxs "monitor system logs in the background"
maxs "format all Python files in this project"
```

### Data Analysis
```bash
maxs "connect to PostgreSQL and analyze user growth"
maxs "create charts from the sales CSV file"
maxs "query the API and generate a report"
```

### Voice Control (Hands-Free)
```bash
# Start voice mode first
maxs
> listen(action="start", trigger_keyword="max")

# Then just speak:
"max, what's the system status?"
"max, backup the database" 
"max, check for security updates"
```

## 🧰 Built-in Tools (50+)

<details>
<summary><strong>🎯 Essential Tools</strong> - Core functionality</summary>

| Tool | Purpose | Example |
|------|---------|---------|
| **shell** | Execute commands with real-time output | `check disk usage` |
| **editor** | File editing with syntax highlighting | `modify config files` |
| **python_repl** | Interactive Python execution | `run data analysis scripts` |
| **http_request** | Universal HTTP client | `call any REST API` |

</details>

<details>
<summary><strong>🎙️ Voice & Audio</strong> - Speech interaction</summary>

| Tool | Purpose | Example |
|------|---------|---------|
| **listen** | Speech-to-text with trigger keywords | `"max, what time is it?"` |
| **speak** | Text-to-speech (multiple engines) | `convert text to speech` |
| **realistic_speak** | Natural speech with emotions | `"[S1] hello! (laughs)"` |

</details>

<details>
<summary><strong>🧠 Memory & Data</strong> - Information systems</summary>

| Tool | Purpose | Example |
|------|---------|---------|
| **sqlite_memory** | Local memory with SQL queries | `search conversation history` |
| **memory** | Cloud knowledge base (Bedrock) | `semantic search across docs` |
| **sql_tool** | Universal database client | `connect to PostgreSQL/MySQL` |
| **data_viz_tool** | Create charts and visualizations | `generate sales reports` |

</details>

<details>
<summary><strong>🌐 Integrations</strong> - External services</summary>

| Tool | Purpose | Example |
|------|---------|---------|
| **use_github** | GitHub GraphQL API | `create issues and PRs` |
| **slack** | Team communication | `send messages and alerts` |
| **use_aws** | AWS service integration | `manage EC2, S3, Lambda` |
| **scraper** | Web scraping | `extract data from websites` |

</details>

<details>
<summary><strong>🚀 Advanced</strong> - Power user features</summary>

| Tool | Purpose | Example |
|------|---------|---------|
| **create_subagent** | Distributed AI via GitHub Actions | `delegate complex tasks` |
| **load_tool** | Dynamic tool loading | `install community tools` |
| **tasks** | Background processes | `run monitoring scripts` |
| **workflow** | Complex automation | `orchestrate deployments` |

</details>

## ⚙️ Configuration

### Quick Settings
```bash
# Use different AI providers
MODEL_PROVIDER=anthropic maxs
MODEL_PROVIDER=openai maxs
MODEL_PROVIDER=ollama maxs

# Enable specific tools only  
STRANDS_TOOLS="listen,speak,sql_tool,github" maxs

# Enable all tools
STRANDS_TOOLS="ALL" maxs
```

### Team Collaboration (Advanced)
```bash
# Enable team features
export STRANDS_TOOLS="event_bridge,sql_tool,memory"
export AWS_REGION=us-west-2
export MAXS_EVENT_TOPIC=my-team

# Shared knowledge base
export STRANDS_KNOWLEDGE_BASE_ID=team-kb-id
```

### External Services
```bash
# GitHub integration
export GITHUB_TOKEN=your-token

# Slack integration  
export SLACK_BOT_TOKEN=xoxb-your-token
export SLACK_APP_TOKEN=xapp-your-token

# AWS services
export AWS_REGION=us-west-2
```

## 💡 Advanced Examples

<details>
<summary><strong>🔥 Hot Reload Tool Creation</strong></summary>

Create and use tools instantly:

```python
# Save to ./tools/crypto.py
from strands import tool
import requests

@tool
def crypto(coin: str) -> str:
    """Get cryptocurrency price."""
    response = requests.get(f"https://api.coinbase.com/v2/exchange-rates?currency={coin}")
    price = response.json()["data"]["rates"]["USD"]
    return f"{coin}: ${price}"
```

Then immediately:
```bash
maxs "get crypto price for bitcoin"  # Tool works instantly!
```

</details>

<details>
<summary><strong>📊 Data Analysis Pipeline</strong></summary>

```bash
# Complete workflow in one command
maxs "connect to PostgreSQL, analyze user growth trends, create visualization, and save report to S3"

# Or step by step
maxs "connect to database 'users' on localhost"
maxs "create monthly signup chart for last 6 months" 
maxs "export chart as PNG and upload to S3 bucket"
```

</details>

<details>
<summary><strong>🤖 Multi-Agent Workflows</strong></summary>

```bash
# Deploy specialized agents
maxs "create subagent for security audit with GitHub Actions"
maxs "create subagent for performance testing with detailed metrics"

# P2P agent communication (no internet needed)
maxs "start bitchat and enable agent triggers"
# Agents automatically coordinate and share results
```

</details>

## 🛡️ Privacy & Security

**Local-first by design:**
- Core functionality works completely offline
- Conversation history stored locally in `/tmp/.maxs/`
- Custom tools saved in `./tools/` directory
- No external data transmission except to chosen AI provider

**Optional cloud features** (when enabled):
- AWS Bedrock for knowledge base (requires AWS credentials)
- Team collaboration via EventBridge (optional)
- External APIs only when explicitly used (GitHub, Slack, etc.)

## 🔧 Troubleshooting

<details>
<summary><strong>Common Issues</strong></summary>

**AI Provider Problems:**
```bash
# Try local model as fallback
ollama serve && ollama pull qwen3:4b
MODEL_PROVIDER=ollama maxs
```

**Voice Recognition Issues:**
```bash
maxs
> listen(action="list_devices")  # Check available microphones
```

**Tool Loading Problems:**
```bash
# Reset and enable all tools
STRANDS_TOOLS="ALL" maxs
```

**Database Connection Issues:**
```bash
maxs
> sql_tool(action="connect", database_type="postgresql", host="localhost")
```

</details>

## 🚀 Why Developers Choose maxs

> *"Started using maxs for quick scripts. Now our entire team builds tools by talking to them. Saved 20 hours last week alone."*  
> — DevOps Engineer

**Key advantages:**
- ⚡ **Instant gratification** - Working tools in 30 seconds
- 🎙️ **Voice-first** - Build while you think out loud  
- 🔄 **Hot reload** - Iterate without interruption
- 📡 **Distributed** - Team coordination without servers
- 🧠 **Intelligent** - Remembers your context and decisions

---

## 📦 Installation

```bash
pipx install maxs && maxs
```

**Alternative setups:**
- **Development:** `git clone https://github.com/cagataycali/maxs && pip install -e .`
- **Binary:** `pip install maxs[binary]` then `pyinstaller --onefile -m maxs.main`

## 📄 License

MIT - Use it however you want!
