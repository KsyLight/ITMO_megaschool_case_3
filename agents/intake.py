from typing import Dict, Any

from llm import get_llm
from utils import normalize_stack, recompute_unknowns
from agents.schemas import CandidateProfile

llm = get_llm()

def run_intake(raw_text: str) -> Dict[str, Any]:
    messages = [
        {
            "role": "system",
            "content": (
                "Ты Intake_Agent. Извлеки профиль кандидата из текста. Верни СТРОГО JSON:\n"
                '{'
                '"name": string|null, '
                '"target_role": string|null, '
                '"grade": string|null, '
                '"years_experience": number|null, '
                '"stack": [string], '
                '"experience_text": string, '
                '"unknowns": [string]'
                '}\n'
                "Правила:\n"
                "1) experience_text НЕ пустой: если нет опыта — верни исходный raw_text.\n"
                "2) stack: выдели технологии из текста.\n"
                "3) unknowns: добавь ключи из набора [years_experience, stack, target_role, grade], если их нет.\n"
                "4) years_experience: если в тексте есть число лет/года/год — извлеки только число.\n"
                "5) grade: если встречается junior/middle/senior/lead.\n"
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
            unknowns=["name", "target_role", "grade", "years_experience", "stack"]
        ).model_dump()

    
    if not data.get("experience_text"):
        data["experience_text"] = raw_text

    data["stack"] = normalize_stack(data.get("stack"), raw_text)
    data["unknowns"] = recompute_unknowns(data)

    return data