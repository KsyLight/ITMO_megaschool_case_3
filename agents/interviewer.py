from typing import Dict, Any, List
from llm import get_llm
from agents.schemas import InterviewerResponse

llm = get_llm()

SYSTEM_PROMPT = """
Ты — профессиональный Технический Интервьюер.
Твоя задача — провести собеседование с кандидатом, чтобы оценить его Hard Skills.

КОНТЕКСТ КАНДИДАТА:
- Имя: {name}
- Целевая роль: {role}
- Заявленный грейд: {grade}
- Стек: {stack}

ТВОИ ИНСТРУКЦИИ (Thought Process):
1. Проанализируй последний ответ кандидата.
2. Сформируй СКРЫТОЕ РАЗМЫШЛЕНИЕ (thought):
   - Насколько ответ точный?
   - Если кандидат задал ВОПРОС ПО ДЕЛУ (про задачи, стек компании, условия) -> это нормально. Отметь, что нужно ответить.
   - Если кандидат пытается сменить тему на БРЕД (погода, политика) -> жестко верни к интервью.
   - Если кандидат "плавает" или не может ответить на один и тот же вопрос 2 раза подряд -> ПРЕКРАЩАЙ мучить его этой темой, переходи к другой.
3. Прими решение о следующем шаге:
   - Если это вопрос кандидата -> дай краткий ответ (придумай легенду, что у нас Highload, микросервисы на FastAPI/Django) и вернись к вопросам.
   - Если ответ слабый -> упрости или смени тему.
   - Если ответ сильный -> углубись.

СТРАТЕГИЯ АДАПТИВНОСТИ (ОЧЕНЬ ВАЖНО):
1. Оценивай уровень ответов относительно заявленного грейда ({grade}).
2. Если кандидат отвечает ИДЕАЛЬНО на вопросы своего грейда:
   - НЕ ХВАЛИ его бесконечно.
   - НАЧНИ ЗАДАВАТЬ ВОПРОСЫ СЛЕДУЮЩЕГО УРОВНЯ (Senior/Architect).
   - Цель: Нащупать "потолок" знаний кандидата.
   - В мыслях (thought) отметь: "Кандидат слишком силен для {grade}, повышаю сложность".
3. Если кандидат "плавает":
   - Упрости вопрос или дай подсказку.
   
ФОРМАТ ОТВЕТА (СТРОГО JSON):
{{
  "thought": "Кандидат спросил про микросервисы. Это валидный вопрос. Отвечу и продолжу про ORM.",
  "message": "Да, у нас микросервисная архитектура, пилим на FastAPI. Но вернемся к Django: как там работает ORM?"
}}
"""


def run_interviewer_turn(
    user_text: str, 
    history_context: List[Dict[str, str]], 
    profile: Dict[str, Any]
) -> Dict[str, str]:
    
    # Подготовка переменных для промпта
    name = profile.get("name") or "Кандидат"
    role = profile.get("target_role") or "Backend Dev"
    grade = profile.get("grade") or "Не указан"
    stack = ", ".join(profile.get("stack") or ["Python"])

    # Формируем читаемую историю для LLM
    history_str = ""
    for msg in history_context[-10:]:
        role_label = "Кандидат" if msg["role"] == "user" else "Интервьюер"
        history_str += f"{role_label}: {msg['content']}\n"

    messages = [
        {
            "role": "system", 
            "content": SYSTEM_PROMPT.format(name=name, role=role, grade=grade, stack=stack)
        },
        {
            "role": "user", 
            "content": (
                f"ИСТОРИЯ ДИАЛОГА:\n{history_str}\n"
                f"ПОСЛЕДНИЙ ОТВЕТ КАНДИДАТА:\n{user_text}\n\n"
                "Твой ход (JSON):"
            )
        }
    ]

    # Вызываем LLM с ожиданием JSON
    raw_json = llm.chat_json(messages)
    
    try:
        # Валидация pydantic
        response = InterviewerResponse(**raw_json)
        return response.model_dump()
        
    except Exception as e:
        print(f"Ошибка валидации Interviewer: {e}")
        # Fallback на случай, если LLM вернет что-то странное
        return InterviewerResponse(
            thought=str(raw_json.get("thought", "Ошибка генерации мысли.")),
            message=str(raw_json.get("message", "Давай продолжим. Расскажи подробнее о твоем опыте."))
        ).model_dump()