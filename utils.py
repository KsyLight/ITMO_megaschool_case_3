import json
import re
import string
from typing import Any, Dict, List, Optional

ALLOWED_STACK = {
    "python", "django", "fastapi", "flask",
    "sql", "postgres", "postgresql", "mysql",
    "redis", "docker", "kubernetes", "git", "linux", "celery", "rabbitmq"
}

START_TRIGGERS = {
    "стоп", "stop", "завершить", "закончить", "конец", "хватит", 
    "exit", "quit", "finish", "bye"
}

PHRASE_TRIGGERS = [
    "давай фидбэк", "дай фидбэк", "хочу фидбэк",
    "подведи итог", "результаты интервью",
    "останови интервью", "прекрати интервью"
]

def is_stop_command(text: str) -> bool:
    if not text:
        return False
    
    raw = text.lower().strip()
    clean = raw.rstrip(string.punctuation)
    
    words = clean.split()
    if not words:
        return False
        
    if words[0] in START_TRIGGERS:
        return True
        
    for phrase in PHRASE_TRIGGERS:
        if phrase in clean:
            return True
            
    return False

def try_parse_json_line(raw: str) -> Optional[Dict[str, Any]]:
    s = raw.strip()
    if not (s.startswith("{") and s.endswith("}")):
        return None
    try:
        obj = json.loads(s)
        return obj if isinstance(obj, dict) else None
    except Exception:
        return None

def normalize_input_to_text(raw: str, obj: Optional[Dict[str, Any]]) -> str:
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

def normalize_stack(stack: Any, raw_text: str) -> List[str]:
    items: List[str] = []
    if isinstance(stack, list):
        for v in stack:
            s = str(v).strip().lower()
            if s:
                items.append(s)
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
        if s in ALLOWED_STACK:
            out.append(s)

    return sorted(list(dict.fromkeys(out)))

def recompute_unknowns(profile: Dict[str, Any]) -> List[str]:
    unknowns: List[str] = []
    if profile.get("years_experience") is None:
        unknowns.append("years_experience")
    if not (profile.get("stack") or []):
        unknowns.append("stack")
    if not profile.get("target_role"):
        unknowns.append("target_role")
    if not profile.get("grade"):
        unknowns.append("grade")
    return unknowns