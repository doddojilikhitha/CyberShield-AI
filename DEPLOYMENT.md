# Deployment & Setup Manual — CyberShield AI

This guide contains instructions on setting up, configuring, running, and deploying the **CyberShield AI** platform.

---

## ⚙️ Environment Variables Config Checklist

Create a `.env` file inside `/artifacts/api-server/` with the following variables:

```bash
# Core API Keys
OPENAI_API_KEY=sk-...               # OpenAI key to engage agent chains and embeddings

# Observability (Optional)
LANGSMITH_API_KEY=lsv2_...          # (Optional) LangSmith API tracing key
LANGCHAIN_TRACING_V2=true           # Set to true to trace to LangSmith
LANGCHAIN_PROJECT=cybershield-ai
```

---

## 🏃 Local Execution

### Backend Launch (Python)
1. Install Python packages:
   ```bash
   cd artifacts/api-server
   pip install -r requirements.txt
   pip install fpdf2
   ```
2. Launch:
   ```bash
   python main.py
   ```
   *The server initializes SQLite tables, builds/updates ChromaDB vector embeddings, and runs on `http://localhost:8080`.*

### Frontend Launch (Vite React)
1. Install node dependencies:
   ```bash
   cd artifacts/cybershield
   npm install
   ```
2. Launch dev server:
   ```bash
   npm run dev
   ```
   *The client starts on `http://localhost:5173` (or the first available port) and communicates with the backend.*

---

## 🐳 Docker Deployment

To launch both frontend and backend automatically with persistence using Docker Compose:

1. Setup environment keys in the root directory `.env`.
2. Build and launch:
   ```bash
   docker-compose up --build
   ```
3. Visit the frontend on `http://localhost`.

---

## 🚀 Replit Deployment

1. Import the repository workspace.
2. The `.replit` and `replit.nix` configurations automatically prepare Python 3.12 and Node environments.
3. Configure your API secrets in **Secrets Manager**:
   - `OPENAI_API_KEY`
4. Click **Run** to execute.

---

## ☁️ Render Deployment

The repository includes a `render.yaml` configuration template defining:
- A python service for the backend.
- A static service for the React dashboard.

1. Create a new Blueprint instance on Render.
2. Point it to this repository.
3. Approve keys mapping configurations and deploy.
