from dotenv import load_dotenv
load_dotenv()

from typing import Any, Dict, List
import json
import time

# Импорт графа
from graph import build_interview_graph

# Импорты утилит
from logger import start_session, add_turn, set_final_feedback, save_log
from agents.intake import run_intake
from agents.reporter import generate_final_feedback
from agents.interviewer import run_interviewer_turn
from utils import (
    is_stop_command,
    try_parse_json_line,
    normalize_input_to_text,
)

# Константы
ASK_FINISH_AFTER = 10
HARD_MAX_USER_TURNS = 15

def pretty_json(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2)

def main() -> None:
    # Инициализация
    app_graph = build_interview_graph()
    
    print("Multi-Agent Interview Coach")
    print("Ввод: свободный текст или JSON.")
    print("-" * 40)

    # Этап Intake (Сбор информации)
    raw = input("Кандидат: ").strip()
    if not raw:
        raw = "Привет, я Python разработчик"
        
    obj = try_parse_json_line(raw)
    candidate_text = normalize_input_to_text(raw, obj)
    
    print("\n[Intake]: Анализ профиля...")
    profile = run_intake(candidate_text)
    
    participant_name = profile.get("name") or "Аноним"
    log = start_session(participant_name)

    # Собираем первые мысли
    t1_thoughts = [{
        "from": "Intake_Agent", "to": "Interviewer_Agent", 
        "content": f"Parsed Profile: {profile.get('grade')} {profile.get('target_role')}" 
    }]

    print("[System]: Граф инициализирован. Агент готовит первый вопрос...")

    # Генерация первого вопроса
    initial_context = [{"role": "user", "content": candidate_text}]
    first_res = run_interviewer_turn(
        "Начинаем. Опирайся на приветствие. Задай первый вопрос.", 
        initial_context, profile
    )
    
    t1_thoughts.append({
        "from": "Interviewer_Agent", "to": "Interviewer_Agent", 
        "content": first_res["thought"]
    })
    current_msg = first_res["message"]
    
    # Логируем первый ход
    add_turn(log, candidate_text, t1_thoughts, current_msg)
    print(f"\nАгент: {current_msg}")

    # Основной цикл интервью
    turn_count = 0
    history_context = [] 
    history_context.append({"role": "user", "content": candidate_text})
    history_context.append({"role": "assistant", "content": current_msg})

    while True:
        user_text = input("\nКандидат: ").strip()
        if not user_text: continue

        # Проверка на выход
        if is_stop_command(user_text):
            print("\n[System]: Стоп-сигнал принят.")
            break
            
        turn_count += 1
        
        # Запуск Графа
        initial_state = {
            "profile": profile,
            "user_input": user_text,
            "history": history_context,
            "internal_thoughts": [],
            "system_alert": ""
        }
        
        try:
            final_state = app_graph.invoke(initial_state)
            

            thoughts = final_state.get("internal_thoughts", [])
            ai_answer = final_state.get("ai_message", "...")
            
            # Проверка, не решил ли граф сам завершить интервью (через reporter)
            if final_state.get("is_finished"):
                print("\n[Graph]: Граф инициировал завершение.")
                break

            # Управление лимитами
            if turn_count >= HARD_MAX_USER_TURNS:
                ai_answer = "Время вышло. Переходим к результатам."
            elif turn_count == ASK_FINISH_AFTER:
                ai_answer += "\n\n(Напишите 'Стоп' для получения фидбека)."

            # Логирование
            add_turn(log, user_text, thoughts, ai_answer)
            
            # Обновление контекста
            history_context.append({"role": "user", "content": user_text})
            history_context.append({"role": "assistant", "content": ai_answer})
            
            print(f"\nАгент: {ai_answer}")

            if turn_count >= HARD_MAX_USER_TURNS:
                break
                
        except Exception as e:
            print(f"Ошибка в цикле: {e}")
            break

    # Генерация отчета
    print("\n[Reporter]: Генерация фидбека...")

    final_feedback = generate_final_feedback(log)
    set_final_feedback(log, final_feedback)
    
    path = save_log(log)
    
    print("\n" + "="*30)
    print("LangGraph сессия завершена")
    print(final_feedback)
    print("="*30)
    print(f"Логи сохранены: {path}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        traceback.print_exc()