import operator
from typing import Annotated, Any, Dict, List, TypedDict, Union, Optional
from langgraph.graph import StateGraph, END

from agents.intake import run_intake
from agents.factchecker import run_factcheck
from agents.interviewer import run_interviewer_turn

class InterviewState(TypedDict):
    messages: List[Dict[str, str]]
    user_input: str
    profile: Dict[str, Any]
    interview_log: List[Any]
    turn_count: int
    final_feedback: Optional[str]
    history: List[Dict[str, str]]
    internal_thoughts: Annotated[List[Dict[str, str]], operator.add]
    system_alert: str
    ai_message: str
    final_report: str
    is_finished: bool

def node_intake(state: InterviewState) -> Dict[str, Any]:
    print("Intake_Agent извлекает данные профиля...")
    user_text = state.get("user_input", "")
    new_profile = run_intake(user_text)
    
    if not new_profile.get("stack"):
        role_lower = str(new_profile.get("target_role", "")).lower()
        if any(word in role_lower for word in ["architect", "lead", "expert", "senior"]):
            new_profile["stack"] = ["System Design", "Distributed Systems", "Highload"]
    
    print(f"[DEBUG] Профиль обновлен: {new_profile}")
    
    return {
        "profile": new_profile,
        "internal_thoughts": [{"from": "Intake_Agent", "content": "Profile parsed"}]
    }

def route_starting_step(state: InterviewState) -> str:
    if not state.get("profile", {}).get("name"):
        return "intake"
    return "factchecker"

def node_factchecker(state: InterviewState) -> Dict[str, Any]:
    print("FactChecker проверяет факты...")
    user_text = state.get("user_input", "")
    if not user_text or user_text == "...":
        return {"system_alert": ""}
        
    fc_res = run_factcheck(user_text)
    updates = {"system_alert": ""}
    if fc_res.get("alert"):
        content = fc_res.get("content", "Alert")
        updates["internal_thoughts"] = [{"from": "FactChecker", "content": content}]
        updates["system_alert"] = f"[SYSTEM ALERT: {content}] "
    return updates

def node_interviewer(state: InterviewState) -> Dict[str, Any]:
    print("Interviewer думает...")
    alert = state.get("system_alert", "")
    user_input = state.get("user_input", "")
    full_text = alert + user_input
    
    resp = run_interviewer_turn(
        user_text=full_text,
        history_context=state.get("history", []),
        profile=state.get("profile", {})
    )
    
    ai_msg_text = resp["message"]
    
    return {
        "internal_thoughts": [{"from": "Interviewer", "content": resp.get("thought", "")}],
        "ai_message": ai_msg_text,
        "history": state.get("history", []) + [{"role": "assistant", "content": ai_msg_text}]
    }

def build_interview_graph():
    workflow = StateGraph(InterviewState)
    workflow.add_node("intake", node_intake)
    workflow.add_node("factchecker", node_factchecker)
    workflow.add_node("interviewer", node_interviewer)
    
    workflow.set_conditional_entry_point(
        route_starting_step,
        {"intake": "intake", "factchecker": "factchecker"}
    )
    
    workflow.add_edge("intake", "interviewer")
    workflow.add_edge("factchecker", "interviewer")
    workflow.add_edge("interviewer", END)
    
    return workflow.compile()