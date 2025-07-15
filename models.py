from pydantic import BaseModel
from typing import Optional


class QuestionRequest(BaseModel):
    subject: str  # 과목
    scope: str  # 범위


class QuestionResponse(BaseModel):
    question_id: str
    question: str
    hint: Optional[str] = None
    answer: Optional[str] = None
    difficulty: str
    score: float


class AnswerRequest(BaseModel):
    user_id: str
    question_id: str
    answer: str
    used_hint: bool = False


class HintRequest(BaseModel):
    user_id: str
    question_id: str


class ShowAnswerRequest(BaseModel):
    user_id: str
    question_id: str


class ShareQuestionRequest(BaseModel):
    user_id: str
    question_id: str
