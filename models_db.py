from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Boolean,
    ForeignKey,
    Text,
)
from sqlalchemy.orm import declarative_base
from datetime import datetime
import json

Base = declarative_base()


class Question(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True, index=True)
    subject = Column(String(50))
    scope = Column(String(100))
    question = Column(String(500))
    options = Column(Text)  # 4지선다 선택지(JSON 문자열)
    hint = Column(String(500))
    answer = Column(String(200))
    difficulty = Column(String(10))
    score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

    def set_options(self, options_list):
        self.options = json.dumps(options_list)

    def get_options(self):
        return json.loads(self.options) if self.options else []


class UserAnswer(Base):
    __tablename__ = "user_answers"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50))  # User 테이블과 FK는 나중에 연결
    question_id = Column(Integer, ForeignKey("questions.id"))
    user_answer = Column(String(200))
    used_hint = Column(Boolean, default=False)
    is_correct = Column(Boolean)
    score = Column(Float)
    answered_at = Column(DateTime, default=datetime.utcnow)


class SharedQuestion(Base):
    __tablename__ = "shared_questions"
    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"))
    shared_by = Column(String(50))  # user_id
    shared_at = Column(DateTime, default=datetime.utcnow)
