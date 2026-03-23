# Credit Memo SME Review Portal — CLAUDE.md

## Project Overview

A working prototype application for AI-generated credit memo review by Subject Matter Experts (SMEs).
SMEs review each section of an AI-generated credit memo, flag issues, edit content, and submit labeled
feedback for prompt refinement and fine-tuning.

**Current state:** Static HTML demo (`jupyterlab.html`) + Gradio Python app (`creditmemo_gradioapp.py`)
**Goal:** Full working prototype — real backend, real UI, agentic development workflow

**Stack:** Python, Gradio (current) — open to evolving based on what best serves the prototype

## Critical Rules

### 1. Code Organization

- Many small files over few large files
- High cohesion, low coupling
- 200-400 lines typical, 800 max per file
- Organize by feature/domain, not by type

### 2. Code Style

- No hardcoded secrets or API keys — use `.env`
- Immutability preferred — avoid mutating shared state
- No leftover debug prints in production code
- Proper error handling
- Validate all user inputs at boundaries

### 3. Testing

- Write tests for new logic before or alongside implementation
- Cover happy path + error cases
- Unit tests for utilities and helpers
- Integration tests for API/backend routes

### 4. Security

- No hardcoded secrets — use environment variables
- Validate all user inputs
- No sensitive data in logs

## File Structure

```
model_demo_prototype/
├── creditmemo_gradioapp.py   # Main Gradio app (current prototype)
├── sample_data.py            # Sample credit memo data
├── jupyterlab.html           # Static HTML demo UI
├── CLAUDE.md                 # This file
├── .env.example              # Environment variable template
├── .env                      # Local env (gitignored)
└── .claude/
    ├── agents/               # Specialized subagents
    ├── commands/             # Slash commands
    ├── rules/                # Coding rules (common + python)
    ├── contexts/             # Dev / research / review modes
    └── hooks.json            # Automation hooks
```

## Available Agents

- `planner` — implementation planning before writing code
- `architect` — system design and architecture decisions
- `code-reviewer` — code quality and security review
- `security-reviewer` — security vulnerability detection
- `tdd-guide` — test-driven development workflow
- `build-error-resolver` — fix Python/runtime errors
- `python-reviewer` — Python-specific code review
- `doc-updater` — keep documentation current
- `refactor-cleaner` — dead code cleanup

## Available Commands

- `/plan` — create implementation plan before starting
- `/code-review` — review code quality
- `/python-review` — Python-specific review
- `/tdd` — test-driven development workflow
- `/build-fix` — fix build/runtime errors
- `/verify` — verify implementation matches plan
- `/checkpoint` — save progress snapshot
- `/learn` — extract patterns from session
- `/quality-gate` — run quality checks
- `/update-docs` — update documentation

## Development Workflow

1. **Plan first** — use `/plan` before implementing anything non-trivial
2. **Write tests** — use `/tdd` for new features
3. **Review** — use `/code-review` or `/python-review` before considering done
4. **Verify** — use `/verify` to confirm implementation matches intent
5. **Checkpoint** — use `/checkpoint` to save progress

## Environment Variables

```bash
# Required for AI features
ANTHROPIC_API_KEY=

# Optional
GRADIO_SERVER_PORT=7860
GRADIO_SERVER_NAME=0.0.0.0
DEBUG=false
```

## Git Workflow

- Conventional commits: `feat:`, `fix:`, `refactor:`, `docs:`, `test:`
- Never commit `.env` or secrets
- All tests must pass before committing
