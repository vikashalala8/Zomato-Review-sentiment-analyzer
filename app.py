import json
import re
import html
import hashlib
from io import BytesIO

import requests
import pandas as pd
import streamlit as st

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
)


# ============================================================
# 1. PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Zomato / Swiggy Review Analyser",
    page_icon="🍽️",
    layout="wide",
)

OLLAMA_CHAT_URL = "http://localhost:11434/api/chat"


# ============================================================
# 2. CUSTOM CSS
# ============================================================

st.html("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Manrope:wght@500;600;700;800&display=swap');

:root {
    --page: #f5f7fc;
    --surface: #ffffff;
    --surface-soft: #f8faff;
    --ink: #172033;
    --muted: #64748b;
    --line: #e3e8f2;
    --purple: #6558d3;
    --purple-dark: #4e43b5;
    --blue: #3478d4;
    --green: #16865b;
    --red: #c74747;
    --amber: #a66a0a;
}

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif !important;
}
.stApp {
    background: var(--page) !important;
    color: var(--ink) !important;
}
[data-testid="stAppViewContainer"] {
    background: var(--page) !important;
}
[data-testid="stHeader"] {
    background: rgba(245,247,252,0.96) !important;
}
.block-container {
    max-width: 1220px;
    padding-top: 2rem !important;
    padding-bottom: 4rem !important;
}
h1, h2, h3, h4, h5, h6,
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li,
[data-testid="stCaptionContainer"],
label, .stText, p {
    color: var(--ink);
}
h1, h2, h3 {
    font-family: 'Manrope', sans-serif !important;
    font-weight: 800 !important;
    letter-spacing: -0.45px;
}
h2 { font-size: 1.45rem !important; margin-top: 1.35rem !important; }
h3 { font-size: 1.08rem !important; }
small, [data-testid="stCaptionContainer"] {
    color: var(--muted) !important;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: #ffffff !important;
    border-right: 1px solid var(--line);
}
[data-testid="stSidebar"] > div {
    background: #ffffff !important;
}
[data-testid="stSidebar"] * {
    color: var(--ink);
}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: #202944 !important;
}
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
    color: #53627a !important;
}

/* Hero */
.hero {
    position: relative;
    overflow: hidden;
    text-align: left;
    padding: 38px 42px;
    margin: 6px 0 30px;
    border: 1px solid #e2e5fb;
    border-radius: 24px;
    background:
        radial-gradient(circle at 90% 15%, rgba(255,255,255,.24), transparent 27%),
        linear-gradient(115deg, #4f46b9 0%, #6558d3 48%, #3478d4 100%);
    box-shadow: 0 16px 38px rgba(68, 79, 160, .15);
}
.hero-title {
    font-family: 'Manrope', sans-serif;
    font-size: clamp(28px, 4vw, 42px);
    line-height: 1.16;
    font-weight: 800;
    color: #ffffff !important;
    letter-spacing: -1.2px;
    margin: 12px 0 10px;
}
.hero-subtitle {
    max-width: 760px;
    font-size: 15px;
    line-height: 1.7;
    color: #eef1ff !important;
}
.ai-badge {
    display: inline-block;
    background: rgba(255,255,255,.16);
    color: #ffffff !important;
    padding: 7px 13px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 700;
    border: 1px solid rgba(255,255,255,.3);
}

/* Metric cards */
.metric-box {
    height: 100%;
    min-height: 126px;
    background: var(--surface) !important;
    border: 1px solid var(--line);
    border-radius: 18px;
    padding: 22px 18px;
    text-align: left;
    box-shadow: 0 5px 18px rgba(26, 43, 77, .055);
}
.metric-label {
    color: #66748b !important;
    font-size: 12px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: .7px;
    margin-bottom: 13px;
}
.metric-value {
    color: #172033 !important;
    font-family: 'Manrope', sans-serif;
    font-size: clamp(20px, 2vw, 27px);
    line-height: 1.3;
    font-weight: 800;
    overflow-wrap: anywhere;
}

/* Content cards */
.result-card {
    background: var(--surface) !important;
    border: 1px solid var(--line);
    border-radius: 18px;
    padding: 21px 22px;
    margin: 13px 0;
    color: var(--ink) !important;
    box-shadow: 0 5px 18px rgba(26, 43, 77, .045);
}
.result-title {
    font-family: 'Manrope', sans-serif;
    font-size: 16px;
    font-weight: 800;
    color: #202944 !important;
    margin-bottom: 12px;
}
.result-text {
    color: #43516a !important;
    font-size: 14px;
    line-height: 1.8;
    overflow-wrap: anywhere;
}
.good, .bad, .warn, .info {
    border-radius: 12px;
    padding: 12px 14px;
    margin: 9px 0;
    line-height: 1.65;
    font-size: 13.5px;
    color: #263247 !important;
}
.good { background: #edf9f3; border: 1px solid #ccebd9; }
.bad  { background: #fff1f0; border: 1px solid #f3d1ce; }
.warn { background: #fff8e9; border: 1px solid #f0dfb8; }
.info { background: #eef5ff; border: 1px solid #d3e3fb; }
.small-muted { color: #718096 !important; font-size: 12px; }

/* Upload and data preview */
[data-testid="stFileUploader"] {
    background: #ffffff !important;
    border: 1.5px dashed #a9a3e8 !important;
    border-radius: 17px !important;
    padding: 16px !important;
}
[data-testid="stFileUploader"] * {
    color: #263247 !important;
}
[data-testid="stFileUploaderDropzone"] {
    background: #fafaff !important;
    border: 0 !important;
}
[data-testid="stDataFrame"] {
    background: #ffffff !important;
    border: 1px solid var(--line) !important;
    border-radius: 14px !important;
    overflow: hidden;
}
[data-testid="stMetric"] {
    background: #ffffff !important;
    border: 1px solid var(--line) !important;
    padding: 16px 18px !important;
    border-radius: 16px !important;
    box-shadow: 0 4px 14px rgba(26,43,77,.04);
}
[data-testid="stMetricLabel"],
[data-testid="stMetricValue"] {
    color: var(--ink) !important;
}

/* Form controls */
[data-testid="stSelectbox"] > div > div,
[data-testid="stNumberInput"] input,
[data-testid="stTextInput"] input {
    background: #ffffff !important;
    color: #172033 !important;
    border: 1px solid #d9dfeb !important;
    border-radius: 10px !important;
}
[data-testid="stSelectbox"] svg {
    fill: #52617a !important;
}
[data-testid="stSlider"] [data-testid="stTickBar"] {
    color: #64748b !important;
}
[data-testid="stExpander"] {
    background: #ffffff !important;
    border: 1px solid var(--line) !important;
    border-radius: 14px !important;
}
[data-testid="stExpander"] summary,
[data-testid="stExpander"] summary p {
    color: #263247 !important;
}
[data-testid="stAlert"] {
    border-radius: 13px !important;
}
hr {
    border-color: var(--line) !important;
}

/* Buttons */
.stButton button, .stDownloadButton button {
    border: 0 !important;
    border-radius: 11px !important;
    min-height: 44px;
    background: linear-gradient(100deg, #5c55c9, #397ed2) !important;
    color: #ffffff !important;
    font-weight: 700 !important;
    box-shadow: 0 6px 16px rgba(83, 91, 193, .16);
    transition: transform .15s ease, filter .15s ease;
}
.stButton button:hover, .stDownloadButton button:hover {
    filter: brightness(1.06);
    transform: translateY(-1px);
}
.stButton button p, .stDownloadButton button p {
    color: #ffffff !important;
}

/* Status and code readability */
[data-testid="stAlert"] p {
    color: inherit !important;
}
[data-testid="stCode"] {
    border-radius: 12px;
}
</style>
""")


# ============================================================
# 3. OLLAMA CONNECTION AND JSON HELPERS
# ============================================================

def check_ollama_running():
    try:
        response = requests.get("http://localhost:11434", timeout=3)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


def extract_json(text):
    """Parse JSON returned by Ollama, including a JSON object in surrounding text."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        return json.loads(match.group())

    raise ValueError("Ollama did not return valid JSON. Try a lower temperature.")


def normalize_sentiment(result):
    """
    Keep exactly one sentiment label.
    Prefer the model's label; infer a fallback only if it is invalid.
    """
    raw = str(result.get("overall_sentiment", "")).strip().lower()

    allowed = {
        "positive": "Positive",
        "negative": "Negative",
        "neutral": "Neutral",
        "mixed": "Mixed",
    }

    # Accept a response containing one valid label, but not a list of all labels.
    if raw in allowed:
        result["overall_sentiment"] = allowed[raw]
        return result

    # If model returns extra text, accept only an unambiguous single label.
    found = [label for label in allowed if re.search(rf"\b{label}\b", raw)]
    if len(found) == 1:
        result["overall_sentiment"] = allowed[found[0]]
        return result

    # Last-resort fallback based on the actual review analysis rating.
    try:
        rating = float(result.get("estimated_rating_out_of_5", 3))
        if rating >= 3.8:
            sentiment = "Positive"
        elif rating <= 2.2:
            sentiment = "Negative"
        else:
            sentiment = "Neutral"
    except (ValueError, TypeError):
        sentiment = "Neutral"

    result["overall_sentiment"] = sentiment
    return result


# ============================================================
# 4. OLLAMA DATA-SPECIFIC ANALYSIS
# ============================================================

def analyse_reviews_ollama(
    records,
    output_language,
    model_name,
    temperature,
):
    """
    Analyse only the records passed from the currently uploaded CSV.
    Each record can include review text, rating and restaurant name.
    """

    actual_data = json.dumps(records, ensure_ascii=False, indent=2)

    system_prompt = """
You are a careful restaurant customer-feedback analyst.

Analyse ONLY the customer records supplied in the user's message.
Every finding must be supported by those records.

Rules:
- Do not invent reviews, restaurants, ratings, complaints or praise.
- Do not reuse generic findings from another dataset.
- Distinguish what the records show from what cannot be determined.
- If a theme occurs only once, do not describe it as a frequent pattern.
- Use the supplied customer rating field if it exists, but do not confuse
  it with the model's estimated rating.
- Return exactly one sentiment label: Positive, Negative, Neutral, or Mixed.
- Return valid JSON only. No Markdown or text outside JSON.
"""

    user_prompt = f"""
Analyse this uploaded CSV selection.

The records below are the actual data selected by the user.
Base the report on these records only.

ACTUAL CSV RECORDS:
{actual_data}

Return one JSON object with exactly these fields:

{{
  "overall_sentiment": "Positive",
  "estimated_rating_out_of_5": 3.5,
  "one_line_verdict": "A short verdict based on these records",
  "summary": "A specific summary of what these records show",
  "top_positives": ["Data-supported positive finding"],
  "top_negatives": ["Data-supported negative finding"],
  "customer_pain_points": ["Data-supported customer problem"],
  "business_suggestions": ["Practical suggestion linked to a finding"],
  "best_for": ["Only if supported by the records"],
  "keywords": ["Actual theme or keyword"],
  "review_evidence": [
    {{
      "observation": "A finding supported by the selected records",
      "example": "A short exact phrase copied from a supplied review"
    }}
  ]
}}

Sentiment instructions:
- Positive: positive experiences clearly dominate.
- Negative: negative experiences clearly dominate.
- Neutral: mostly factual, balanced, or neither positive nor negative.
- Mixed: meaningful positive and negative experiences both appear.
- Select exactly ONE label. Never output all four choices.

Rating instructions:
- Return one numeric estimate from 0 to 5.
- Base it on the sentiment in these selected reviews.
- It is an AI estimate, not an official platform rating.

Evidence instructions:
- Use short exact snippets from the supplied review text.
- Do not create example quotations.
- If there is no suitable evidence, return an empty list.

Output language: {output_language}
"""

    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "stream": False,
        "format": "json",
        "options": {
            "temperature": temperature,
            "num_ctx": 8192,
            "num_predict": 1800,
        },
    }

    response = requests.post(
        OLLAMA_CHAT_URL,
        json=payload,
        timeout=300,
    )
    response.raise_for_status()

    raw_text = response.json()["message"]["content"]
    result = extract_json(raw_text)

    return normalize_sentiment(result)


# ============================================================
# 5. HTML DISPLAY HELPERS
# ============================================================

def safe_text(value):
    return html.escape(str(value))


def display_metric(label, value):
    st.html(f"""
    <div class="metric-box">
        <div class="metric-label">{safe_text(label)}</div>
        <div class="metric-value">{safe_text(value)}</div>
    </div>
    """)


def display_text_card(title, content):
    st.html(f"""
    <div class="result-card">
        <div class="result-title">{safe_text(title)}</div>
        <div class="result-text">{safe_text(content)}</div>
    </div>
    """)


def display_card(title, items, css_class):
    content = ""

    if not isinstance(items, list):
        items = []

    for item in items:
        content += f'<div class="{css_class}">{safe_text(item)}</div>'

    if not content:
        content = '<p class="small-muted">No findings available in the selected records.</p>'

    st.html(f"""
    <div class="result-card">
        <div class="result-title">{safe_text(title)}</div>
        {content}
    </div>
    """)


# ============================================================
# 6. PDF REPORT GENERATION
# ============================================================

def create_pdf_report(result, review_count, file_name):
    """Create a downloadable PDF containing the complete analysis."""

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=42,
        leftMargin=42,
        topMargin=42,
        bottomMargin=42,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        fontSize=19,
        leading=24,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#1F2937"),
        spaceAfter=12,
    )

    heading_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontSize=13,
        leading=17,
        textColor=colors.HexColor("#1D4ED8"),
        spaceBefore=13,
        spaceAfter=7,
    )

    body_style = ParagraphStyle(
        "ReportBody",
        parent=styles["BodyText"],
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor("#222222"),
        spaceAfter=6,
    )

    small_style = ParagraphStyle(
        "SmallText",
        parent=styles["BodyText"],
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#555555"),
    )

    story = []

    def paragraph_text(value):
        return html.escape(str(value)).replace("\n", "<br/>")

    def add_section(title, items):
        story.append(Paragraph(paragraph_text(title), heading_style))

        if not isinstance(items, list) or not items:
            story.append(Paragraph("No findings available.", body_style))
            return

        for item in items:
            story.append(Paragraph("&#8226; " + paragraph_text(item), body_style))

    story.append(
        Paragraph("Zomato / Swiggy Review Analysis Report", title_style)
    )
    story.append(
        Paragraph(f"Source CSV: {paragraph_text(file_name)}", small_style)
    )
    story.append(
        Paragraph(f"Customer reviews analysed: {review_count}", small_style)
    )
    story.append(Spacer(1, 14))

    sentiment = result.get("overall_sentiment", "N/A")
    rating = result.get("estimated_rating_out_of_5", "N/A")

    metric_data = [
        ["Overall Sentiment", "AI Estimated Rating"],
        [paragraph_text(sentiment), paragraph_text(f"{rating}/5")],
    ]

    metric_table = Table(
        metric_data,
        colWidths=[3.25 * inch, 3.25 * inch],
    )
    metric_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DBEAFE")),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#111827")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("PADDING", (0, 0), (-1, -1), 10),
        ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor("#CBD5E1")),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
    ]))
    story.append(metric_table)
    story.append(Spacer(1, 12))

    story.append(Paragraph("Overall Verdict", heading_style))
    story.append(
        Paragraph(
            paragraph_text(result.get("one_line_verdict", "N/A")),
            body_style,
        )
    )

    story.append(Paragraph("Executive Summary", heading_style))
    story.append(
        Paragraph(paragraph_text(result.get("summary", "N/A")), body_style)
    )

    add_section("Top Positives", result.get("top_positives", []))
    add_section("Top Negatives", result.get("top_negatives", []))
    add_section("Customer Pain Points", result.get("customer_pain_points", []))
    add_section("Business Suggestions", result.get("business_suggestions", []))
    add_section("Best For", result.get("best_for", []))
    add_section("Important Keywords", result.get("keywords", []))

    story.append(Paragraph("Evidence from Customer Reviews", heading_style))

    evidence = result.get("review_evidence", [])
    if evidence:
        for item in evidence:
            if not isinstance(item, dict):
                continue

            observation = paragraph_text(item.get("observation", ""))
            example = paragraph_text(item.get("example", ""))

            story.append(
                Paragraph(f"<b>Observation:</b> {observation}", body_style)
            )
            story.append(
                Paragraph(f"<b>Review example:</b> &quot;{example}&quot;", body_style)
            )
    else:
        story.append(
            Paragraph("No review evidence was returned by the model.", body_style)
        )

    story.append(Spacer(1, 14))
    story.append(HRFlowable(width="100%", color=colors.HexColor("#CBD5E1")))
    story.append(Spacer(1, 6))
    story.append(
        Paragraph(
            "Generated locally using Ollama AI. The estimated rating and "
            "analysis are AI-generated interpretations of the selected records.",
            small_style,
        )
    )

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


# ============================================================
# 7. SIDEBAR
# ============================================================

with st.sidebar:
    st.title("🍽️ Review Analyser")
    st.caption("AI School of India — Module 1 Project")

    model_name = st.selectbox(
        "Ollama Model",
        ["qwen2.5:3b", "llama3.2:1b", "llama3.2", "mistral"],
        index=0,
    )

    output_language = st.selectbox(
        "Output Language",
        ["English", "Telugu", "Tenglish"],
        index=0,
    )

    temperature = st.slider(
        "Temperature",
        min_value=0.0,
        max_value=1.0,
        value=0.2,
        step=0.1,
        help="Lower values generally give more consistent structured output.",
    )

    if st.button("Clear Result"):
        st.session_state.pop("analysis_result", None)
        st.session_state.pop("analysis_key", None)
        st.rerun()

    st.markdown("---")
    st.markdown("### Setup Commands")
    st.code(
        "ollama pull qwen2.5:3b\n"
        "python -m streamlit run app.py",
        language="bash",
    )


# ============================================================
# 8. MAIN HEADER
# ============================================================

st.html("""
<div class="hero">
    <div class="ai-badge">✦ AI-POWERED CUSTOMER INSIGHTS</div>
    <div class="hero-title">Restaurant Review Intelligence</div>
    <div class="hero-subtitle">
        Understand what customers love, identify service gaps, and turn
        real customer feedback into practical business improvements.
    </div>
</div>
""")


# ============================================================
# 9. CHECK OLLAMA
# ============================================================

if not check_ollama_running():
    st.error("Ollama is not running.")
    st.info("Ollama may already be running in another terminal. If not, open PowerShell and run:")
    st.code("ollama serve")
    st.stop()


# ============================================================
# 10. CSV UPLOAD AND FILE CHANGE DETECTION
# ============================================================

st.markdown("## 1. Upload your dataset")

st.caption("Upload a CSV with written customer reviews. Rating and restaurant-name columns are optional.")

uploaded_file = st.file_uploader(
    "Choose a customer reviews CSV file",
    type=["csv"],
    key="csv_uploader",
)

if uploaded_file is None:
    st.info("Upload a CSV file to begin the analysis.")
    st.stop()

file_bytes = uploaded_file.getvalue()
file_hash = hashlib.sha256(file_bytes).hexdigest()

# Remove old results immediately when a different CSV is uploaded.
if st.session_state.get("current_file_hash") != file_hash:
    st.session_state.pop("analysis_result", None)
    st.session_state.pop("analysis_key", None)
    st.session_state["current_file_hash"] = file_hash

try:
    try:
        df = pd.read_csv(BytesIO(file_bytes))
    except UnicodeDecodeError:
        df = pd.read_csv(BytesIO(file_bytes), encoding="latin1")
except Exception as exc:
    st.error(f"Could not read the CSV file: {exc}")
    st.stop()

if df.empty or len(df.columns) == 0:
    st.error("The uploaded CSV is empty.")
    st.stop()


# ============================================================
# 11. DATASET INFORMATION AND PREVIEW
# ============================================================

st.success("CSV uploaded successfully!")

st.markdown("### Dataset overview")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Records", len(df))
with col2:
    st.metric("Total Columns", len(df.columns))
with col3:
    st.metric("Missing Values", int(df.isna().sum().sum()))

st.markdown("### Data preview")
st.dataframe(df.head(10), use_container_width=True)


# ============================================================
# 12. COLUMN SELECTION
# ============================================================

def find_column(possible_names):
    for column in df.columns:
        if str(column).strip().lower() in possible_names:
            return column
    return None


default_review = find_column({
    "review", "reviews", "review_text", "text",
    "comment", "content", "customer_review"
})

default_rating = find_column({
    "rating", "rate", "stars", "customer_rating"
})

default_restaurant = find_column({
    "restaurant", "restaurant_name", "name", "business_name"
})

st.markdown("## 2. Choose your columns")

review_options = ["-- Select Review Column --"] + df.columns.tolist()
review_index = (
    df.columns.tolist().index(default_review) + 1
    if default_review is not None else 0
)

review_column = st.selectbox(
    "Customer Review Column",
    review_options,
    index=review_index,
)

if review_column == "-- Select Review Column --":
    st.warning("Please select the column containing actual written customer reviews.")
    st.stop()

rating_options = ["None"] + df.columns.tolist()
rating_index = (
    df.columns.tolist().index(default_rating) + 1
    if default_rating is not None else 0
)

rating_column = st.selectbox(
    "Customer Rating Column (Optional)",
    rating_options,
    index=rating_index,
)

restaurant_options = ["None"] + df.columns.tolist()
restaurant_index = (
    df.columns.tolist().index(default_restaurant) + 1
    if default_restaurant is not None else 0
)

restaurant_column = st.selectbox(
    "Restaurant Name Column (Optional)",
    restaurant_options,
    index=restaurant_index,
)


# ============================================================
# 13. VALIDATE AND SELECT REVIEWS
# ============================================================

valid_df = df[df[review_column].notna()].copy()
valid_df[review_column] = valid_df[review_column].astype(str).str.strip()
valid_df = valid_df[valid_df[review_column] != ""]

total_reviews = len(valid_df)

if total_reviews == 0:
    st.error("No non-empty customer reviews were found in the selected column.")
    st.stop()

st.markdown("## 3. Configure analysis")

max_reviews = st.number_input(
    "Number of reviews to analyse",
    min_value=1,
    max_value=total_reviews,
    value=min(20, total_reviews),
    step=1,
)

selected_df = valid_df.head(int(max_reviews)).copy()

st.info(
    f"Available reviews: {total_reviews} | "
    f"Selected reviews: {len(selected_df)}"
)

with st.expander("View selected records"):
    st.dataframe(selected_df, use_container_width=True)


# ============================================================
# 14. BUILD ACTUAL RECORDS FOR OLLAMA
# ============================================================

records = []

for row_number, (_, row) in enumerate(selected_df.iterrows(), start=1):
    record = {
        "row_id": row_number,
        "customer_review": str(row[review_column]),
    }

    if rating_column != "None" and pd.notna(row[rating_column]):
        record["customer_rating"] = str(row[rating_column])

    if restaurant_column != "None" and pd.notna(row[restaurant_column]):
        record["restaurant_name"] = str(row[restaurant_column])

    records.append(record)


# ============================================================
# 15. UNIQUE ANALYSIS KEY
# ============================================================

analysis_signature = {
    "file_hash": file_hash,
    "review_column": review_column,
    "rating_column": rating_column,
    "restaurant_column": restaurant_column,
    "max_reviews": int(max_reviews),
    "model": model_name,
    "language": output_language,
    "temperature": temperature,
}

analysis_key = hashlib.sha256(
    json.dumps(analysis_signature, sort_keys=True).encode("utf-8")
).hexdigest()


# ============================================================
# 16. RUN ANALYSIS
# ============================================================

analyse_button = st.button(
    "🚀 Analyse Uploaded Dataset",
    use_container_width=True,
)

if analyse_button:
    with st.spinner(
        f"Ollama is analysing {len(records)} selected customer reviews..."
    ):
        try:
            result = analyse_reviews_ollama(
                records=records,
                output_language=output_language,
                model_name=model_name,
                temperature=temperature,
            )

            st.session_state["analysis_result"] = result
            st.session_state["analysis_key"] = analysis_key
            st.session_state["analysed_count"] = len(records)
            st.session_state["analysed_file_name"] = uploaded_file.name

            st.success("Dataset-specific analysis completed!")

        except requests.exceptions.Timeout:
            st.error("Ollama timed out. Try analysing fewer reviews.")

        except requests.exceptions.RequestException as exc:
            st.error(f"Ollama connection error: {exc}")

        except Exception as exc:
            st.error(f"Analysis error: {exc}")


# ============================================================
# 17. DISPLAY RESULTS ONLY FOR CURRENT DATA AND SETTINGS
# ============================================================

if (
    "analysis_result" in st.session_state
    and st.session_state.get("analysis_key") == analysis_key
):
    result = st.session_state["analysis_result"]
    analysed_count = st.session_state.get("analysed_count", 0)

    st.markdown("---")
    st.markdown("## 4. Analysis report")
    st.caption(f"Based on {analysed_count:,} actual records from {st.session_state.get('analysed_file_name', 'your CSV')}.")

    # One sentiment only
    sentiment = result.get("overall_sentiment", "Neutral")

    c1, c2, c3 = st.columns(3)

    with c1:
        display_metric("Overall Sentiment", sentiment)

    with c2:
        display_metric(
            "Estimated Rating",
            f'{result.get("estimated_rating_out_of_5", "N/A")}/5',
        )

    with c3:
        display_metric(
            "Verdict",
            result.get("one_line_verdict", "N/A"),
        )

    display_text_card(
        "🧾 Dataset-Specific Summary",
        result.get("summary", "No summary available."),
    )

    left, right = st.columns(2)

    with left:
        display_card(
            "✅ Top Positives",
            result.get("top_positives", []),
            "good",
        )
        display_card(
            "🔑 Keywords",
            result.get("keywords", []),
            "info",
        )

    with right:
        display_card(
            "❌ Top Negatives",
            result.get("top_negatives", []),
            "bad",
        )
        display_card(
            "👥 Best For",
            result.get("best_for", []),
            "info",
        )

    display_card(
        "😟 Customer Pain Points",
        result.get("customer_pain_points", []),
        "warn",
    )

    display_card(
        "💡 Business Suggestions",
        result.get("business_suggestions", []),
        "info",
    )

    # Evidence from actual reviews
    st.markdown("### 🔍 Evidence from Uploaded Reviews")

    evidence = result.get("review_evidence", [])

    if evidence:
        for item in evidence:
            if isinstance(item, dict):
                observation = item.get("observation", "")
                example = item.get("example", "")

                display_text_card(
                    observation,
                    f'Review example: "{example}"',
                )
    else:
        st.info("No review evidence was returned by the model.")

    # PDF download
    st.markdown("---")

    try:
        pdf_data = create_pdf_report(
            result=result,
            review_count=analysed_count,
            file_name=st.session_state.get("analysed_file_name", "uploaded.csv"),
        )

        st.download_button(
            label="📄 Download Analysis Report (PDF)",
            data=pdf_data,
            file_name="Zomato_Review_Analysis_Report.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

    except Exception as exc:
        st.error(f"Could not generate PDF report: {exc}")

    # Optional JSON download
    st.download_button(
        label="⬇️ Download Analysis as JSON",
        data=json.dumps(result, indent=2, ensure_ascii=False),
        file_name="restaurant_review_analysis.json",
        mime="application/json",
        use_container_width=True,
    )
