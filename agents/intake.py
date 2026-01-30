from typing import Dict, Any
import re

from llm import get_llm
from utils import normalize_stack, recompute_unknowns
from agents.schemas import CandidateProfile

llm = get_llm()

def run_intake(raw_text: str) -> Dict[str, Any]:
    messages = [
        {
            "role": "system",
            "content": (
                "Ты Intake_Agent. Твоя задача — извлечь профиль кандидата.\n"
                "Верни СТРОГО JSON:\n"
                "{\n"
                "  \"name\": string|null,\n"
                "  \"target_role\": string|null,\n"
                "  \"grade\": string|null,\n"
                "  \"years_experience\": number|null,\n"
                "  \"stack\": [string],\n"
                "  \"experience_text\": string,\n"
                "  \"unknowns\": [string]\n"
                "}\n\n"
                "КРИТИЧЕСКИЕ ПРАВИЛА:\n"
                "1. Если в 'target_role' указан язык (например, 'Java Developer'), ОБЯЗАТЕЛЬНО добавь его в 'stack'.\n"
                "2. Если пользователь говорит про Java, в стеке НЕ МОЖЕТ быть Python.\n"
                "3. В unknowns пиши поля, которые НЕ удалось найти в тексте."
            ),
        },
        {"role": "user", "content": raw_text},
    ]

    json_data = llm.chat_json(messages)

    try:
        profile = CandidateProfile(**json_data)
        data = profile.model_dump()
    except Exception as e:
        print(f"Ошибка валидации профиля (Intake): {e}")
        data = CandidateProfile(
            name=None,
            target_role=None,
            grade=None,
            years_experience=None,
            stack=[],
            experience_text=raw_text,
            unknowns=["name", "target_role", "grade", "stack"]
        ).model_dump()

    # --- ЖЕСТКАЯ ПОДСТРАХОВКА (Решает вашу проблему) ---
    if not data.get("stack") or len(data["stack"]) == 0:
        source_text = (str(data.get("target_role", "")) + " " + raw_text).lower()
        # Список популярных языков для проверки
        check_techs = ["java", "python", "javascript", "go", "rust", "c++", "c#", "php"]
        for tech in check_techs:
            if tech in source_text:
                data["stack"] = [tech.capitalize() if tech != "java" else "Java"]
                break

    if not data.get("experience_text"):
        data["experience_text"] = raw_text

    # Вызов ваших утилит для финальной шлифовки
    data["stack"] = normalize_stack(data.get("stack"), raw_text)
    data["unknowns"] = recompute_unknowns(data)

    return data