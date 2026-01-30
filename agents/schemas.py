from typing import List, Optional
from pydantic import BaseModel, Field

class CandidateProfile(BaseModel):
    name: Optional[str] = Field(default=None, description="Имя кандидата")
    target_role: Optional[str] = Field(default=None, description="Желаемая позиция")
    grade: Optional[str] = Field(default=None, description="Грейд (Junior/Middle/Senior)")
    years_experience: Optional[int] = Field(default=None, description="Опыт в годах (число)")
    
    stack: List[str] = Field(default_factory=list, description="Список технологий")
    
    # Доп. поля
    experience_text: Optional[str] = Field(default=None, description="Сырой текст об опыте")
    unknowns: List[str] = Field(default_factory=list, description="Чего мы еще не знаем")

    class Config:
        extra = "ignore" 


class InterviewerResponse(BaseModel):
    thought: str = Field(default="Анализирую...", description="Мысли агента")
    message: str = Field(default="Продолжим.", description="Сообщение кандидату")

class FactCheckResponse(BaseModel):
    alert: bool = Field(default=False, description="Есть ли фактическая ошибка")
    content: str = Field(default="OK", description="Текст алерта")