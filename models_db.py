from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Boolean,
    ForeignKey,
    Text,
    BigInteger,
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
    user_id = Column(BigInteger)  # String에서 BigInteger로 변경
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
    shared_at = Column(DateTime, default=datetime.utcnow)


class Class(Base):
    __tablename__ = "tbl_class"
    class_id = Column(Integer, primary_key=True)
    class_major = Column(String(50))  # ENUM이지만 문자열로 처리
    class_name = Column(String(3))
    grade = Column(Integer)


class User(Base):
    __tablename__ = "tbl_user"
    user_id = Column(BigInteger, primary_key=True, autoincrement=True)
    username = Column(String(50))
    account_id = Column(String(100))
    role = Column(String(10))  # ENUM이지만 문자열로 처리
    password = Column(String(64), nullable=False)


class ClassRoom(Base):
    __tablename__ = "tbl_class_room"
    class_id = Column(BigInteger, primary_key=True)
    # 필요한 컬럼들은 나중에 추가


class Student(Base):
    __tablename__ = "tbl_student"
    user_id = Column(BigInteger, primary_key=True)
    solved_score = Column(BigInteger)
    elective_subject = Column(String(20))  # ENUM이지만 문자열로 처리
    class_id = Column(BigInteger, ForeignKey("tbl_class_room.class_id"))
    version = Column(BigInteger)
    class_num = Column(Integer)
    grade = Column(Integer)
    num = Column(Integer)
