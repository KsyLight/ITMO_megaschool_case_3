import streamlit as st
from dotenv import load_dotenv
import uuid
from typing import Dict, Any

from graph import build_interview_graph
from agents.reporter import generate_final_feedback
from logger import start_session, add_turn, set_final_feedback, save_log
from utils import is_stop_command

load_dotenv()

st.set_page_config(page_title="AI Interview Coach", layout="wide")
st.title("Multi-Agent Interview Coach")
st.markdown("---")

st.markdown("""
<style>
    .stChatMessage { font-family: 'Inter', sans-serif; }
</style>
""", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []
if "interview_log" not in st.session_state:
    st.session_state.interview_log = None
if "profile" not in st.session_state:
    st.session_state.profile = {}
if "app" not in st.session_state:
    st.session_state.app = build_interview_graph()
if "interview_active" not in st.session_state:
    st.session_state.interview_active = False
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

with st.sidebar:
    st.header("Профиль кандидата")
    if not st.session_state.interview_active:
        user_input_intro = st.text_area(
            "Расскажите о себе:", 
            height=200, 
            placeholder="Привет, я Дмитрий, Python Junior..."
        )
        if st.button("Начать интервью", use_container_width=True) and user_input_intro:
            st.session_state.messages = [{"role": "user", "content": user_input_intro}]
            st.session_state.interview_log = start_session("Кандидат")
            st.session_state.interview_active = True
            st.rerun()
    else:
        st.success("Интервью идет")
        if st.button("Завершить досрочно"):
            st.session_state.messages.append({"role": "user", "content": "Стоп"})
            st.rerun()

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if st.session_state.interview_active:
    
    last_role = st.session_state.messages[-1]["role"]
    
    if last_role == "user":
        last_user_msg = st.session_state.messages[-1]["content"]

        if is_stop_command(last_user_msg):
            st.session_state.interview_active = False
            
            with st.spinner("Генерация отчета..."):
                log_data = st.session_state.interview_log
                if not log_data or not log_data["turns"]:
                    log_data = start_session("User")
                    for m in st.session_state.messages:
                        if m["role"] == "user":
                            add_turn(log_data, m["content"], [], "")

                final_report = generate_final_feedback(log_data)
                set_final_feedback(log_data, final_report)
                saved_path = save_log(log_data)

                with st.chat_message("assistant"):
                    st.markdown(final_report)
                    st.success(f"Лог сохранен: {saved_path}")
                
                st.session_state.messages.append({"role": "assistant", "content": final_report})
                st.stop()

        with st.spinner("Агент думает..."):
            try:
                config = {"configurable": {"thread_id": st.session_state.thread_id}}
                
                inputs = {
                    "messages": st.session_state.messages,
                    "user_input": last_user_msg,
                    "profile": st.session_state.profile,
                    "interview_log": st.session_state.interview_log["turns"] if st.session_state.interview_log else [],
                    "history": st.session_state.messages
                }
                
                final_response_text = ""
                internal_thoughts = []
                
                for event in st.session_state.app.stream(inputs, config=config, stream_mode="updates"):
                    
                    if "intake" in event:
                        st.session_state.profile = event["intake"].get("profile", {})

                    if "interviewer" in event:
                        data = event["interviewer"]
                        final_response_text = data.get("ai_message", "")
                        if "internal_thoughts" in data:
                            internal_thoughts.extend(data["internal_thoughts"])

                    if "reporter" in event:
                        final_response_text = event["reporter"].get("final_feedback", "")
                        st.session_state.interview_active = False

                if final_response_text:
                    with st.chat_message("assistant"):
                        st.markdown(final_response_text)
                    st.session_state.messages.append({"role": "assistant", "content": final_response_text})
                    
                    if st.session_state.interview_log:
                        add_turn(
                            st.session_state.interview_log, 
                            last_user_msg, 
                            internal_thoughts, 
                            final_response_text
                        )
                    st.rerun()
                    
            except Exception as e:
                st.error(f"Ошибка: {e}")

    else:
        if user_text := st.chat_input("Ваш ответ..."):
            st.session_state.messages.append({"role": "user", "content": user_text})
            st.rerun()