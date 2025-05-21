# api_logic/gemini_api.py

import os
import re
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
BASE = "https://generativelanguage.googleapis.com/v1beta/models"


def process_pdf_with_gemini(pdf_text: str) -> str:
    """
    Extract a numbered list of courses from the transcript text using Gemini Flash.
    """
    if not API_KEY:
        return pdf_text

    url = f"{BASE}/gemini-2.0-flash:generateContent?key={API_KEY}"
    prompt = (
        "Extract a numbered list of course codes and names from the following transcript text. "
        "Respond with only the list (no additional sentences or headings):\n\n"
        f"{pdf_text}"
    )
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }
    headers = {"Content-Type": "application/json"}

    resp = requests.post(url, headers=headers, json=payload, timeout=60)
    if resp.status_code != 200:
        # return the raw error for debugging
        return f"Gemini Error ({resp.status_code}): {resp.text}"

    data = resp.json().get("candidates", [])
    if not data:
        return "Gemini returned no candidates."

    raw = data[0]["content"]["parts"][0]["text"]

    # drop everything before "1."
    lines = raw.splitlines()
    for i, line in enumerate(lines):
        if re.match(r'^\s*1\.\s+', line):
            return "\n".join(lines[i:]).strip()

    return raw.strip()


def process_with_gemini(prompt: str) -> str:
    """
    Send a prompt to Gemini Flash to get a text answer.
    """
    if not API_KEY:
        return "Error: Gemini API key not configured"

    url = f"{BASE}/gemini-2.0-flash:generateContent?key={API_KEY}"
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }
    headers = {"Content-Type": "application/json"}

    resp = requests.post(url, headers=headers, json=payload, timeout=90)
    if resp.status_code != 200:
        return f"Gemini Error ({resp.status_code}): {resp.text}"

    data = resp.json().get("candidates", [])
    if not data:
        return "Gemini returned no candidates."

    return data[0]["content"]["parts"][0]["text"].strip()
