from typing import Dict, Any
from llm import get_llm
from agents.schemas import FactCheckResponse

llm = get_llm()


def _is_stop(text: str) -> bool:
    t = (text or "").strip().lower()
    return t.startswith("стоп") or t.startswith("stop")


def _should_factcheck_llm(user_message: str) -> Dict[str, Any]:
    messages = [
        {
            "role": "system",
            "content": (
                "Ты Router для FactChecker. Определи, содержит ли сообщение пользователя фактическое утверждение "
                "или потенциальную дезинформацию, которую стоит проверять. Верни СТРОГО JSON:\n"
                '{ "should_factcheck": boolean, "reason": string }\n'
                "Правила:\n"
                "- should_factcheck=false для коротких ответов, эмоций, 'не знаю', 'ок', 'да', 'нет', 'стоп', "
                "и вообще для сообщений без фактических утверждений.\n"
                "- should_factcheck=true для утверждений о версиях, стандартах, документации, планах изменений, "
                "технических 'фактов', которые могут быть неверными.\n"
                "reason короткий (1 строка). Никаких ``` и markdown."
            ),
        },
        {"role": "user", "content": user_message.strip()},
    ]
    
    res = llm.chat_json(messages)
    if not isinstance(res, dict):
        return {"should_factcheck": False, "reason": "invalid_router_response"}
        
    should = bool(res.get("should_factcheck", False))
    reason = str(res.get("reason", "")).strip()
    return {"should_factcheck": should, "reason": reason}


def _factcheck_llm(user_message: str) -> Dict[str, Any]:
    messages = [
        {
            "role": "system",
            "content": (
                "Ты FactChecker_Agent. Верни СТРОГО JSON:\n"
                '{ "alert": boolean, "content": string }\n'
                "Если утверждение похоже на ложный/неподтвержденный факт: alert=true и content начинается с 'ALERT:' "
                "и коротко (1-2 предложения) объясняет почему сомнительно/ложно и что сказать/спросить дальше.\n"
                "Не называй конкретные версии/даты/цифры, если они не даны пользователем. Формулируй нейтрально: "
                "'нет подтверждений в официальных источниках', 'нужно проверить источник'.\n"
                "Если ок: alert=false, content='OK'.\n"
                "Никаких ``` и markdown."
            ),
        },
        {"role": "user", "content": user_message.strip()},
    ]
    
    raw_json = llm.chat_json(messages)
    
    try:
        # Валидация pydantic
        res = FactCheckResponse(**raw_json)
        
        content = res.content.strip()
        if res.alert and not content.lower().startswith("alert:"):
            content = "ALERT: " + content
            
        # Обновляем контент в объекте и возвращаем dict
        res.content = content
        return res.model_dump()
        
    except Exception as e:
        print(f"Ошибка валидации FactChecker: {e}")
        # Fallback
        return FactCheckResponse(alert=False, content="OK").model_dump()


def run_factcheck(user_message: str) -> Dict[str, Any]:
    text = (user_message or "").strip()
    if not text:
        return {"alert": False, "content": "OK"}
    if _is_stop(text):
        return {"alert": False, "content": "OK"}

    route = _should_factcheck_llm(text)
    if not route.get("should_factcheck", False):
        return {"alert": False, "content": "OK"}

    return _factcheck_llm(text)