# app/services/openai_service.py
import os
import openai
from config import settings

class OpenAIService:
    def __init__(self):
        openai.api_key = settings.OPENAI_API_KEY

    def query_openai(self, prompt: str, model_name: str = "gpt-4o-mini", temperature: float = 0.1, top_p: float = 1.0) -> str:
        try:
            response = openai.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant. Provide answers based on given context."},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                top_p=top_p
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error querying OpenAI: {e}")
            return "죄송합니다. 응답 생성 중 오류가 발생했습니다."
