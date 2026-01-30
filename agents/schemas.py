from typing import List, Optional
from pydantic import BaseModel, Field

# Схема для профиля кандидата (intake)
class CandidateProfile(BaseModel):
    name: Optional[str] = Field(default="Unknown Candidate", description="Имя кандидата")
    target_role: Optional[str] = Field(default="Developer", description="Желаемая позиция")
    grade: Optional[str] = Field(default="Junior", description="Грейд (Junior/Middle/Senior)")
    years_experience: Optional[int] = Field(default=0, description="Опыт в годах (число)")
    stack: List[str] = Field(default_factory=list, description="Список технологий")
    experience_text: str = Field(default="", description="Сырой текст об опыте")
    unknowns: List[str] = Field(default_factory=list, description="Чего мы еще не знаем")

# Схема для ответа интервьюера
class InterviewerResponse(BaseModel):
    # Дефолтные значения спасают от падения программы при ошибках парсинга
    thought: str = Field(default="Анализирую ответ...", description="Внутренние размышления агента")
    message: str = Field(default="Можешь уточнить?", description="Сообщение для кандидата")

# Cхема для фактчекера
class FactCheckResponse(BaseModel):
    alert: bool = Field(default=False, description="True, если найдена ошибка/ложь/галлюцинация")
    content: str = Field(default="OK", description="Текст предупреждения или 'OK'")