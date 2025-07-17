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


class AnswerResponse(BaseModel):
    correct: bool
    score: float
    answer: Optional[str] = None


class ShowAnswerResponse(BaseModel):
    answer: str


class ShareResponse(BaseModel):
    message: str


class RankingItem(BaseModel):
    user_id: int  # str에서 int로 변경
    username: Optional[str] = None
    score: float
    grade: Optional[int] = None
    class_num: Optional[int] = None
    num: Optional[int] = None


class MyRanking(BaseModel):
    rank: int
    user_id: int  # str에서 int로 변경
    username: Optional[str] = None
    score: float
    grade: Optional[int] = None
    class_num: Optional[int] = None
    num: Optional[int] = None


class RankingResponse(BaseModel):
    top_10: List[RankingItem]
    my_rank: Optional[MyRanking] = None


class SharedQuestionItem(BaseModel):
    question_id: int
    question: str
    difficulty: str
    score: float
    shared_at: str


class SharedQuestionsResponse(BaseModel):
    questions: List[SharedQuestionItem]


class QuestionDetailResponse(BaseModel):
    question_id: int
    question: str
    options: List[str]
    hint: str
    answer: str
    difficulty: str
    score: float


class StudentInfo(BaseModel):
    user_id: int
    username: str
    grade: int
    class_num: int
    num: int


class SubjectScore(BaseModel):
    subject: str
    score: float


class StudentScoresResponse(BaseModel):
    student_info: StudentInfo
    total_score: float
    subject_scores: List[SubjectScore]
