# Signal Studio × MoneyPrinter Native

An all-in-one, human-led AI video production workstation with **in-house MP4 rendering**, 3-advisor council deliberation, viral hook A/B testing, live karaoke subtitle simulation, and multi-platform packaging.

## 🌟 Key Capabilities

- **🎬 In-House Video Rendering (`studio/renderer.py`)**: Assemble complete MP4 videos with Microsoft Neural voiceover, B-roll footage, subtitles, and audio mixing directly in the app.
- **🎙️ Edge-TTS Voice Synthesizer (`studio/voice.py`)**: 100% free neural speech generation (Jenny, Guy, Aria, Sonia, Davis) with speed control and word-by-word subtitle timestamps (zero API keys required).
- **🎞️ Pexels Stock Media Downloader (`studio/stock_media.py`)**: Automatic HD stock clip search, download, and local caching.
- **📱 Live Video & Subtitle Simulator (`studio/simulator.py`)**: Real-time HTML5 video canvas with dynamic karaoke word highlighting for instant pre-render visualization.
- **🧪 Viral Hook A/B Lab (`studio/hooks.py`)**: 5 psychological hook archetypes with predicted **3-Second Hold Rate %** and 1-click script insertion.
- **📽️ Scene Storyboard Timeline (`studio/storyboard.py`)**: 5-second scene breakdown with targeted visual search queries and camera motions.
- **🎨 Vector SVG Thumbnail Canvas (`studio/thumbnails.py`)**: Scalable, high-contrast SVG thumbnail mockups with glow effects, 4 color themes, and AI image prompts.
- **📈 Script Retention Science (`studio/retention.py`)**: Sentence-by-sentence pacing map, AI cliché scanner, and 4 creator tone presets (*Hormozi*, *Veritasium*, *Shorts*, *Balanced*).
- **📦 Multi-Platform Social SEO (`studio/social.py`)**: Auto-generated YouTube chapters/timestamps, citations, X/Twitter threads, and LinkedIn posts.
- **🗂️ Project Library Manager (`studio/storage.py`)**: Save, load, and manage draft projects locally.

## Run Locally

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run studio_app.py
```

On macOS/Linux, activate with `source .venv/bin/activate`.

## Optional Environment Variables

- `GEMINI_API_KEY`: For Google Gemini 2.5 / 1.5 live AI council
- `OPENAI_API_KEY`: For OpenAI GPT-4o / GPT-4o-mini
- `PEXELS_API_KEY`: For live Pexels HD video search (uses curated offline stock cache if omitted)
- `YOUTUBE_API_KEY`: For YouTube Data API v3 trend metrics
- `GOOGLE_SEARCH_API_KEY` & `GOOGLE_SEARCH_CX`: For Google Programmable Search

## Upstream Integration

While Signal Studio can render standalone MP4s natively, it also produces validated `VideoParams` payloads for upstream [MoneyPrinterTurbo-Extended](https://github.com/Asad-Ismail/MoneyPrinterTurbo-Extended).
