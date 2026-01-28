import hashlib
import streamlit as st
from api_client import get_datasets
from state import set_state

st.header("👤 Identify User")

name = st.text_input("Full name")

if st.button("Continue", disabled=not name):
    user_id = hashlib.md5(name.encode()).hexdigest()
    set_state("user_id", user_id)
    set_state("user_name", name)

    datasets = get_datasets(user_id)
    set_state("datasets", datasets)

    st.switch_page("pages/2_ingest.py")
