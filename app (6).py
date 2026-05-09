import streamlit as st
import requests
import json
import base64
import subprocess
import re

# ── Page config ───────────────────────────────────────────────
st.set_page_config(
    page_title="PDF → PowerPoint · AI",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── CSS ───────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@300;400;500&display=swap');
html,body,[class*=css]{
    font-family:'DM Sans',sans-serif;
    background:#0f0f0f !important;
    color:#e8e0d8 !important;
}
.stApp{background:#0f0f0f !important;}
section[data-testid=stSidebar]{
    background:#0a0a0a !important;
    border-right:1px solid #222;
}
section[data-testid=stSidebar] *{color:#aaa !important;}
.hero{
    background:linear-gradient(135deg,#1a1a2e 0%,#16213e 50%,#0f3460 100%);
    border-radius:16px;padding:2.5rem 2rem;margin-bottom:1.5rem;
    text-align:center;border:1px solid #1e3a5f;
}
.hero h1{
    font-family:'Syne',sans-serif;font-size:2.4rem;
    font-weight:800;color:#fff;margin:0 0 .5rem;
}
.hero p{font-size:1rem;color:#7ab3d4;margin:0;}
.step-card{
    background:#161616;border:1px solid #222;
    border-radius:12px;padding:1.2rem 1.4rem;margin-bottom:.8rem;
}
.progress-bar{
    background:#1a1a1a;border-radius:8px;
    height:6px;overflow:hidden;margin:.5rem 0;
}
.progress-fill{
    height:100%;border-radius:8px;
    background:linear-gradient(90deg,#1e90ff,#00c896);
    transition:width .4s ease;
}
.slide-preview{
    background:#1a1a2e;border:1px solid #1e3a5f;
    border-radius:8px;padding:.8rem;margin-bottom:.5rem;
}
.slide-num{
    font-size:.7rem;font-weight:700;color:#1e90ff;
    text-transform:uppercase;letter-spacing:.1em;margin-bottom:.3rem;
}
.slide-title-prev{font-size:.95rem;font-weight:600;color:#fff;margin-bottom:.3rem;}
.slide-bullets{color:#7ab3d4;font-size:.78rem;line-height:1.6;}
.success-box{
    background:#0a1e0a;border:1px solid #1a4a1a;
    border-radius:12px;padding:1.5rem;text-align:center;
}
.success-title{
    font-family:'Syne',sans-serif;font-size:1.4rem;
    font-weight:700;color:#00c896;
}
.success-sub{font-size:.85rem;color:#7ab3d4;margin-top:.3rem;}
.api-box{
    background:#0a1628;border:1px solid #1e3a5f;
    border-radius:10px;padding:1rem;margin-bottom:.8rem;
    font-size:.82rem;color:#7ab3d4;line-height:1.7;
}
.free-badge{
    background:#00c896;color:#000;font-size:.7rem;
    font-weight:700;padding:2px 8px;border-radius:20px;
    margin-left:6px;vertical-align:middle;
}
#MainMenu,footer,header{visibility:hidden;}
</style>
""", unsafe_allow_html=True)

# ── Themes ────────────────────────────────────────────────────
THEMES = {
    "Midnight Executive": {"bg":"1E2761","accent":"4A90D9","text":"FFFFFF","sub":"CADCFC","dark":True},
    "Ocean Depth":        {"bg":"065A82","accent":"21B0FF","text":"FFFFFF","sub":"A8D8F0","dark":True},
    "Forest Pro":         {"bg":"1B4332","accent":"52B788","text":"FFFFFF","sub":"B7E4C7","dark":True},
    "Cherry Bold":        {"bg":"990011","accent":"FF6B6B","text":"FFFFFF","sub":"FFD6D6","dark":True},
    "Charcoal Clean":     {"bg":"2D2D2D","accent":"00D4FF","text":"FFFFFF","sub":"B0B0B0","dark":True},
    "Clean White":        {"bg":"FFFFFF","accent":"2563EB","text":"1E1E1E","sub":"6B7280","dark":False},
    "Warm Ivory":         {"bg":"FAFAF5","accent":"B85042","text":"1E1E1E","sub":"6B6B6B","dark":False},
    "Teal Professional":  {"bg":"028090","accent":"02C39A","text":"FFFFFF","sub":"A8E6DF","dark":True},
}

# ── Gemini API call (raw HTTP, no package needed) ─────────────
def call_gemini(api_key, pdf_b64, prompt):
    """Call Google Gemini 1.5 Flash via raw HTTP — 100% free."""
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-1.5-flash:generateContent?key={api_key}"
    )
    body = {
        "contents": [{
            "parts": [
                {
                    "inline_data": {
                        "mime_type": "application/pdf",
                        "data": pdf_b64
                    }
                },
                {"text": prompt}
            ]
        }],
        "generationConfig": {
            "temperature":     0.3,
            "maxOutputTokens": 8192,
        }
    }
    resp = requests.post(url, json=body, timeout=120)
    if resp.status_code == 400:
        raise ValueError("Bad request — check your API key or PDF size.")
    if resp.status_code == 403:
        raise ValueError("Invalid API key. Get a free key at aistudio.google.com")
    if resp.status_code == 429:
        raise ValueError("Rate limit reached. Wait 1 minute and try again.")
    if resp.status_code != 200:
        raise ValueError(f"Gemini API error {resp.status_code}: {resp.text[:300]}")

    data = resp.json()
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        raise ValueError(f"Unexpected API response: {str(data)[:300]}")

# ── Hero ──────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <h1>📄 → 📊 PDF to PowerPoint</h1>
  <p>Upload any PDF · Google Gemini AI reads it · Downloads a beautiful .pptx instantly</p>
</div>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔑 Google Gemini API Key")
    st.markdown("""
    <div class="api-box">
        <b style="color:#fff">FREE API Key steps:</b><br>
        1. Go to <a href="https://aistudio.google.com/app/apikey"
           target="_blank" style="color:#1e90ff">aistudio.google.com/app/apikey</a><br>
        2. Click <b style="color:#fff">Create API Key</b><br>
        3. Copy &amp; paste below<br><br>
        ✅ Completely free · No credit card · 15 req/min
    </div>
    """, unsafe_allow_html=True)

    api_key = st.text_input(
        "", type="password",
        placeholder="AIzaSy...",
        label_visibility="collapsed"
    )
    st.markdown("---")

    st.markdown("### 🎨 Theme")
    selected_theme = st.selectbox(
        "", list(THEMES.keys()),
        label_visibility="collapsed"
    )
    st.markdown("---")

    st.markdown("### ⚙️ Settings")
    num_slides      = st.slider("Number of slides", 6, 20, 10)
    pres_style      = st.selectbox("Presentation style", [
        "Executive Summary", "Detailed Report",
        "Academic / Research", "Business Pitch", "Training / Workshop"
    ])
    custom_focus    = st.text_input(
        "Focus topic (optional)",
        placeholder="e.g. financials, key findings..."
    )
    incl_charts     = st.checkbox("Auto-detect data for charts", value=True)
    incl_summary    = st.checkbox("Executive summary slide",     value=True)
    incl_conclusion = st.checkbox("Conclusion / next steps",     value=True)

# ── Upload ────────────────────────────────────────────────────
col1, col2 = st.columns([1.2, 1])

with col1:
    st.markdown("### 📤 Upload PDF")
    uploaded = st.file_uploader(
        "", type=["pdf"], label_visibility="collapsed"
    )
    if uploaded:
        st.markdown(f"""
        <div class="step-card">
          <div style="font-size:1.4rem;color:#00c896">✓</div>
          <div style="font-weight:600;color:#fff">{uploaded.name}</div>
          <div style="font-size:.82rem;color:#666">
            {len(uploaded.getvalue())//1024} KB · Ready to convert
          </div>
        </div>""", unsafe_allow_html=True)

with col2:
    st.markdown("### 📊 Slide preview")
    preview_box = st.empty()
    preview_box.markdown("""
    <div style="background:#161616;border:1px dashed #333;border-radius:12px;
                padding:3rem 2rem;text-align:center;color:#444;font-size:.9rem">
        <div style="font-size:3rem;margin-bottom:.8rem">📊</div>
        Upload a PDF and click Generate
    </div>""", unsafe_allow_html=True)

# ── Generate button ───────────────────────────────────────────
st.markdown("---")
_, btn_col, _ = st.columns([1, 2, 1])
with btn_col:
    generate = st.button(
        "✨  Generate PowerPoint",
        use_container_width=True,
        type="primary"
    )

# ── Main logic ────────────────────────────────────────────────
if generate:
    if not api_key:
        st.error("Please enter your Google Gemini API key in the sidebar. It is FREE at aistudio.google.com/app/apikey")
        st.stop()
    if not uploaded:
        st.error("Please upload a PDF file.")
        st.stop()

    theme     = THEMES[selected_theme]
    status_el = st.empty()
    prog_el   = st.empty()

    def show_progress(msg, pct):
        status_el.markdown(
            f'<div style="text-align:center;font-size:.9rem;'
            f'color:#7ab3d4;margin:.5rem 0">{msg}</div>',
            unsafe_allow_html=True
        )
        prog_el.markdown(
            f'<div class="progress-bar">'
            f'<div class="progress-fill" style="width:{pct}%"></div>'
            f'</div>',
            unsafe_allow_html=True
        )

    try:
        # ── Step 1: Encode PDF ─────────────────────────────────
        show_progress("📖 Reading PDF…", 10)
        pdf_b64 = base64.standard_b64encode(uploaded.getvalue()).decode()

        # ── Step 2: Call Gemini ────────────────────────────────
        show_progress("🧠 Gemini AI analysing document…", 25)

        prompt = f"""You are an expert presentation designer.
Carefully read this entire PDF document. Extract ALL real content — facts, numbers, quotes, statistics, findings.
Create a JSON plan for a {num_slides}-slide {pres_style} presentation.

STRICT RULES:
- Use ONLY content found in this PDF. Never invent or hallucinate anything.
- Every bullet point must be a specific real fact from the document.
- Be detailed and specific — include actual numbers, percentages, names from the PDF.
{"- Slide 1 must be an executive summary of the whole document." if incl_summary else ""}
{"- Final slide must be conclusion and next steps." if incl_conclusion else ""}
{"- Find numerical data (tables, stats, percentages) and create chart slides from them." if incl_charts else ""}
{"- Pay special attention to: " + custom_focus + "." if custom_focus else ""}

Return ONLY valid JSON. No markdown. No explanation. No code fences. Just the raw JSON object:
{{
  "title": "exact title from document",
  "subtitle": "subtitle or document description",
  "author": "author name if found, else empty string",
  "slides": [
    {{"slide_num":1,"type":"title","title":"...","subtitle":"...","body":"..."}},
    {{"slide_num":2,"type":"bullets","title":"...","bullets":["Real specific fact 1","Real specific fact 2","Real specific fact 3","Real specific fact 4","Real specific fact 5"]}},
    {{"slide_num":3,"type":"two_col","title":"...","left_title":"...","left_points":["...","...","..."],"right_title":"...","right_points":["...","...","..."]}},
    {{"slide_num":4,"type":"chart","title":"...","chart_type":"bar","chart_labels":["Label1","Label2","Label3","Label4"],"chart_values":[10,20,15,25],"chart_title":"...","body":"data source context"}},
    {{"slide_num":5,"type":"stat_callout","title":"...","stats":[{{"value":"87%","label":"Metric name"}},{{"value":"$2.4M","label":"Metric name"}},{{"value":"3x","label":"Metric name"}}],"body":"supporting context"}},
    {{"slide_num":6,"type":"conclusion","title":"Key Conclusions","bullets":["Takeaway 1","Takeaway 2","Next step 1","Next step 2"]}}
  ]
}}

Generate exactly {num_slides} slides total.
Use a good variety of types across slides: bullets, two_col, chart, stat_callout, quote, conclusion.
No two consecutive slides should have the same type."""

        raw_text = call_gemini(api_key, pdf_b64, prompt)

        show_progress("🔍 Parsing AI response…", 45)

        # Clean and parse JSON
        clean = raw_text.strip()
        clean = re.sub(r"^```(?:json)?", "", clean).strip()
        clean = re.sub(r"```$",          "", clean).strip()
        start = clean.find("{")
        end   = clean.rfind("}") + 1
        if start == -1 or end == 0:
            raise ValueError("No JSON found in Gemini response.")
        clean = clean[start:end]
        plan  = json.loads(clean)

        show_progress("✅ Content extracted — designing slides…", 55)

        # ── Step 3: Preview ────────────────────────────────────
        prev = ""
        for s in plan.get("slides", [])[:6]:
            bl = ""
            if s.get("bullets"):
                bl = "".join(f"· {b}<br>" for b in s["bullets"][:3])
            elif s.get("stats"):
                bl = " &nbsp;|&nbsp; ".join(
                    f"<b>{x['value']}</b> {x['label']}"
                    for x in s["stats"][:3]
                )
            elif s.get("left_points"):
                bl = "".join(f"· {b}<br>" for b in s["left_points"][:2])
            prev += (
                f'<div class="slide-preview">'
                f'<div class="slide-num">'
                f'Slide {s.get("slide_num","")} · {s.get("type","").upper()}'
                f'</div>'
                f'<div class="slide-title-prev">{s.get("title","")}</div>'
                f'<div class="slide-bullets">{bl}</div>'
                f'</div>'
            )
        preview_box.markdown(prev, unsafe_allow_html=True)

        # ── Step 4: Install pptxgenjs ──────────────────────────
        show_progress("📦 Preparing slide engine…", 65)
        subprocess.run(
            ["npm", "install", "-g", "pptxgenjs"],
            capture_output=True, check=False
        )

        # ── Step 5: Build PPTX ─────────────────────────────────
        show_progress("🎨 Designing beautiful slides…", 75)

        bg   = theme["bg"]
        acc  = theme["accent"]
        txt  = theme["text"]
        sub  = theme["sub"]
        card = "1E2A3A" if theme["dark"] else "F0F4F8"

        def esc(v):
            return (str(v)
                    .replace("\\", "\\\\")
                    .replace('"',  '\\"')
                    .replace("\n", " ")
                    .replace("\r", "")
                    .replace("'",  "\\'"))

        def bullet_arr(items, sz=15):
            parts = []
            for i, b in enumerate(items):
                bl = esc(b)
                br = "true" if i < len(items) - 1 else "false"
                parts.append(
                    f'{{text:"{bl}",options:{{'
                    f'bullet:true,breakLine:{br},fontSize:{sz},'
                    f'color:"{sub}",paraSpaceAfter:6}}}}'
                )
            return "[" + ",".join(parts) + "]"

        def hdr(t):
            return (
                f'sl.addShape(pres.shapes.RECTANGLE,'
                f'{{x:0,y:0,w:10,h:0.12,'
                f'fill:{{color:"{acc}"}},line:{{color:"{acc}"}}}});'
                f'sl.addShape(pres.shapes.RECTANGLE,'
                f'{{x:0.4,y:0.22,w:9.2,h:0.88,'
                f'fill:{{color:"{card}"}},line:{{color:"{acc}",pt:0}}}});'
                f'sl.addText("{t}",{{x:0.6,y:0.24,w:8.8,h:0.84,'
                f'fontSize:24,bold:true,color:"{txt}",'
                f'fontFace:"Georgia",valign:"middle",margin:0}});'
            )

        slides_js = []

        for s in plan.get("slides", []):
            stype = s.get("type", "bullets")
            st_   = esc(s.get("title", ""))
            snum  = s.get("slide_num", "")
            ftr   = (
                f'sl.addText("{snum}",{{x:9.2,y:5.25,w:0.5,h:0.25,'
                f'fontSize:9,color:"{sub}",align:"right"}});'
            )

            if stype == "title":
                st2  = esc(s.get("subtitle", ""))
                auth = esc(plan.get("author", ""))
                js = (
                    f'{{let sl=pres.addSlide();'
                    f'sl.background={{color:"{bg}"}};'
                    f'sl.addShape(pres.shapes.RECTANGLE,'
                    f'{{x:0,y:0,w:0.18,h:5.625,'
                    f'fill:{{color:"{acc}"}},line:{{color:"{acc}"}}}});'
                    f'sl.addText("{st_}",{{x:0.5,y:1.2,w:9,h:2.0,'
                    f'fontSize:40,bold:true,color:"{txt}",'
                    f'fontFace:"Georgia",valign:"middle"}});'
                    f'sl.addText("{st2}",{{x:0.5,y:3.3,w:9,h:0.8,'
                    f'fontSize:18,color:"{sub}",fontFace:"Calibri"}});'
                    f'sl.addText("{auth}",{{x:0.5,y:4.8,w:9,h:0.5,'
                    f'fontSize:12,color:"{sub}",fontFace:"Calibri",italic:true}});'
                    f'sl.addShape(pres.shapes.RECTANGLE,'
                    f'{{x:0.5,y:5.2,w:2.5,h:0.05,'
                    f'fill:{{color:"{acc}"}},line:{{color:"{acc}"}}}}); }}'
                )

            elif stype == "bullets":
                ba = bullet_arr(s.get("bullets", []))
                js = (
                    f'{{let sl=pres.addSlide();'
                    f'sl.background={{color:"{bg}"}};'
                    f'{hdr(st_)}'
                    f'sl.addText({ba},{{x:0.6,y:1.28,w:8.8,h:4.1,'
                    f'fontFace:"Calibri",valign:"top"}});'
                    f'{ftr}}}'
                )

            elif stype == "two_col":
                lt  = esc(s.get("left_title",  "Left"))
                rt  = esc(s.get("right_title", "Right"))
                lba = bullet_arr(s.get("left_points",  []), 14)
                rba = bullet_arr(s.get("right_points", []), 14)
                js = (
                    f'{{let sl=pres.addSlide();'
                    f'sl.background={{color:"{bg}"}};'
                    f'sl.addShape(pres.shapes.RECTANGLE,'
                    f'{{x:0,y:0,w:10,h:0.12,'
                    f'fill:{{color:"{acc}"}},line:{{color:"{acc}"}}}});'
                    f'sl.addText("{st_}",{{x:0.4,y:0.18,w:9.2,h:0.75,'
                    f'fontSize:26,bold:true,color:"{txt}",'
                    f'fontFace:"Georgia",valign:"middle"}});'
                    f'sl.addShape(pres.shapes.RECTANGLE,'
                    f'{{x:0.3,y:1.05,w:4.5,h:4.2,'
                    f'fill:{{color:"{card}"}},line:{{color:"{acc}",pt:1}}}});'
                    f'sl.addShape(pres.shapes.RECTANGLE,'
                    f'{{x:0.3,y:1.05,w:4.5,h:0.48,'
                    f'fill:{{color:"{acc}"}},line:{{color:"{acc}"}}}});'
                    f'sl.addText("{lt}",{{x:0.4,y:1.07,w:4.3,h:0.44,'
                    f'fontSize:13,bold:true,color:"FFFFFF",'
                    f'fontFace:"Calibri",valign:"middle",margin:0}});'
                    f'sl.addText({lba},{{x:0.4,y:1.62,w:4.3,h:3.5,'
                    f'fontFace:"Calibri",valign:"top"}});'
                    f'sl.addShape(pres.shapes.RECTANGLE,'
                    f'{{x:5.2,y:1.05,w:4.5,h:4.2,'
                    f'fill:{{color:"{card}"}},line:{{color:"{acc}",pt:1}}}});'
                    f'sl.addShape(pres.shapes.RECTANGLE,'
                    f'{{x:5.2,y:1.05,w:4.5,h:0.48,'
                    f'fill:{{color:"{acc}"}},line:{{color:"{acc}"}}}});'
                    f'sl.addText("{rt}",{{x:5.3,y:1.07,w:4.3,h:0.44,'
                    f'fontSize:13,bold:true,color:"FFFFFF",'
                    f'fontFace:"Calibri",valign:"middle",margin:0}});'
                    f'sl.addText({rba},{{x:5.3,y:1.62,w:4.3,h:3.5,'
                    f'fontFace:"Calibri",valign:"top"}});'
                    f'{ftr}}}'
                )

            elif stype == "chart":
                labels = json.dumps(s.get("chart_labels", ["A","B","C"]))
                values = json.dumps(s.get("chart_values", [1,2,3]))
                ctitle = esc(s.get("chart_title", st_))
                body   = esc(s.get("body", ""))
                cmap   = {
                    "bar":    "pres.charts.BAR",
                    "column": "pres.charts.BAR",
                    "line":   "pres.charts.LINE",
                    "pie":    "pres.charts.PIE",
                }
                ct = cmap.get(s.get("chart_type","bar").lower(),"pres.charts.BAR")
                js = (
                    f'{{let sl=pres.addSlide();'
                    f'sl.background={{color:"{bg}"}};'
                    f'{hdr(st_)}'
                    f'sl.addChart({ct},'
                    f'[{{name:"{ctitle}",labels:{labels},values:{values}}}],'
                    f'{{x:0.4,y:1.22,w:9.2,h:3.85,barDir:"col",'
                    f'chartColors:["{acc}","3498DB","2ECC71","E74C3C","9B59B6"],'
                    f'chartArea:{{fill:{{color:"{card}"}}}},'
                    f'catAxisLabelColor:"{sub}",valAxisLabelColor:"{sub}",'
                    f'valGridLine:{{color:"333333",size:0.5}},'
                    f'catGridLine:{{style:"none"}},'
                    f'showValue:true,dataLabelColor:"{txt}",showLegend:false}});'
                    f'sl.addText("{body}",{{x:0.4,y:5.14,w:9.2,h:0.36,'
                    f'fontSize:10,color:"{sub}",fontFace:"Calibri",italic:true}});'
                    f'{ftr}}}'
                )

            elif stype == "stat_callout":
                stats  = s.get("stats", [])
                body   = esc(s.get("body", ""))
                xpos   = [0.3, 3.5, 6.7]
                stat_s = ""
                for i, si in enumerate(stats[:3]):
                    xp  = xpos[i]
                    val = esc(si.get("value",""))
                    lbl = esc(si.get("label",""))
                    stat_s += (
                        f'sl.addShape(pres.shapes.RECTANGLE,'
                        f'{{x:{xp},y:1.2,w:3.0,h:2.8,'
                        f'fill:{{color:"{card}"}},line:{{color:"{acc}",pt:1}}}});'
                        f'sl.addShape(pres.shapes.RECTANGLE,'
                        f'{{x:{xp},y:1.2,w:3.0,h:0.12,'
                        f'fill:{{color:"{acc}"}},line:{{color:"{acc}"}}}});'
                        f'sl.addText("{val}",{{x:{xp+0.1},y:1.52,w:2.8,h:1.35,'
                        f'fontSize:44,bold:true,color:"{acc}",'
                        f'fontFace:"Georgia",align:"center",valign:"middle"}});'
                        f'sl.addText("{lbl}",{{x:{xp+0.1},y:2.87,w:2.8,h:0.7,'
                        f'fontSize:13,color:"{sub}",fontFace:"Calibri",'
                        f'align:"center",valign:"middle"}});'
                    )
                js = (
                    f'{{let sl=pres.addSlide();'
                    f'sl.background={{color:"{bg}"}};'
                    f'{hdr(st_)}{stat_s}'
                    f'sl.addText("{body}",{{x:0.4,y:4.22,w:9.2,h:0.88,'
                    f'fontSize:13,color:"{sub}",fontFace:"Calibri",valign:"top"}});'
                    f'{ftr}}}'
                )

            elif stype == "quote":
                quote = esc(s.get("body", s.get("quote","")))
                auth  = esc(s.get("author",""))
                js = (
                    f'{{let sl=pres.addSlide();'
                    f'sl.background={{color:"{bg}"}};'
                    f'sl.addShape(pres.shapes.RECTANGLE,'
                    f'{{x:0,y:0,w:0.18,h:5.625,'
                    f'fill:{{color:"{acc}"}},line:{{color:"{acc}"}}}});'
                    f'sl.addText("\\u201C",{{x:0.5,y:0.3,w:2,h:1.5,'
                    f'fontSize:96,color:"{acc}",fontFace:"Georgia",bold:true}});'
                    f'sl.addText("{quote}",{{x:0.8,y:1.1,w:8.5,h:3.0,'
                    f'fontSize:22,color:"{txt}",fontFace:"Georgia",'
                    f'italic:true,valign:"middle"}});'
                    f'sl.addText("\\u2014 {auth}",{{x:0.8,y:4.3,w:8.5,h:0.6,'
                    f'fontSize:15,color:"{sub}",fontFace:"Calibri"}});}}'
                )

            elif stype == "conclusion":
                ba = bullet_arr(s.get("bullets",[]))
                js = (
                    f'{{let sl=pres.addSlide();'
                    f'sl.background={{color:"{bg}"}};'
                    f'sl.addShape(pres.shapes.RECTANGLE,'
                    f'{{x:0,y:0,w:10,h:0.12,'
                    f'fill:{{color:"{acc}"}},line:{{color:"{acc}"}}}});'
                    f'sl.addShape(pres.shapes.RECTANGLE,'
                    f'{{x:0,y:5.5,w:10,h:0.125,'
                    f'fill:{{color:"{acc}"}},line:{{color:"{acc}"}}}});'
                    f'sl.addText("{st_}",{{x:0.4,y:0.18,w:9.2,h:0.85,'
                    f'fontSize:28,bold:true,color:"{txt}",'
                    f'fontFace:"Georgia",valign:"middle"}});'
                    f'sl.addShape(pres.shapes.RECTANGLE,'
                    f'{{x:0.4,y:1.1,w:9.2,h:3.9,'
                    f'fill:{{color:"{card}"}},line:{{color:"{acc}",pt:1}}}});'
                    f'sl.addText({ba},{{x:0.6,y:1.2,w:8.8,h:3.7,'
                    f'fontFace:"Calibri",valign:"top"}});'
                    f'{ftr}}}'
                )

            else:
                items = s.get("bullets",[s.get("body","")])
                ba    = bullet_arr([x for x in items if x])
                js = (
                    f'{{let sl=pres.addSlide();'
                    f'sl.background={{color:"{bg}"}};'
                    f'{hdr(st_)}'
                    f'sl.addText({ba},{{x:0.6,y:1.28,w:8.8,h:4.1,'
                    f'fontFace:"Calibri",valign:"top"}});'
                    f'{ftr}}}'
                )

            slides_js.append(js)

        # ── Write & run Node.js ────────────────────────────────
        pptx_path  = "/tmp/output_pres.pptx"
        js_path    = "/tmp/make_pres.js"
        pptx_title = esc(plan.get("title","Presentation"))

        js_code = (
            'const pptxgen=require("pptxgenjs");'
            'let pres=new pptxgen();'
            'pres.layout="LAYOUT_16x9";'
            f'pres.title="{pptx_title}";'
            + "".join(slides_js) +
            f'pres.writeFile({{fileName:"{pptx_path}"}}).then(()=>console.log("OK")).catch(e=>{{console.error(e);process.exit(1);}});'
        )

        with open(js_path,"w") as f:
            f.write(js_code)

        show_progress("⚙️ Generating PPTX file…", 88)

        result = subprocess.run(
            ["node", js_path],
            capture_output=True, text=True, timeout=120
        )

        if result.returncode != 0:
            st.error("PPTX generation failed.")
            st.code(result.stderr[:1500])
            st.stop()

        show_progress("✅ Done!", 100)

        with open(pptx_path,"rb") as f:
            pptx_bytes = f.read()

        status_el.empty()
        prog_el.empty()

        # ── Success ────────────────────────────────────────────
        n = len(plan.get("slides",[]))
        st.markdown(
            f'<div class="success-box">'
            f'<div style="font-size:3rem">🎉</div>'
            f'<div class="success-title">Presentation Ready!</div>'
            f'<div class="success-sub">'
            f'{n} slides · {selected_theme} · {len(pptx_bytes)//1024} KB'
            f'</div></div>',
            unsafe_allow_html=True
        )

        safe_name = re.sub(
            r"[^a-zA-Z0-9_\- ]","",
            plan.get("title","presentation")
        )[:40].strip().replace(" ","_")

        st.download_button(
            "⬇️  Download PowerPoint (.pptx)",
            data=pptx_bytes,
            file_name=f"{safe_name}.pptx",
            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            use_container_width=True,
        )

        with st.expander("📋 View all slide content"):
            for s in plan.get("slides",[]):
                st.markdown(
                    f"**Slide {s.get('slide_num')} — "
                    f"{s.get('title')}** `{s.get('type')}`"
                )
                for b in s.get("bullets",[]): st.markdown(f"  - {b}")
                for x in s.get("stats",[]): st.markdown(f"  - **{x['value']}** — {x['label']}")
                if s.get("body"): st.markdown(f"  *{s['body']}*")
                st.markdown("---")

    except json.JSONDecodeError as e:
        st.error(f"Could not parse AI response as JSON: {e}")
        with st.expander("Raw Gemini response"):
            try: st.code(raw_text[:3000])
            except: st.write("No response captured.")
    except ValueError as e:
        st.error(str(e))
    except subprocess.TimeoutExpired:
        st.error("Timed out. Try with fewer slides.")
    except FileNotFoundError:
        st.error("Node.js not found. Make sure packages.txt has 'nodejs' and 'npm'.")
    except Exception as e:
        st.error(f"Unexpected error: {e}")
        import traceback
        st.code(traceback.format_exc())
