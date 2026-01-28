import time
import streamlit as st
from api_client import get_job
from state import get_state

job_type = (get_state("job_type") or "INGEST").upper()

if job_type == "GENERATE":
    st.header("⏳ Generation Progress")
else:
    st.header("⏳ Ingesting and extracting Features")

job_id = get_state("job_id")

job = get_job(job_id)

status = job.get("status", "queued")
progress_map = {
    "queued": 0,
    "running": 50,
    "completed": 100,
    "failed": 0
}
percent = progress_map.get(status.lower(), 0)

stage = job.get("progress", {}).get("stage", "Unknown")
message = job.get("progress", {}).get("message", "")

if status.lower() == "running":
    if str(stage).lower() == "feature_engineering":
        percent = 75

st.progress(percent)
st.write(f"**Status:** {status}")
st.write(f"**Stage:** {stage}")
st.caption(message)

if status.lower() == "completed":
    if job_type == "INGEST":
        st.success("Dataset ready!")
        time.sleep(1)
        st.switch_page("pages/4_generate.py")
    else:
        result = job.get("result", {}) or {}
        output = result.get("output")
        if output:
            st.success("Generation completed!")
            st.subheader("Generated Output")
            st.markdown(output)
        else:
            st.warning("Job completed, but output is not available yet.")

        with st.expander("Metadata & Debug"):
            st.json(job.get("zenml", {}))
            st.json(job.get("polling", {}))
            st.json(job.get("errors", []))

        if st.button("Generate something else"):
            st.switch_page("pages/4_generate.py")

elif status.lower() == "failed":
    st.error("Job failed")
    if job.get("errors"):
        st.error(f"Error: {job['errors'][0].get('message')}")
else:
    time.sleep(2.5)
    st.rerun()
