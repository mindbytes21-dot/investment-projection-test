"""
Glass-style CSS for the app.

Design rules (also checked by tests/test_app.py):
  * Everything the user reads or types inside a glass panel is BLACK on a light
    translucent surface: inputs, dropdown and its menu, labels, banners, results.
  * Only the page title/subtitle (which sit directly on the dark gradient) are white.
  * No blanket colour rules on bare tags such as div, span or p.
"""

CSS = """
.stApp{
  background:
    radial-gradient(circle at 15% 12%, rgba(60,200,255,.70) 0, transparent 38%),
    radial-gradient(circle at 88% 38%, rgba(255,120,190,.65) 0, transparent 40%),
    radial-gradient(circle at 20% 90%, rgba(140,110,255,.75) 0, transparent 42%),
    radial-gradient(circle at 85% 95%, rgba(255,190,90,.55) 0, transparent 35%),
    linear-gradient(135deg, #2446be 0%, #6e46c8 50%, #e15a96 100%);
  background-attachment: fixed;
}
header[data-testid="stHeader"]{background:transparent}
.block-container{max-width:600px;padding-top:2.5rem}

/* Title sits directly on the dark gradient, so it is white */
.hero h1{color:#fff;font-weight:700;letter-spacing:-.5px;margin:0 0 .25rem;
  text-shadow:0 2px 12px rgba(0,0,40,.45)}
.hero p{color:#fff;margin:0 0 1.2rem;text-shadow:0 1px 8px rgba(0,0,40,.45)}

/* Glass panels */
[data-testid="stForm"], .st-key-lookup{
  background:rgba(255,255,255,.58);
  border:1px solid rgba(255,255,255,.75);
  border-radius:26px;
  padding:1.2rem 1.4rem 1rem;
  backdrop-filter:blur(24px) saturate(160%);
  -webkit-backdrop-filter:blur(24px) saturate(160%);
  box-shadow:0 10px 40px rgba(10,15,60,.35), inset 0 1px 0 rgba(255,255,255,.6);
}
.st-key-lookup{margin-bottom:1rem}

/* Field labels: black */
[data-testid="stWidgetLabel"] p, label p{
  color:#000 !important;font-size:.78rem;font-weight:600;
  letter-spacing:.06em;text-transform:uppercase;
}

/* Text boxes and number boxes: light surface, black text */
div[data-baseweb="input"], div[data-baseweb="base-input"],
[data-testid="stTextInputRootElement"], [data-testid="stNumberInputContainer"]{
  background:rgba(255,255,255,.94) !important;
  border:1px solid rgba(0,0,0,.18) !important;
  border-radius:14px !important;
}
input, textarea{
  color:#000 !important;-webkit-text-fill-color:#000 !important;caret-color:#000 !important;
}
input::placeholder, textarea::placeholder{
  color:rgba(0,0,0,.5) !important;-webkit-text-fill-color:rgba(0,0,0,.5) !important;
}
[data-testid="stNumberInputStepUp"], [data-testid="stNumberInputStepDown"]{
  color:#000 !important;background:transparent !important;
}
[data-testid="stNumberInputStepUp"] svg, [data-testid="stNumberInputStepDown"] svg{
  fill:#000 !important;color:#000 !important;
}

/* Dropdown: selected value, arrow and the opened menu.
   Covers both the older BaseWeb widgets and the newer React-Aria ones. */
div[data-baseweb="select"] > div, [data-testid="stSelectbox"] [role="group"]{
  background:rgba(255,255,255,.94) !important;
  border:1px solid rgba(0,0,0,.18) !important;
  border-radius:14px !important;
}
div[data-baseweb="select"] *, [data-testid="stSelectbox"] input,
[data-testid="stSelectbox"] button{
  color:#000 !important;-webkit-text-fill-color:#000 !important;
}
div[data-baseweb="select"] svg, [data-testid="stSelectbox"] svg{
  fill:#000 !important;color:#000 !important;
}
[data-baseweb="popover"] ul, [data-baseweb="popover"] li,
[data-testid="stSelectboxVirtualDropdown"], [role="listbox"], [role="option"]{
  background:#fff !important;color:#000 !important;
}
[data-baseweb="popover"] li *, [role="option"] *{
  color:#000 !important;-webkit-text-fill-color:#000 !important;
}
[data-baseweb="popover"] li:hover, [data-baseweb="popover"] li[aria-selected="true"],
[role="option"][data-focused="true"], [role="option"][aria-selected="true"]{
  background:#e6f0ff !important;
}

/* Banners (success / error / warning): black text on a light tint */
.banner{
  margin:.6rem 0;padding:.8rem 1rem;border-radius:14px;color:#000;font-weight:500;
  background:rgba(255,255,255,.94);border:1px solid rgba(0,0,0,.12);
  border-left:6px solid #888;
}
.banner.ok{background:#e8f8ee;border-left-color:#1a9c4b}
.banner.err{background:#fdeceb;border-left-color:#d92d20}
.banner.warn{background:#fff4e0;border-left-color:#e08a00}

/* Result panel */
.glass-pill{
  margin:1rem 0;padding:1rem;text-align:center;color:#000;
  background:rgba(255,255,255,.78);border:1px solid rgba(255,255,255,.85);
  border-radius:20px;
  backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);
}
.glass-pill .small{font-size:.75rem;letter-spacing:.08em;color:#000}
.glass-pill .big{font-size:2rem;font-weight:700;color:#000}
.glass-pill .meta{font-size:.8rem;color:#000;opacity:.8}

/* Footnote: black on a light panel */
.note{
  margin-top:1rem;padding:.7rem 1rem;border-radius:14px;font-size:.78rem;color:#000;
  background:rgba(255,255,255,.72);border:1px solid rgba(255,255,255,.85);
}

/* Buttons keep white text on the blue glass */
.stButton > button, .stDownloadButton > button,
[data-testid="stFormSubmitButton"] > button{
  width:100%;border-radius:16px;border:1px solid rgba(255,255,255,.7);
  background:linear-gradient(180deg, rgba(90,175,255,.97), rgba(10,110,235,.97));
  box-shadow:0 6px 20px rgba(10,80,200,.35);padding:.65rem 1rem;
}
.stButton > button p, .stDownloadButton > button p,
[data-testid="stFormSubmitButton"] > button p{
  color:#fff !important;font-weight:600;
}
.stButton > button:hover, .stDownloadButton > button:hover,
[data-testid="stFormSubmitButton"] > button:hover{
  border-color:#fff;filter:brightness(1.08);
}
"""
