# Zomato / Swiggy Review Analyser — Ollama + Qwen2.5:3b

This is AI School of India Module 1, Video 4 project.

## Run locally

Install Ollama from https://ollama.com

Then run:

```bash
ollama pull qwen2.5:3b
```

Create environment:

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## What this app does

Paste restaurant reviews and get:

- Overall sentiment
- Estimated rating
- Summary
- Top positives
- Top negatives
- Customer pain points
- Business suggestions
- Best for
- Keywords
- Downloadable JSON report

## Important

This app runs locally because Ollama runs on your laptop.

It will not work directly on Streamlit Cloud unless you switch to a cloud API like Gemini, OpenAI, or OpenRouter.
