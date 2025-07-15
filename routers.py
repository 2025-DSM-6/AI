import os
import random
from fastapi import APIRouter, HTTPException
from models import (
    QuestionRequest,
    QuestionResponse,
    AnswerRequest,
    HintRequest,
    ShowAnswerRequest,
    ShareQuestionRequest,
)
from typing import List, Dict, Any, Optional
import google.generativeai as genai
import logging
from dotenv import load_dotenv


load_dotenv()

# Gemini API 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
genai.configure(api_key=os.getenv("GEMINI_KEY"))
model = genai.GenerativeModel("gemini-2.0-flash")

router = APIRouter()

# 임시 데이터 저장 (DB 연동 전)
questions_db: Dict[str, Dict[str, Any]] = {}
user_scores: Dict[str, float] = {}
shared_questions: List[Dict[str, Any]] = []


# Gemini API 호출 함수 (사용자 요청대로 이름 및 구조 변경)
def generate_with_google(prompt: str) -> str:
    try:
        response = model.generate_content(prompt)
        return response.text if response else "GEMINI API error"
    except Exception as e:
        logger.error(f"Google API 호출 중 오류 발생: {e}")
        return "API 호출 중 오류 발생"


@router.post("/generate-question", response_model=QuestionResponse)
def generate_question(req: QuestionRequest):
    import uuid

    # 난이도 비율: 상(20%), 중(40%), 하(40%)
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
    qid = str(uuid.uuid4())

    prompt = f"""
[문제 생성 요청]
과목: {req.subject}
범위: {req.scope}
난이도: {difficulty}
문제 유형: 단서형, 객관식, 단답형 등 다양한 유형 중 랜덤

아래 예시처럼 문제, 힌트, 정답만 만들어줘. (보기/선택지는 필요 없음)

예시1(국어-단서형)
단서1: 신라→실라
단서2: 실내→실래
단서3: 광안리→광알리
힌트: ㄴ이 ㄹ과 만나 ㄹ로 바뀌는 음운 변동
문제: 다음에서 사용된 음운의 변동은?
정답: 유음화

예시2(국어-단답형)
문제: 다음 중 비음화가 일어나는 단어를 고르시오.
힌트: 비음화는 ㄱ, ㄷ, ㅂ이 ㄴ, ㅁ 앞에서 ㅇ, ㄴ, ㅁ으로 바뀌는 현상
정답: 국물

예시3(수학-단서형)
단서: √-1
힌트: 허수 단위
문제: 복소수 단위 i의 정의는 무엇인가요?
정답: i

예시4(수학-단답형)
문제: 이차방정식 x^2-4=0의 두 실근의 곱을 구하시오.
힌트: 근과 계수의 관계를 이용
정답: -4

정답은 반드시 하나만(번호가 아니라 내용) 제공해줘.
"""

    ai_text = generate_with_google(prompt)

    # Gemini 응답 파싱
    question_text = ""
    hint = ""
    answer = ""
    if (
        ai_text
        and not ai_text.startswith("API 호출 중 오류")
        and not ai_text.startswith("GEMINI API error")
    ):
        lines = [line.strip() for line in ai_text.split("\n") if line.strip()]
        for line in lines:
            if line.startswith("문제:"):
                question_text = line.replace("문제:", "").strip()
            elif line.startswith("힌트:"):
                hint = line.replace("힌트:", "").strip()
            elif line.startswith("정답:"):
                answer = line.replace("정답:", "").strip()
    else:
        question_text = (
            f"[예시] {req.subject} - {req.scope} ({difficulty}) 문제를 생성했습니다."
        )
        hint = f"[예시] {req.subject} 힌트입니다."
        answer = f"[예시] {req.subject} 정답입니다."

    question = {
        "question_id": qid,
        "question": question_text,
        "hint": hint,
        "answer": answer,
        "difficulty": difficulty,
        "score": score,
    }
    questions_db[qid] = question
    return question


@router.post("/get-hint")
def get_hint(req: HintRequest):
    q = questions_db.get(req.question_id)
    if not q:
        raise HTTPException(status_code=404, detail="문제를 찾을 수 없습니다.")
    return {"hint": q["hint"]}


@router.post("/submit-answer")
def submit_answer(req: AnswerRequest):
    q = questions_db.get(req.question_id)
    if not q:
        raise HTTPException(status_code=404, detail="문제를 찾을 수 없습니다.")
    correct = req.answer.strip() == q["answer"]
    score = 0.0
    if correct:
        if req.used_hint:
            score = q["score"] * 0.5
        else:
            score = q["score"]
        user_scores[req.user_id] = user_scores.get(req.user_id, 0) + score
    return {
        "correct": correct,
        "score": score,
        "answer": q["answer"] if not correct else None,
    }


@router.post("/show-answer")
def show_answer(req: ShowAnswerRequest):
    q = questions_db.get(req.question_id)
    if not q:
        raise HTTPException(status_code=404, detail="문제를 찾을 수 없습니다.")
    return {"answer": q["answer"]}


@router.get("/ranking")
def get_ranking():
    ranking = sorted(user_scores.items(), key=lambda x: x[1], reverse=True)
    return [{"user_id": uid, "score": score} for uid, score in ranking]


@router.post("/share-question")
def share_question(req: ShareQuestionRequest):
    q = questions_db.get(req.question_id)
    if not q:
        raise HTTPException(status_code=404, detail="문제를 찾을 수 없습니다.")
    shared_questions.append(q)
    return {"message": "문제가 공유되었습니다."}


@router.get("/shared-questions")
def get_shared_questions():
    return shared_questions
