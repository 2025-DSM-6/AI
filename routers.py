import os
import random
from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session
from database import get_db
from models_db import Question, UserAnswer, SharedQuestion
from models import (
    QuestionRequest,
    QuestionResponse,
    AnswerRequest,
    ShowAnswerRequest,
    ShareQuestionRequest,
    StudentScoresResponse,
    AnswerResponse,
    ShowAnswerResponse,
    ShareResponse,
    RankingResponse,
    SharedQuestionsResponse,
    QuestionDetailResponse,
)
from typing import List, Dict, Any, Optional
import google.generativeai as genai
import logging
from dotenv import load_dotenv
import json


load_dotenv()

# Gemini API 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
genai.configure(api_key=os.getenv("GEMINI_KEY"))
model = genai.GenerativeModel("gemini-2.0-flash")

router = APIRouter()


# Gemini API 호출 함수 (사용자 요청대로 이름 및 구조 변경)
def generate_with_google(prompt: str) -> str:
    try:
        response = model.generate_content(prompt)
        return response.text if response else "GEMINI API error"
    except Exception as e:
        logger.error(f"Google API 호출 중 오류 발생: {e}")
        return "API 호출 중 오류 발생"


@router.post("/generate-question", response_model=QuestionResponse)
def generate_question(req: QuestionRequest, db: Session = Depends(get_db)):
    import uuid

    rand = random.random()
    if rand < 0.2:
        difficulty = "상"
        score = 3.0
    elif rand < 0.6:
        difficulty = "중"
        score = 2.0
    else:
        difficulty = "하"
        score = 1.0

    prompt = f"""
[문제 생성 요청]
과목: {req.subject}
범위: {req.scope}
난이도: {difficulty}
문제 유형: 4지선다 객관식

아래 예시처럼 문제, 4개의 선택지(options), 정답(번호), 힌트만 만들어줘.
문제는 반드시 '문제:'로 시작해서 한 줄로 만들어줘.

예시)
문제: 다음 중 한국의 수도는 어디인가요?
1. 부산
2. 서울
3. 대구
4. 인천
정답: 2
힌트: 대한민국의 정치, 경제, 문화의 중심지
"""

    ai_text = generate_with_google(prompt)

    # Gemini 응답 파싱
    question_text = ""
    options = []
    answer = ""
    hint = ""
    first_nonempty = None
    if (
        ai_text
        and not ai_text.startswith("API 호출 중 오류")
        and not ai_text.startswith("GEMINI API error")
    ):
        lines = [line.strip() for line in ai_text.split("\n") if line.strip()]
        for line in lines:
            if not first_nonempty and line:
                first_nonempty = line
            if line.startswith("문제:"):
                question_text = line.replace("문제:", "").strip()
            elif line[:2] in ["1.", "2.", "3.", "4."]:
                options.append(line[2:].strip())
            elif line.startswith("정답:"):
                answer = line.replace("정답:", "").strip()
            elif line.startswith("힌트:"):
                hint = line.replace("힌트:", "").strip()
        # 반드시 4개만 반환
        options = (options + [""] * 4)[:4]
        # 문제 텍스트가 비어 있으면 백업값 사용
        if not question_text and first_nonempty:
            question_text = first_nonempty
    else:
        question_text = (
            f"[예시] {req.subject} - {req.scope} ({difficulty}) 문제를 생성했습니다."
        )
        options = ["1번", "2번", "3번", "4번"]
        answer = "1"
        hint = f"[예시] {req.subject} 힌트입니다."

    # DB에 문제 저장 (options는 응답에만 포함)
    new_question = Question(
        subject=req.subject,
        scope=req.scope,
        question=question_text,
        options=json.dumps(options),
        hint=hint,
        answer=answer,
        difficulty=difficulty,
        score=score,
    )
    db.add(new_question)
    db.commit()
    db.refresh(new_question)

    return {
        "question_id": new_question.id,
        "question": new_question.question,
        "options": options,
        "hint": new_question.hint,
        "answer": new_question.answer,
        "difficulty": new_question.difficulty,
        "score": new_question.score,
    }


@router.post("/submit-answer", response_model=AnswerResponse)
def submit_answer(req: AnswerRequest, db: Session = Depends(get_db)):
    q = db.query(Question).filter(Question.id == req.question_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="문제를 찾을 수 없습니다.")
    correct = req.answer.strip() == q.answer
    score = 0.0
    if correct:
        score = q.score * 0.5 if req.used_hint else q.score
    # 풀이 기록 저장
    user_answer = UserAnswer(
        user_id=req.user_id,
        question_id=q.id,
        user_answer=req.answer,
        used_hint=req.used_hint,
        is_correct=correct,
        score=score,
    )
    db.add(user_answer)
    db.commit()
    return {
        "correct": correct,
        "score": score,
        "answer": q.answer if not correct else None,
    }


@router.post("/show-answer", response_model=ShowAnswerResponse)
def show_answer(req: ShowAnswerRequest, db: Session = Depends(get_db)):
    q = db.query(Question).filter(Question.id == req.question_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="문제를 찾을 수 없습니다.")
    return {"answer": q.answer}


@router.get("/ranking", response_model=RankingResponse)
def get_ranking(
    user_id: str = Query(..., description="조회할 사용자 ID"),
    db: Session = Depends(get_db),
):
    from sqlalchemy import func
    from models_db import Student, User

    # user_id별 총점 집계
    scores = (
        db.query(UserAnswer.user_id, func.sum(UserAnswer.score).label("total_score"))
        .group_by(UserAnswer.user_id)
        .order_by(func.sum(UserAnswer.score).desc())
        .all()
    )
    # 학생 정보와 사용자 정보 한 번에 조회
    user_ids = [uid for uid, _ in scores[:10]]
    students = db.query(Student).filter(Student.user_id.in_(user_ids)).all()
    users = db.query(User).filter(User.user_id.in_(user_ids)).all()
    student_map = {s.user_id: s for s in students}
    user_map = {u.user_id: u for u in users}

    top_10 = []
    for idx, (uid, score) in enumerate(scores[:10], 1):
        stu = student_map.get(uid)
        user = user_map.get(uid)
        top_10.append(
            {
                "user_id": uid,
                "username": user.username if user else None,
                "score": float(score),
                "grade": stu.grade if stu else None,
                "class_num": stu.class_num if stu else None,
                "num": stu.num if stu else None,
            }
        )
    # 내 랭킹
    my_rank = None
    for idx, (uid, score) in enumerate(scores, 1):
        if uid == user_id:
            stu = db.query(Student).filter(Student.user_id == uid).first()
            user = db.query(User).filter(User.user_id == uid).first()
            my_rank = {
                "rank": idx,
                "user_id": uid,
                "username": user.username if user else None,
                "score": float(score),
                "grade": stu.grade if stu else None,
                "class_num": stu.class_num if stu else None,
                "num": stu.num if stu else None,
            }
            break
    return {"top_10": top_10, "my_rank": my_rank}


@router.get("/my-ranking", response_model=RankingResponse)
def get_my_ranking(
    user_id: str = Query(..., description="조회할 사용자 ID"),
    db: Session = Depends(get_db),
):
    from sqlalchemy import func

    scores = (
        db.query(UserAnswer.user_id, func.sum(UserAnswer.score).label("total_score"))
        .group_by(UserAnswer.user_id)
        .order_by(func.sum(UserAnswer.score).desc())
        .all()
    )
    my_rank = None
    for idx, (uid, score) in enumerate(scores, 1):
        if uid == user_id:
            my_rank = {"rank": idx, "user_id": uid, "score": float(score)}
            break
    return my_rank


@router.post("/share-question", response_model=ShareResponse)
def share_question(req: ShareQuestionRequest, db: Session = Depends(get_db)):
    q = db.query(Question).filter(Question.id == req.question_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="문제를 찾을 수 없습니다.")
    shared = SharedQuestion(question_id=q.id)
    db.add(shared)
    db.commit()
    return {"message": "문제가 공유되었습니다."}


@router.get("/shared-questions", response_model=SharedQuestionsResponse)
def get_shared_questions(subject: str = None, db: Session = Depends(get_db)):
    query = db.query(SharedQuestion).join(
        Question, SharedQuestion.question_id == Question.id
    )
    if subject:
        query = query.filter(Question.subject == subject)
    shared = query.all()
    result = []
    for s in shared:
        q = db.query(Question).filter(Question.id == s.question_id).first()
        if q:
            result.append(
                {
                    "question_id": q.id,
                    "question": q.question,
                    "difficulty": q.difficulty,
                    "score": q.score,
                    "shared_at": s.shared_at.isoformat(),  # datetime을 문자열로 변환
                }
            )
    if result == []:
        raise HTTPException(status_code=404, detail="공유된 문제가 없습니다")
    return {"questions": result}  # questions 필드로 감싸서 반환


@router.get("/question/{question_id}", response_model=QuestionDetailResponse)
def get_question_detail(question_id: int, db: Session = Depends(get_db)):
    q = db.query(Question).filter(Question.id == question_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="문제를 찾을 수 없습니다.")
    return {
        "question_id": q.id,
        "question": q.question,
        "options": q.get_options(),
        "hint": q.hint,
        "answer": q.answer,
        "difficulty": q.difficulty,
        "score": q.score,
    }


@router.get("/student-scores", response_model=StudentScoresResponse)
def get_student_scores(
    grade: int = Query(..., description="학년"),
    class_num: int = Query(..., description="반"),
    num: int = Query(..., description="번호"),
    db: Session = Depends(get_db),
):
    from sqlalchemy import func
    from models_db import Student, User, Question

    # 1학년/반/번호로 학생 찾기
    student = (
        db.query(Student)
        .filter(
            Student.grade == grade, Student.class_num == class_num, Student.num == num
        )
        .first()
    )

    if not student:
        raise HTTPException(status_code=44, detail="학생을 찾을 수 없습니다.")

    # 2생 이름 가져오기
    user = db.query(User).filter(User.user_id == student.user_id).first()
    username = user.username if user else "Unknown"
    # 3. 해당 학생의 과목별 점수 집계
    subject_scores = (
        db.query(Question.subject, func.sum(UserAnswer.score).label("total_score"))
        .join(UserAnswer, Question.id == UserAnswer.question_id)
        .filter(UserAnswer.user_id == student.user_id)
        .group_by(Question.subject)
        .order_by(func.sum(UserAnswer.score).desc())
        .all()
    )

    # 4. 전체 총점 계산
    total_score = sum(score for _, score in subject_scores)

    # 5. 응답 데이터 구성
    subject_breakdown = [
        {"subject": subject, "score": float(score)} for subject, score in subject_scores
    ]

    return {
        "student_info": {
            "user_id": student.user_id,
            "username": username,
            "grade": student.grade,
            "class_num": student.class_num,
            "num": student.num,
        },
        "total_score": float(total_score),
        "subject_scores": subject_breakdown,
    }
