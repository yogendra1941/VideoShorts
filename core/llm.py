"""Unified LLM interface supporting Inception Labs (mercury-3), Ollama, Gemini, and OpenAI."""

import json
import logging
import requests
from typing import Optional, Dict, Any

from config import config

logger = logging.getLogger("VideoShorts.LLM")


class LLMClient:
    """Dispatches prompt requests to the configured LLM provider."""

    def __init__(self, provider: Optional[str] = None):
        self.provider = (provider or config.LLM_PROVIDER).lower()

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        json_output: bool = True,
        temperature: float = 0.2,
    ) -> str:
        """Sends prompt to the active LLM provider and returns the raw response text."""
        if self.provider == "inception":
            return self._call_inception(prompt, system_prompt, json_output, temperature)
        elif self.provider == "ollama":
            return self._call_ollama(prompt, system_prompt, json_output, temperature)
        elif self.provider == "gemini":
            return self._call_gemini(prompt, system_prompt, json_output, temperature)
        elif self.provider == "openai":
            return self._call_openai(prompt, system_prompt, json_output, temperature)
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")

    def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
    ) -> Dict[str, Any]:
        """Sends prompt and returns the parsed JSON dict."""
        raw_text = self.generate(
            prompt,
            system_prompt=system_prompt,
            json_output=True,
            temperature=temperature,
        )

        # Attempt clean parsing
        text = raw_text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            logger.error("Failed to parse LLM JSON response: %s\nRaw output: %s", exc, raw_text)
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1:
                return json.loads(text[start : end + 1])
            raise

    def _call_inception(
        self,
        prompt: str,
        system_prompt: Optional[str],
        json_output: bool,
        temperature: float,
    ) -> str:
        """Calls Inception Labs Mercury-3 API endpoint."""
        if not config.INCEPTION_API_KEY:
            raise ValueError("INCEPTION_API_KEY is not configured in .env")

        url = f"{config.INCEPTION_BASE_URL.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {config.INCEPTION_API_KEY}",
            "Content-Type": "application/json",
        }

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": config.INCEPTION_MODEL,
            "messages": messages,
            "temperature": temperature,
        }

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=60)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error("Inception Labs API request failed: %s", e)
            raise

    def _call_ollama(
        self,
        prompt: str,
        system_prompt: Optional[str],
        json_output: bool,
        temperature: float,
    ) -> str:
        url = f"{config.OLLAMA_BASE_URL.rstrip('/')}/api/generate"
        payload = {
            "model": config.OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature},
        }
        if system_prompt:
            payload["system"] = system_prompt
        if json_output:
            payload["format"] = "json"

        try:
            resp = requests.post(url, json=payload, timeout=120)
            resp.raise_for_status()
            data = resp.json()
            return data.get("response", "")
        except requests.exceptions.ConnectionError:
            raise RuntimeError(
                f"Cannot connect to Ollama at {config.OLLAMA_BASE_URL}. "
                "Ensure Ollama is running ('ollama serve' or desktop app)."
            )

    def _call_gemini(
        self,
        prompt: str,
        system_prompt: Optional[str],
        json_output: bool,
        temperature: float,
    ) -> str:
        if not config.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not configured in .env")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={config.GEMINI_API_KEY}"
        contents = []
        if system_prompt:
            contents.append({"role": "user", "parts": [{"text": f"SYSTEM INSTRUCTIONS:\n{system_prompt}"}]})
            contents.append({"role": "model", "parts": [{"text": "Understood. I will strictly follow these instructions."}]})

        contents.append({"role": "user", "parts": [{"text": prompt}]})

        payload: Dict[str, Any] = {
            "contents": contents,
            "generationConfig": {"temperature": temperature},
        }
        if json_output:
            payload["generationConfig"]["responseMimeType"] = "application/json"

        resp = requests.post(url, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        candidates = data.get("candidates", [])
        if not candidates:
            return ""
        return candidates[0]["content"]["parts"][0]["text"]

    def _call_openai(
        self,
        prompt: str,
        system_prompt: Optional[str],
        json_output: bool,
        temperature: float,
    ) -> str:
        if not config.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not configured in .env")

        headers = {
            "Authorization": f"Bearer {config.OPENAI_API_KEY}",
            "Content-Type": "application/json",
        }
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload: Dict[str, Any] = {
            "model": "gpt-4o-mini",
            "messages": messages,
            "temperature": temperature,
        }
        if json_output:
            payload["response_format"] = {"type": "json_object"}

        resp = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
