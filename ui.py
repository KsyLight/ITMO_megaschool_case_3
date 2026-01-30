import streamlit as st
from dotenv import load_dotenv
import uuid
from graph import build_interview_graph
from agents.reporter import generate_final_feedback
from logger import start_session, add_turn, set_final_feedback, save_log
from utils import is_stop_command

load_dotenv()
STUDENT_NAME = "Василенко Егор Викторович"

st.set_page_config(page_title="AI Interview Coach", layout="wide")
st.title("Multi-Agent Interview Coach")
st.markdown("---")
st.markdown("<style>.stChatMessage { font-family: 'Inter', sans-serif; }</style>", unsafe_allow_html=True)

# Инициализация стейта
if "messages" not in st.session_state: st.session_state.messages = []
if "interview_log" not in st.session_state: st.session_state.interview_log = None
if "profile" not in st.session_state: st.session_state.profile = {}
if "app" not in st.session_state: st.session_state.app = build_interview_graph()
if "interview_active" not in st.session_state: st.session_state.interview_active = False
if "thread_id" not in st.session_state: st.session_state.thread_id = str(uuid.uuid4())
if "last_ai_message" not in st.session_state: st.session_state.last_ai_message = ""

with st.sidebar:
    st.header("Настройки интервью")
    st.caption(f"Студент: {STUDENT_NAME}")
    
    if not st.session_state.interview_active:
        # ВВОД ПОЛНЫХ ДАННЫХ ДЛЯ INTAKE
        candidate_info = st.text_area(
            "О себе (Имя, Стек, Грейд):", 
            placeholder="Я Иван, Middle Python Developer. Знаю Django, Docker, PostgreSQL.",
            height=120
        )
        start_btn = st.button("Начать интервью", use_container_width=True)
        
        if start_btn and candidate_info:
            st.session_state.interview_log = start_session(STUDENT_NAME)
            
            # ВАЖНО: Пустой профиль запустит Intake Agent в графе
            st.session_state.profile = {} 
            
            # Первое сообщение - это контекст, который обработает Intake
            st.session_state.messages = [{"role": "user", "content": candidate_info}]
            st.session_state.interview_active = True
            st.rerun()
    else:
        # Отображение распарсенного профиля (если Intake уже отработал)
        p = st.session_state.profile
        if p.get("name"):
            st.success(f"Кандидат: {p.get('name')} | {p.get('target_role')}")
        if st.button("Завершить досрочно"):
            st.session_state.messages.append({"role": "user", "content": "Стоп"})
            st.rerun()

# Отрисовка чата (скрываем нулевое сообщение с контекстом)
for idx, msg in enumerate(st.session_state.messages):
    if idx == 0: continue
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if st.session_state.interview_active:
    last_role = st.session_state.messages[-1]["role"]
    
    if last_role == "user":
        last_user_msg = st.session_state.messages[-1]["content"]

        if is_stop_command(last_user_msg):
            st.session_state.interview_active = False
            with st.spinner("Генерация отчета..."):
                log = st.session_state.interview_log
                rep = generate_final_feedback(log)
                set_final_feedback(log, rep)
                path = save_log(log)
                with st.chat_message("assistant"):
                    st.markdown(rep)
                    st.success(f"Лог: {path}")
                st.session_state.messages.append({"role": "assistant", "content": rep})
                st.stop()

        with st.spinner("Агент думает..."):
            try:
                config = {"configurable": {"thread_id": st.session_state.thread_id}}
                inputs = {
                    "messages": st.session_state.messages,
                    "user_input": last_user_msg,
                    "profile": st.session_state.profile,
                    "history": st.session_state.messages
                }
                
                final_txt = ""
                thoughts = []
                
                for event in st.session_state.app.stream(inputs, config=config, stream_mode="updates"):
                    # Intake обновит профиль
                    if "intake" in event:
                        st.session_state.profile = event["intake"].get("profile", st.session_state.profile)

                    if "interviewer" in event:
                        data = event["interviewer"]
                        final_txt = data.get("ai_message", "")
                        if "internal_thoughts" in data: thoughts.extend(data["internal_thoughts"])

                if final_txt:
                    if st.session_state.interview_log and len(st.session_state.messages) > 1:
                        q = st.session_state.last_ai_message or "Start"
                        add_turn(st.session_state.interview_log, last_user_msg, thoughts, q)
                    
                    st.session_state.last_ai_message = final_txt
                    st.session_state.messages.append({"role": "assistant", "content": final_txt})
                    st.rerun()
                    
            except Exception as e:
                st.error(f"Ошибка: {e}")
    else:
        if user_text := st.chat_input("Ваш ответ..."):
            st.session_state.messages.append({"role": "user", "content": user_text})
            st.rerun()