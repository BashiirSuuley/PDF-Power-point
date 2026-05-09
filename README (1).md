# 📄 → 📊 PDF to PowerPoint — AI Converter

Upload any PDF → AI reads every page → Beautiful `.pptx` downloaded instantly.

## Files to upload to GitHub
- `app.py` — main app (uses raw HTTP, no anthropic package)
- `requirements.txt` — only streamlit + requests
- `packages.txt` — installs Node.js on Streamlit Cloud
- `README.md` — this file

## Deploy on Streamlit Cloud
1. Create GitHub repo, upload all 4 files
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. New app → your repo → branch: main → main file: `app.py`
4. Deploy

## Run locally
```bash
npm install -g pptxgenjs
pip install streamlit requests
streamlit run app.py
```
