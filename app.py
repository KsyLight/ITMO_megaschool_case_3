import os
import uuid
from dotenv import load_dotenv

load_dotenv()
from graph import build_interview_graph
from logger import start_session, add_turn, set_final_feedback, save_log
from agents.reporter import generate_final_feedback
from utils import is_stop_command

HARD_MAX_USER_TURNS = 15
STUDENT_NAME = "Василенко Егор Викторович"

def main() -> None:
    app_graph = build_interview_graph()
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    print("--- Multi-Agent Interview Coach (CLI) ---")
    print(f"Студент: {STUDENT_NAME}")
    
    print("\nВведите данные кандидата (Имя, Роль, Стек, Грейд):")
    candidate_info = input(">>> ").strip()
    while not candidate_info:
        candidate_info = input("Введите данные кандидата: ").strip()
        
    log = start_session(STUDENT_NAME)

    state = {
        "profile": {}, 
        "messages": [],
        "user_input": candidate_info,
        "history": [],
        "internal_thoughts": [],
        "turn_count": 0,
        "is_finished": False
    }

    print(f"\n[System]: Данные отправлены в Intake Agent...")
    print("-" * 40)

    try:
        turn_count = 0
        while True:
            final_state = app_graph.invoke(state, config=config)
            state.update(final_state)
            
            ai_answer = state.get("ai_message", "Error")
            thoughts = state.get("internal_thoughts", [])
            
            print(f"\n[Агент]: {ai_answer}")

            user_text = ""
            while not user_text:
                user_text = input(f"\n[{state.get('profile', {}).get('name', 'Кандидат')}]: ").strip()
                if not user_text:
                    print("[System]: Пожалуйста, введите ваш ответ.")

            if is_stop_command(user_text):
                print("\n[System]: Завершение сессии по команде.")
                break

            state["internal_thoughts"] = [] 
            state["history"].append({"role": "user", "content": user_text})
            state["user_input"] = user_text
            
            add_turn(log, user_text, thoughts, ai_answer)
            
            turn_count += 1
            state["turn_count"] = turn_count

            if turn_count >= HARD_MAX_USER_TURNS or state.get("is_finished"):
                break

    except Exception as e:
        print(f"\n[Ошибка]: {e}")
        import traceback; traceback.print_exc()

    print("\n[Reporter]: Генерация фидбека...")
    final_feedback = generate_final_feedback(log)
    set_final_feedback(log, final_feedback)
    path = save_log(log)
    print("\nРЕЗУЛЬТАТЫ:\n", final_feedback)
    print(f"Лог сохранен: {path}")

if __name__ == "__main__":
    main()