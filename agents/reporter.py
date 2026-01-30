import json
from typing import Any, Dict
from llm import get_llm
from agents.resources import get_resources_str

llm = get_llm()

REPORT_PROMPT = """
Ты — Tech Lead и Hiring Manager.
Твоя задача — проанализировать лог технического интервью и составить финальный отчет (Feedback).

ВХОДНЫЕ ДАННЫЕ:
1. Лог интервью (JSON). Изучи поле "internal_thoughts" (мысли интервьюера и фактчекера).
2. СПРАВОЧНИК ССЫЛОК (для Roadmap):
{resources_str}

ТРЕБУЕМАЯ СТРУКТУРА ОТЧЕТА:

1. ВЕРДИКТ
   - Оцененный грейд: (Junior / Middle / Senior).
     ВАЖНО: Если кандидат заявлялся как Junior, но отвечал на сложные вопросы уровня Senior -> пиши "Grade: Senior (Overqualified)".
   - Рекомендация: (Hire / No Hire / Strong Hire).
     ЕСЛИ Overqualified: Рекомендуй Hire, но с пометкой "Рассмотреть на грейд выше".
   - Уровень уверенности (0-100%).

2. ТЕХНИЧЕСКИЙ АНАЛИЗ (Hard Skills)
   - Confirmed Skills: Темы, где кандидат ответил верно.
   - Knowledge Gaps: Темы, где кандидат ошибся или не знал ответа.
     ВАЖНО: Для каждого пункта "Knowledge Gaps" ты ОБЯЗАН написать КРАТКИЙ ПРАВИЛЬНЫЙ ТЕХНИЧЕСКИЙ ОТВЕТ.
     Пример: "Не знает отличия tuple от list. (Правильно: tuple неизменяем и хешируем, list изменяем)".

3. SOFT SKILLS & COMMUNICATION
   - Честность (были ли попытки соврать, обнаруженные FactChecker?).
   - Ясность изложения.
   - Инициативность (задавал ли вопросы о проекте?).

4. ROADMAP (Что учить)
   - Список тем для изучения на основе пробелов.
   - ДЛЯ КАЖДОГО ПУНКТА ОБЯЗАТЕЛЬНО ПРИЛОЖИ ССЫЛКУ.
     Алгоритм выбора ссылки:
     A. Если подходящая тема есть в "СПРАВОЧНИКЕ ССЫЛОК" выше -> бери ссылку оттуда.
     B. Если темы нет -> сгенерируй ссылку на поиск Google: https://www.google.com/search?q=запрос+python
     
     Пример: 
     "- Изучить оптимизацию ORM. [Документация](https://docs.djangoproject.com/...)"
     "- Разобраться с Kafka. [Поиск](https://www.google.com/search?q=kafka+python)"

ВАЖНО: Пиши отчет на русском языке. Не используй Markdown-заголовки (с #) и форматирование через *, используй просто ВЕРХНИЙ РЕГИСТР для разделов.
"""

def generate_final_feedback(log_data: Dict[str, Any]) -> str:
    log_str = json.dumps(log_data, ensure_ascii=False, indent=2)
    
    # Получаем список ссылок
    res_str = get_resources_str()

    messages = [
        {
            "role": "system", 
            "content": REPORT_PROMPT.format(resources_str=res_str)
        },
        {"role": "user", "content": f"Вот лог интервью:\n{log_str}"}
    ]

    return llm.chat(messages)