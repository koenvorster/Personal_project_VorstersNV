# Dev Container Setup for VorstersNV

Your development container is now configured with all necessary tools!

## 🚀 Quick Start

### Option 1: VS Code Dev Container (Recommended)
1. **Open the project in VS Code**
2. **Install the "Dev Containers" extension** (ms-vscode-remote.remote-containers)
3. **Click** "Reopen in Container" when prompted, or:
   - Press `Ctrl+Shift+P` → "Dev Containers: Reopen in Container"
4. Wait for the container to build and post-create script to run

### Option 2: Manual Setup (Without Dev Container)
```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Node.js dependencies
cd frontend && npm install && cd ..

# Start Docker services
docker-compose up -d
```

## 📋 What's Included

✅ **GitHub CLI** - Manage repos, PRs, issues from terminal  
✅ **Python 3.12** - Latest stable with full dev tools  
✅ **Node.js 18** - Frontend development  
✅ **Docker-in-Docker** - Run containers from within container  
✅ **VS Code Extensions** - Python, Pylance, Ruff, ESLint, Copilot  

## 🛠️ Available Commands

### Backend
```bash
# Start webhook service
uvicorn webhooks.app:app --reload --port 8000

# Run tests
pytest tests/ -v

# Test an agent
python scripts/test_agent.py klantenservice_agent

# Switch project mode
python scripts/set_mode.py --mode build
```

### Frontend
```bash
cd frontend

# Dev server
npm run dev

# Build
npm run build

# Linting
npm run lint
```

### Docker Services
```bash
# Start all services (Ollama, PostgreSQL, Redis)
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f
```

### GitHub CLI
```bash
# Login to GitHub (first time)
gh auth login

# Create a PR
gh pr create --title "Feature: ..." --body "Description"

# List issues
gh issue list

# Check status
gh status
```

## 📦 Port Forwarding

When running in dev container, these ports are automatically forwarded:

| Port | Service |
|------|---------|
| **3000** | Next.js Frontend |
| **8000** | FastAPI Backend |
| **11434** | Ollama |
| **5432** | PostgreSQL |
| **6379** | Redis |

## 🔐 Environment Variables

The `.env` file is created automatically in post-create script. Update these values for production:

```env
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_DEFAULT_MODEL=llama3
WEBHOOK_SECRET=dev-secret-change-me
DB_URL=postgresql+asyncpg://vorstersNV:dev-password-change-me@postgres:5432/vorstersNV
REDIS_URL=redis://redis:6379
```

## 📚 Project Structure

```
Personal_project_VorstersNV/
├── agents/           # YAML agent definitions
├── ollama/           # Ollama client & runner
├── webhooks/         # FastAPI webhook handlers
├── api/              # API routers
├── db/               # Database models & migrations
├── frontend/         # Next.js app
├── prompts/          # System & preprompets
├── scripts/          # Utility scripts
└── tests/            # Test suite
```

## ✅ First Time Setup Checklist

- [ ] Dev container is running
- [ ] `.env` file is configured
- [ ] `docker-compose up -d` started services
- [ ] `pytest tests/ -v` passes
- [ ] Frontend dev server starts: `cd frontend && npm run dev`
- [ ] GitHub CLI logged in: `gh auth login`

## 🐛 Troubleshooting

**Container won't start?**
- Delete `.devcontainer` and rebuild
- Check Docker is running
- Review build logs in VS Code output

**Port conflicts?**
- Change ports in `docker-compose.yml`
- Forward different host port in `devcontainer.json`

**Python imports failing?**
- Rebuild container
- Reinstall dependencies: `pip install -r requirements.txt`

**Still stuck?**
- Check logs: `docker-compose logs <service>`
- Run health check: `curl http://localhost:8000/health`

---

Happy coding! 🎉
