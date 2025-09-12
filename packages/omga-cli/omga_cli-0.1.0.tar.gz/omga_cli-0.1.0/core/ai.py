import os
import time
import requests
from core.cache_db import get, set_
from core.logger import logger

API_KEY = "tpsg-1Yu7qcOGfBJMLbKYBAfh3SbOZrHX47Y"
BASE_URL = "https://api.metisai.ir/v1beta"

class MetisClient:
    def __init__(self, model='gemini-2.0-flash', timeout=20):
        self.model = model
        self.timeout = timeout
        self.headers = {
            "x-goog-api-key": API_KEY,
            "Content-Type": "application/json"
        }

    def generate(self, prompt, max_tokens=1024, temperature=0.7):
        cached = get(prompt)
        if cached:
            return cached

        payload = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens}
        }

        attempts = 0
        while attempts < 3:
            try:
                response = requests.post(
                    f"{BASE_URL}/models/{self.model}:generateContent",
                    json=payload,
                    headers=self.headers,
                    timeout=self.timeout
                )
                response.raise_for_status()
                data = response.json()
                text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "").strip()
                set_(prompt, text)
                return text
            except requests.RequestException as e:
                attempts += 1
                delay = min(2 ** attempts, 4)
                logger.warning(f"Metis API error, retry {attempts}/3: {e}, sleeping {delay}s")
                time.sleep(delay)
                if attempts == 3:
                    logger.error(f"Metis API failed after retries: {e}")
                    raise

def ask(prompt: str) -> str:
    client = MetisClient()
    return client.generate(prompt)
