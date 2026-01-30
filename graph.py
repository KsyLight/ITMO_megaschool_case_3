import operator
from typing import Annotated, Any, Dict, List, TypedDict, Union, Optional

from langgraph.graph import StateGraph, END

from agents.factchecker import run_factcheck
from agents.interviewer import run_interviewer_turn


class InterviewState(TypedDict):
    # То, что передает UI
    messages: List[Dict[str, str]]
    user_input: str
    profile: Dict[str, Any]
    interview_log: List[Any]
    turn_count: int
    final_feedback: Optional[str]
    history: List[Dict[str, str]]
    
    # Внутренние данные графа
    internal_thoughts: Annotated[List[Dict[str, str]], operator.add]
    system_alert: str
    
    # Выходные данные
    ai_message: str
    final_report: str
    is_finished: bool

# Узлы графа
def node_factchecker(state: InterviewState) -> Dict[str, Any]:
    """Узел проверки фактов. Запускается первым."""
    print("FactChecker проверяет факты...")
    user_text = state.get("user_input", "")
    
    # Вызов логики factchecker
    fc_res = run_factcheck(user_text)
    
    updates = {}
    if fc_res.get("alert"):
        content = fc_res.get("content", "Alert detected")
        updates["internal_thoughts"] = [{
            "from": "FactChecker_Agent",
            "to": "Interviewer_Agent",
            "content": content
        }]
        updates["system_alert"] = f"[SYSTEM ALERT: {content}] "
    else:
        updates["system_alert"] = ""
        
    return updates

def node_interviewer(state: InterviewState) -> Dict[str, Any]:
    """Узел Интервьюера."""
    print("Interviewer думает...")
    
    # Склеиваем алерт и текст юзера
    alert = state.get("system_alert", "")
    user_input = state.get("user_input", "")
    full_text = alert + user_input
    
    # Вызов логики
    resp = run_interviewer_turn(
        user_text=full_text,
        history_context=state.get("history", []),
        profile=state.get("profile", {})
    )
    
    ai_msg_text = resp["message"]
    
    new_messages = state.get("messages", []) + [{"role": "assistant", "content": ai_msg_text}]
    new_history = state.get("history", []) + [
        {"role": "user", "content": user_input},
        {"role": "assistant", "content": ai_msg_text}
    ]

    return {
        "internal_thoughts": [{
            "from": "Interviewer_Agent", 
            "to": "Interviewer_Agent", 
            "content": resp.get("thought", "")
        }],
        "ai_message": ai_msg_text,
        "messages": new_messages,
        "history": new_history
    }

def node_reporter(state: InterviewState) -> Dict[str, Any]:
    """Узел Репортера."""
    return {"is_finished": True}

# Сборка Графа
def build_interview_graph():
    workflow = StateGraph(InterviewState)
    workflow.add_node("factchecker", node_factchecker)
    workflow.add_node("interviewer", node_interviewer)
    workflow.set_entry_point("factchecker")
    workflow.add_edge("factchecker", "interviewer")
    workflow.add_edge("interviewer", END)
    
    return workflow.compile()