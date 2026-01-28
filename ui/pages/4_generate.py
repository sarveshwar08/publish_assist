import streamlit as st
from api_client import generate_content
from state import get_state, set_state

st.header("✍️ Generate Content")

dataset_id = get_state("dataset_id")

topic = st.text_input("Topic")
platform = st.selectbox(
    "Platform",
    ["linkedin", "substack", "youtube"]
)
tone = st.selectbox(
    "Tone",
    ["informative", "story", "opinion"]
)
use_web = st.checkbox("Use Web Search", value=False)

if st.button("Generate", disabled=not topic):
    payload = {
        "dataset_id": dataset_id,
        "topic": topic,
        "platform": platform,
        "tone": tone,
        "use_web": use_web,
    }

    resp = generate_content(payload)

    debug = resp.get("debug", {}) or {}
    job_id = debug.get("job_id")
    if not job_id:
        st.error("Generation started, but no job_id was returned.")
        st.json(resp)
    else:
        set_state("job_id", job_id)
        set_state("job_type", "GENERATE")
        set_state("last_generate_debug", debug)
        st.switch_page("pages/3_job_status.py")
