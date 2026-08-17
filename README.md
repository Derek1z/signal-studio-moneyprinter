# Signal Studio × MoneyPrinterTurbo

A compact, human-gated YouTube content workflow that turns a niche into a validated MoneyPrinterTurbo generation payload with live AI council deliberation, real-time research grounding, and direct engine dispatch.

## What it includes

- **Creative Brief**: Niche, audience, and editorial-goal input
- **Live AI & Trend Scoring**: Deterministic demo fixtures alongside live Google Gemini, OpenAI/Ollama, and YouTube Data API v3 trend scoring
- **3-Advisor Council & Judge**: Multi-perspective ideation (*Story Architect*, *Audience Advocate*, *Skeptical Editor*) with automated executive judge evaluation
- **Research & Citation Gate**: Live web search citations (zero-key DuckDuckGo or Google Programmable Search) with primary source links
- **Script Editor**: Duration estimation, word counter, and mandatory personal proof/experience verification
- **Packaging & Visual Concepts**: High-CTR title alternatives, thumbnail layout prompts, and B-roll search tag generation
- **Monetization & Reused-Content Risk Audit**: Heuristic analysis with remediation advice to keep channels compliant with YouTube policies
- **MoneyPrinterTurbo Dispatch**: Validated `VideoParams` contract generation with direct REST API dispatch and one-click JSON payload download

The studio operates with **zero-key demo fallbacks by default**, so it runs instantly without mandatory API keys. Add your keys in the sidebar drawer or via environment variables to enable live AI deliberation and search.

## Run locally

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run studio_app.py
```

On macOS/Linux, activate with `source .venv/bin/activate`.

## Environment Variables (Optional)

You can pre-configure API keys via environment variables:
- `GEMINI_API_KEY`: For Google Gemini 2.5 / 1.5 models
- `OPENAI_API_KEY`: For OpenAI GPT-4o / GPT-4o-mini
- `YOUTUBE_API_KEY`: For YouTube Data API v3 trend analysis
- `GOOGLE_SEARCH_API_KEY` & `GOOGLE_SEARCH_CX`: For Google Programmable Search

## Architecture

The studio is an editorial orchestration and safety layer. It produces a payload matching MoneyPrinterTurbo Extended's `VideoParams` contract, while video rendering remains in the upstream engine.

Upstream project: https://github.com/Asad-Ismail/MoneyPrinterTurbo-Extended
