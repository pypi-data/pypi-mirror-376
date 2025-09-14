from echotest.services.llms.GeminiService import GeminiService
from echotest.services.llms.AnthropicService import AnthropicService
from echotest.services.llms.OpenAIService import OpenAIService


def getLLM(llm: str, api_key: str) -> OpenAIService:
    if llm == "openai":
        return OpenAIService(api_key)
    elif llm == "anthropic":
        return AnthropicService(api_key)
    elif llm == "gemini":
        return GeminiService(api_key)
    else:
        raise TypeError(f"{llm} is not a valid embeddings llm")
