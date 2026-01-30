import json
import re
import string
from typing import Any, Dict, List, Optional

# Расширенный список для поиска по ключевым словам (если LLM не отдала стек явно)
ALLOWED_STACK = {
    "python", "django", "fastapi", "flask",
    "java", "spring", "hibernate", "kotlin", "maven", "gradle",
    "javascript", "typescript", "react", "vue", "node",
    "sql", "postgres", "postgresql", "mysql", "mongodb",
    "redis", "docker", "kubernetes", "git", "linux", "celery", "rabbitmq", "kafka"
}

# Триггеры для завершения интервью
STOP_WORDS = {
    "стоп", "stop", "завершить", "закончить", "конец", "хватит", 
    "exit", "quit", "finish", "bye"
}

STOP_PHRASES = [
    "давай фидбэк", "дай фидбэк", "хочу фидбэк",
    "подведи итог", "результаты интервью",
    "останови интервью", "прекрати интервью"
]

def is_stop_command(text: str) -> bool:
    """Проверка, хочет ли пользователь закончить интервью."""
    if not text:
        return False
    
    raw = text.lower().strip()
    clean = raw.rstrip(string.punctuation)
    
    words = clean.split()
    if not words:
        return False
        
    if words[0] in STOP_WORDS:
        return True
        
    for phrase in STOP_PHRASES:
        if phrase in clean:
            return True
            
    return False

def try_parse_json_line(raw: str) -> Optional[Dict[str, Any]]:
    """Попытка распарсить строку как JSON."""
    s = raw.strip()
    if not (s.startswith("{") and s.endswith("}")):
        return None
    try:
        obj = json.loads(s)
        return obj if isinstance(obj, dict) else None
    except Exception:
        return None

def normalize_stack(stack: Any, raw_text: str) -> List[str]:
    """
    Приводит стек к плоскому списку строк в нижнем регистре.
    Больше не удаляет технологии, которых нет в ALLOWED_STACK.
    """
    items: List[str] = []
    
    if isinstance(stack, list):
        for v in stack:
            s = str(v).strip().lower()
            if s: items.append(s)
    elif isinstance(stack, str):
        parts = re.split(r"[,\|;/]+|\s+", stack.lower())
        items.extend([p.strip() for p in parts if p.strip()])

    if not items:
        low = raw_text.lower()
        for t in ALLOWED_STACK:
            if t in low:
                items.append(t)

    out: List[str] = []
    for s in items:
        s = s.replace("postgresql", "postgres")
        out.append(s)

    return sorted(list(dict.fromkeys(out)))

def recompute_unknowns(profile: Dict[str, Any]) -> List[str]:
    """Определяет, какие обязательные поля профиля еще не заполнены."""
    unknowns: List[str] = []
    
    # Проверка на года опыта
    if profile.get("years_experience") is None:
        unknowns.append("years_experience")
        
    # Проверка на стек
    if not (profile.get("stack") or []):
        unknowns.append("stack")
        
    # Проверка на роль
    if not profile.get("target_role"):
        unknowns.append("target_role")
        
    # Проверка на грейд
    if not profile.get("grade"):
        unknowns.append("grade")
        
    return unknowns

def normalize_input_to_text(raw: str, obj: Optional[Dict[str, Any]]) -> str:
    """Вспомогательная функция для форматирования входных данных в строку (для логов)."""
    if obj is None:
        return raw.strip()

    def pick(*keys: str) -> Optional[Any]:
        for k in keys:
            if k in obj and obj[k] is not None:
                return obj[k]
        return None

    name = pick("Имя", "имя", "name", "candidate_name")
    position = pick("Позиция", "позиция", "position", "role")
    grade = pick("Грейд", "грейд", "grade", "level")
    experience = pick("Опыт", "опыт", "experience", "background")

    parts = [
        f"Имя: {str(name).strip()}" if name else "",
        f"Позиция: {str(position).strip()}" if position else "",
        f"Грейд: {str(grade).strip()}" if grade else "",
        f"Опыт: {str(experience).strip()}" if experience else "",
    ]
    text = " | ".join([p for p in parts if p]).strip()
    return text if text else raw.strip()