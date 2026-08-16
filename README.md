# Signal Studio × MoneyPrinterTurbo

A compact, human-gated YouTube content workflow that turns a niche into a validated MoneyPrinterTurbo generation payload.

## What it includes

- niche, audience, and editorial-goal input
- deterministic trend/topic scoring with a live-provider seam
- inspectable three-advisor LLM council abstraction and judge
- research/fact-check approval gate
- script editor and explicit production approval
- voice, semantic B-roll, subtitles, music, and format settings
- title and thumbnail concepts
- repetitive/reused/inauthentic-content risk checks
- MoneyPrinterTurbo-compatible JSON handoff

The hosted prototype uses clearly labeled demo providers, so it works without API keys. Replace demo evidence with live, cited research before publishing a video.

## Run locally

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run studio_app.py
```

On macOS/Linux, activate with `source .venv/bin/activate`.

## Architecture

The studio is intentionally a thin editorial orchestration layer. It produces a payload matching MoneyPrinterTurbo Extended's `VideoParams` contract, while video rendering remains in the upstream engine.

Upstream project: https://github.com/Asad-Ismail/MoneyPrinterTurbo-Extended


