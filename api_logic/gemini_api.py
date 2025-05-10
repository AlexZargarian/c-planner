# api_logic/gemini_api.py

import os
import re
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

def process_pdf_with_gemini(pdf_text: str) -> str:
    """
    Call Gemini’s gemini-2.0-flash to extract a numbered list of courses.
    Then remove any preamble so only the list remains.
    """
    if not API_KEY:
        return pdf_text

    url = (
        "https://generativelanguage.googleapis.com/v1beta/"
        f"models/gemini-2.0-flash:generateContent?key={API_KEY}"
    )
    prompt = (
        "Extract a numbered list of course codes and names from the following transcript text. "
        "Respond with only the list (no additional sentences or headings):\n\n"
        f"{pdf_text}"
    )
    payload = {
        "contents": [ { "parts": [ { "text": prompt } ] } ],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 1024
        }
    }
    headers = { "Content-Type": "application/json" }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        candidates = data.get("candidates", [])
        if not candidates:
            raise ValueError("No candidates in response")

        # get raw text
        content = candidates[0].get("content", {})
        parts   = content.get("parts", [])
        raw     = parts[0].get("text", "") if parts else ""

        # --- CLEANUP: drop everything before the first “1.” line ---
        lines = raw.splitlines()
        for i, line in enumerate(lines):
            if re.match(r'^\s*1\.\s+', line):
                clean = lines[i:]
                return "\n".join(clean).strip()

        # if no “1.” found, just return raw
        return raw.strip()

    except Exception:
        return pdf_text.strip()
