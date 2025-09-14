import google.generativeai as genai
from echotest.services.llms.LLMService import LLMService


class GeminiService(LLMService):
    def __init__(self, api_key: str) -> None:
        genai.configure(api_key=api_key)

    def query(self, model: str, text: str) -> str:
        gemini_model = genai.GenerativeModel(model)

        response = gemini_model.generate_content(text)

        return response.text
