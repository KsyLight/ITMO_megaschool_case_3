from typing import Dict, Any, List
from llm import get_llm
from agents.schemas import InterviewerResponse

llm = get_llm()

SYSTEM_PROMPT = """
Ты — профессиональный Технический Интервьюер. 
Твоя задача — оценить Hard Skills кандидата строго по тем данным, которые указаны в его профиле.

КОНТЕКСТ КАНДИДАТА:
- Имя: {name}
- Целевая роль: {role}
- Заявленный грейд: {grade}
- Стек технологий: {stack}

КРИТИЧЕСКИЕ ПРАВИЛА:
1. Твои вопросы должны касаться ТОЛЬКО технологий из списка: {stack}. 
2. Запрещено упоминать любые другие языки программирования или фреймворки, которых нет в списке кандидата.
3. Если кандидат — {role}, то тема беседы — исключительно {stack}.

АЛГОРИТМ НАЧАЛА ДИАЛОГА:
Если это твой самый первый ход (в истории нет твоих сообщений), ты ОБЯЗАН:
1. Поздороваться по имени: "Здравствуйте, {name}!".
2. Представиться: "Я ваш AI-интервьюер. Сегодня мы проведем технический скрининг на позицию {role}".
3. Обозначить формат: "У нас запланировано около 10-15 вопросов по вашему основному стеку: {stack}".
4. Задать первый вопрос именно по тематике {stack}.

ТВОИ ИНСТРУКЦИИ (Thought Process):
1. Анализ: В поле "thought" оценивай только знания по {stack}.
2. Вопросы кандидата: Если спрашивают про проект, отвечай, что в компании используется {stack} и современные архитектуры, затем возвращайся к вопросам по {stack}.
3. Управление темой: Вежливо пресекай любые попытки уйти от темы {stack}.

СТРАТЕГИЯ АДАПТИВНОСТИ:
- Повышай или понижай сложность вопросов только в рамках технологий {stack}.

ФОРМАТ ОТВЕТА (СТРОГО JSON):
{{
  "thought": "Техническая оценка ответа по {stack}. Соответствие уровню {grade}. План следующего вопроса.",
  "message": "Текст твоего сообщения кандидату."
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