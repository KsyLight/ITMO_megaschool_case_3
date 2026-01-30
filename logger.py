import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
import copy

Thought = Dict[str, str]
InternalThoughts = List[Thought]
Log = Dict[str, Any]


def start_session(participant_name: str) -> Log:
    return {
        "participant_name": participant_name,
        "turns": [],
        "final_feedback": "",
    }


def _normalize_internal_thoughts(
    internal_thoughts: Union[str, InternalThoughts, None],
    default_from: str = "Observer_Agent",
    default_to: str = "Interviewer_Agent",
) -> InternalThoughts:
    """Сохраняет мысли в памяти как список словарей (для удобства работы)."""
    if internal_thoughts is None:
        return []

    if isinstance(internal_thoughts, str):
        s = internal_thoughts.strip()
        if not s:
            return []
        return [{"from": default_from, "to": default_to, "content": s}]

    if isinstance(internal_thoughts, list):
        norm: InternalThoughts = []
        for item in internal_thoughts:
            if not isinstance(item, dict):
                continue
            frm = str(item.get("from", "")).strip()
            to = str(item.get("to", "")).strip()
            content = str(item.get("content", "")).strip()
            if frm and to and content:
                norm.append({"from": frm, "to": to, "content": content})
        return norm

    return []


def add_turn(
    log: Log,
    user_message: str,
    internal_thoughts: Union[str, InternalThoughts, None],
    agent_visible_message: str,
) -> int:
    turn_id = len(log["turns"]) + 1
    log["turns"].append(
        {
            "turn_id": turn_id,
            "user_message": user_message,
            "internal_thoughts": _normalize_internal_thoughts(internal_thoughts),
            "agent_visible_message": agent_visible_message,
        }
    )
    return turn_id


def set_final_feedback(log: Log, final_feedback: str) -> None:
    log["final_feedback"] = final_feedback


def make_log_filename(prefix: str = "interview_log", ext: str = "json") -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{ts}.{ext}"


def save_log(
    log: Log,
    filename: Optional[str] = None,
    out_dir: str = "outputs",
) -> str:
    """
    Сохраняет лог в файл, преобразуя формат под требования ТЗ.
    Internal thoughts преобразуются из списка словарей в строку.
    """
    os.makedirs(out_dir, exist_ok=True)

    if not filename:
        filename = make_log_filename()

    path = os.path.join(out_dir, filename)

    export_data = {
        "participant_name": log.get("participant_name", "Unknown"),
        "turns": [],
        "final_feedback": log.get("final_feedback", "")
    }

    for turn in log.get("turns", []):
        # Логика склеивания мыслей в строку
        thoughts_list = turn.get("internal_thoughts", [])
        thoughts_str_parts = []
        
        for t in thoughts_list:
            agent_name = t.get("from", "System").replace("_Agent", "")
            content = t.get("content", "").strip()
            if agent_name == "Intake" and "Parsed Profile" in content:
                content = "Профиль кандидата успешно проанализирован."
            
            thoughts_str_parts.append(f"[{agent_name}]: {content}")
        
        final_thoughts_str = " ".join(thoughts_str_parts)

        export_data["turns"].append({
            "turn_id": turn["turn_id"],
            "agent_visible_message": turn["agent_visible_message"],
            "user_message": turn["user_message"],
            "internal_thoughts": final_thoughts_str
        })

    with open(path, "w", encoding="utf-8") as f:
        json.dump(export_data, f, ensure_ascii=False, indent=2)

    return path