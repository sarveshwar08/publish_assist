import requests
import os

API_BASE = os.getenv("API_BASE", "http://localhost:8000/v1")


def get_datasets(user_id: str):
    r = requests.get(f"{API_BASE}/datasets", params={"user_id": user_id})
    r.raise_for_status()
    return r.json()


def start_ingest(payload: dict):
    r = requests.post(f"{API_BASE}/ingest", json=payload)
    r.raise_for_status()
    return r.json()


def get_job(job_id: str):
    r = requests.get(f"{API_BASE}/jobs/{job_id}")
    r.raise_for_status()
    return r.json()


def generate_content(payload: dict):
    r = requests.post(f"{API_BASE}/generate", json=payload)
    r.raise_for_status()
    return r.json()
