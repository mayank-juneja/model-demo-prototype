# Credit Memo SME Review Portal

A prototype demo showing how AI can assist with credit memo generation and review.

**JupyterLab-style shell** (FastAPI) wraps a **Gradio SME review app** with a **Claude-powered MLBuddy chat assistant**.

---

## Setup

**1. Clone and enter the project**
```bash
git clone https://github.com/mayank-juneja/model-demo-prototype
cd model-demo-prototype
```

**2. Create a virtual environment and install dependencies**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**3. Add your Anthropic API key**
```bash
cp .env.example .env
# edit .env and set ANTHROPIC_API_KEY=sk-ant-...
```

---

## Run

```bash
.venv/bin/uvicorn main:app --reload --port 8000
```

Then open **http://127.0.0.1:8000** in your browser.

> The Gradio credit memo app starts automatically on port 7860.
> Do not close the terminal — both servers run from this one command.

---

## What you can do

| Action | How |
|--------|-----|
| View the credit memo pipeline | Explore the JupyterLab tabs |
| Chat with MLBuddy | Use the chat panel (bottom right) |
| Run the credit memo app | Ask MLBuddy "run the app" or click the Credit Memo App tab |
| Edit the app code | Open `creditmemo_gradioapp.py` in the file browser, edit, save — app reloads automatically |
| Share publicly | Ask MLBuddy "run in share mode" — generates a `gradio.live` URL |

---

## Project structure

```
main.py                  # FastAPI server (shell + API endpoints)
jupyterlab.html          # JupyterLab-style UI
creditmemo_gradioapp.py  # Gradio SME review app
sample_data.py           # Sample credit memo (Acme Industrial Corp)
chat_service.py          # Claude API streaming for MLBuddy
run_gradio.py            # Gradio launcher (patches gradio-client bug)
.env.example             # Environment variable template
```
