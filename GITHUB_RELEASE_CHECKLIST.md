# GitHub Publication & Release Checklist — CyberShield AI

This checklist outlines the mandatory quality checks, test validations, security sweeps, and documentation reviews required before pushing the repository to public production or executing a GitHub Release.

---

## 🚀 Pre-Push Checks

- [ ] **Clean Git Status**: Verify no untracked artifacts, log outputs, or temp check files exist in the active directory.
  * *Command*: `git status`
- [ ] **No Staged Configurations**: Verify `.env` files are in `.gitignore` and are not staged in the current index.
  * *Command*: `git diff --name-only --cached`
- [ ] **Branch Match**: Ensure the active branch is aligned with target release guidelines (e.g. `main` or `release/v1.0`).

---

## 🧪 Testing & Linting Checks

- [ ] **Python Unit & Integration Tests**: Verify all tests in the backend pass successfully.
  * *Command*: `pytest`
- [ ] **TypeScript Type Safety**: Verify the frontend has no compilation or type validation errors.
  * *Command*: `npm run typecheck` in `artifacts/cybershield`
- [ ] **Frontend Production Build**: Verify Vite React compiles without packaging failures.
  * *Command*: `npm run build` in `artifacts/cybershield`
- [ ] **Python Styling Checks**: Run styling and format checks to verify styling alignment.
  * *Command*: `ruff check` in `artifacts/api-server`

---

## 🔒 Secret & Key Checks

- [ ] **API Keys Clean Sweep**: Run a scan to ensure no active OpenAI, Gemini, or LangSmith keys have been committed.
  * *Signature patterns to scan*:
    * `sk-` (OpenAI Keys)
    * `AIzaSy` (Gemini Keys)
    * `lsv2_` (LangSmith Keys)
- [ ] **Template Environment Settings**: Verify the [artifacts/api-server/.env](artifacts/api-server/.env) contains **only placeholder values** (e.g. `YOUR_GEMINI_API_KEY_HERE`) and no real keys.
- [ ] **Mock Embedding Dimensions**: Confirm mock/offline configurations (in `embedding_service.py`) dynamically adapt fallback dimensions when running without keys.

---

## 📄 Documentation Checks

- [ ] **README.md Validation**: Verify the root [README.md](README.md) details:
  * Problem Statement and Architecture
  * Complete Local Setup instructions (commands and ports)
  * Dynamic Gemini and OpenAI environment configurations
  * ASCII-compatible Project Structure Tree
- [ ] **Code Quality Review**: Verify [CODE_QUALITY_ANALYSIS.md](CODE_QUALITY_ANALYSIS.md) is updated and describes input sanitization, prompt injection guards, and LangGraph containment patterns.
- [ ] **Observability Documentation**: Verify [OBSERVABILITY_ANALYSIS.md](OBSERVABILITY_ANALYSIS.md) matches the two-tier tracing structure and database mapping layout.
- [ ] **Clickable Markdown Links**: Ensure all referenced file paths are valid relative paths from the workspace root.
