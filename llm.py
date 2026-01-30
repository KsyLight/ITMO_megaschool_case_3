import os

from dotenv import load_dotenv
load_dotenv()

import json
import warnings
import time
from typing import List, Dict, Any, Optional

# Глушим предупреждения LangChain
from langchain_core._api import LangChainDeprecationWarning
warnings.simplefilter("ignore", category=LangChainDeprecationWarning)

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage
from langchain_core.language_models.chat_models import BaseChatModel

# Великий Гигачат
try:
    from langchain_gigachat.chat_models import GigaChat
except ImportError:
    try:
        from langchain_community.chat_models import GigaChat
    except ImportError:
        GigaChat = None

# OpenAI
try:
    from langchain_openai import ChatOpenAI
except ImportError:
    ChatOpenAI = None

# Gemini
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
except ImportError:
    ChatGoogleGenerativeAI = None

# Google Vertex AI
try:
    from langchain_google_vertexai import ChatVertexAI
except ImportError:
    ChatVertexAI = None


Message = Dict[str, str]

class LLMService:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LLMService, cls).__new__(cls)
            cls._instance.model = cls._instance._init_model()
        return cls._instance

    def _init_model(self) -> BaseChatModel:
        # Читаем конфиг из .env
        provider = os.getenv("LLM_PROVIDER", "gigachat").lower()
        temperature = float(os.getenv("LLM_TEMPERATURE", "0.2"))
        model_name = os.getenv("LLM_MODEL") 
        timeout = int(os.getenv("LLM_TIMEOUT", "30"))

        if provider == "gigachat":
            if not GigaChat:
                raise ImportError("Библиотека не найдена. Выполни: pip install langchain-gigachat")
            
            verify_ssl = os.getenv("GIGACHAT_VERIFY_SSL", "true").lower() == "true"

            return GigaChat(
                credentials=os.environ["GIGACHAT_CREDENTIALS"],
                scope=os.getenv("GIGACHAT_SCOPE", "GIGACHAT_API_PERS"),
                verify_ssl_certs=verify_ssl,
                timeout=timeout,
                model=model_name or "GigaChat-Pro",
                temperature=temperature,
                verbose=False
            )
        
        if provider in ["openai", "openrouter"]:
            if not ChatOpenAI:
                raise ImportError("Библиотека не найдена. Выполни: pip install langchain-openai")
            
            base_url = "https://openrouter.ai/api/v1" if provider == "openrouter" else None
            api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
            
            return ChatOpenAI(
                api_key=api_key,
                base_url=base_url,
                model_name=model_name or "gpt-4o-mini",
                temperature=temperature,
                request_timeout=timeout
            )

        if provider == "gemini":
            if not ChatGoogleGenerativeAI:
                raise ImportError("Библиотека не найдена. Выполни: pip install langchain-google-genai")
            
            return ChatGoogleGenerativeAI(
                google_api_key=os.environ["GOOGLE_API_KEY"],
                model=model_name or "gemini-1.5-flash",
                temperature=temperature,
                convert_system_message_to_human=True,
                timeout=timeout
            )
        
        if provider == "vertex":
            if not ChatVertexAI:
                raise ImportError("Библиотека не найдена. Выполни: pip install langchain-google-vertexai")
            
            return ChatVertexAI(
                model_name=model_name or "gemini-1.5-pro",
                temperature=temperature,
                project=os.getenv("GOOGLE_PROJECT_ID"),
                location=os.getenv("GOOGLE_LOCATION", "us-central1"),
                max_retries=1
            )
            
        raise ValueError(f"Неизвестный LLM_PROVIDER: {provider}")

    def _convert_messages(self, messages: List[Message]) -> List[BaseMessage]:
        lc_msgs = []
        for m in messages:
            content = str(m.get("content", ""))
            if m["role"] == "system":
                lc_msgs.append(SystemMessage(content=content))
            elif m["role"] == "user":
                lc_msgs.append(HumanMessage(content=content))
            elif m["role"] == "assistant":
                lc_msgs.append(AIMessage(content=content))
        return lc_msgs

    def chat(self, messages: List[Message]) -> str:
        lc_msgs = self._convert_messages(messages)
        
        max_retries = 2
        for attempt in range(max_retries):
            try:
                return self.model.invoke(lc_msgs).content
            except Exception as e:
                print(f"Ошибка сети LLM (попытка {attempt+1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2) # Ждем 2 секунды
                    continue
                else:
                    return "Извините, ошибка соединения с нейросетью. Попробуйте повторить запрос."

    def chat_json(self, messages: List[Message]) -> Dict[str, Any]:
        """Гарантирует возврат JSON."""
        json_instruction = "\n\nВАЖНО: Ответ должен быть ТОЛЬКО валидным JSON объектом. Без Markdown, без ```."
        
        msgs = [m.copy() for m in messages]
        if msgs and msgs[-1]["role"] == "user":
            msgs[-1]["content"] += json_instruction
        else:
            msgs.append({"role": "user", "content": json_instruction})

        raw = self.chat(msgs)
        return self._parse_json_safe(raw)
    

    def _parse_json_safe(self, text: Any) -> Dict[str, Any]:
        if isinstance(text, list) and len(text) > 0:
            text = text[0]
        
        if hasattr(text, 'content'):
            text = text.content
            
        if not isinstance(text, str):
            text = str(text)

        text = text.strip()
        
        if "```" in text:
            parts = text.split("```")
            for part in parts:
                if "{" in part:
                    text = part.replace("json", "").strip()
                    break
        
        text = text.strip().strip("'").strip('"')
        
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            try:
                import re
                match = re.search(r'\{.*\}', text, re.DOTALL)
                if match:
                    return json.loads(match.group(0))
            except:
                pass
            return {"error": "json_parse_error", "raw_content": text}

def get_llm() -> LLMService:
    return LLMService()