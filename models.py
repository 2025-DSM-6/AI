from pydantic import BaseModel
from typing import Optional, List


class QuestionRequest(BaseModel):
    subject: str  # 과목
    scope: str  # 범위


class QuestionResponse(BaseModel):
    question_id: int
    question: str
    options: List[str]  # 4지선다 객관식 선택지
    hint: Optional[str] = None
    answer: Optional[str] = None
    difficulty: str
    score: float


class AnswerRequest(BaseModel):
    user_id: str
    question_id: str
    answer: str
    used_hint: bool = False


class ShowAnswerRequest(BaseModel):
    user_id: str
    question_id: str


class ShareQuestionRequest(BaseModel):
    question_id: str
