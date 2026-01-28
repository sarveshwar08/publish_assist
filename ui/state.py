import streamlit as st


def get_state(key, default=None):
    if key not in st.session_state:
        st.session_state[key] = default
    return st.session_state[key]


def set_state(key, value):
    st.session_state[key] = value
