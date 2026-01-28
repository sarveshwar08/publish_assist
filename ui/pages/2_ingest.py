import streamlit as st
from api_client import start_ingest
from state import get_state, set_state

st.header("📥 Dataset Setup")

datasets = get_state("datasets", [])
user_name = get_state("user_name")

if datasets:
    st.subheader("Existing datasets found")
    latest = datasets[0]

    if st.button("Use latest dataset"):
        set_state("dataset_id", latest["id"])
        st.switch_page("pages/4_generate.py")

    st.divider()

st.subheader("Create new dataset")

substack = st.text_input("Substack username (optional)")
medium = st.text_input("Medium username (optional)")
youtube = st.text_input("YouTube handle (optional)")

if st.button("Start ingestion"):
    payload = {
        "user_full_name": user_name,
        "substack_username": substack or None,
        "medium_username": medium or None,
        "youtube_handle": youtube or None,
    }

    resp = start_ingest(payload)
    set_state("job_id", resp["job_id"])
    set_state("job_type", "INGEST")
    set_state("dataset_id", resp["dataset_id"])

    st.switch_page("pages/3_job_status.py")
