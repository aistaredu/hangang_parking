# 회원 관련 API

from fastapi import APIRouter, status, HTTPException, Depends, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.orm import Session

from schema.request import UserSignUpRequest, UserLoginRequest
from schema.response import UserSignUpResponse
from database.db_connection import get_session
from models.models import User
from auth.password import hash_password, verify_password
from auth.jwt import create_access_token

router = APIRouter(tags=["User"])

# 백그라운드 태스크: 회원가입 환영 이메일
def send_welcome_email(email: str):
    import time
    time.sleep(5)
    print(f"Send Welcome Email to {email}...")

# 회원가입
@router.post(
    "/users/signup",
    status_code=status.HTTP_201_CREATED,
    response_model=UserSignUpResponse, # 응답 모델 지정 — 비밀번호 제외한 정보만 반환
)
def signup_user_handler(
    body: UserSignUpRequest,   # 자동으로 입력값 검증 (이메일 형식, 비밀번호 규칙)
    background_tasks: BackgroundTasks,  # 백그라운드 태스크 주입
    session: Session = Depends(get_session),
):
    # 이메일 중복 검사
    stmt = select(User).where(User.email == body.email) # 이메일 중복 조회 쿼리 객체 생성
    existing_user = session.scalar(stmt)  # 쿼리 실행, 결과가 없으면 None 반환
    if existing_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="이미 사용중인 이메일입니다")

    # 비밀번호 해시 생성
    hashed_password = hash_password(body.password)  # 평문 비밀번호 → 해시값

    # User 모델 생성 후 DB 저장
    user = User(
        email=str(body.email),
        hashed_password=hashed_password,
        name=body.name,
        role="user",
    )
    session.add(user)  # 세션에 등록
    session.commit()  # 데이터베이스에 저장
    session.refresh(user)  # DB에서 생성된 값 (id, created_at) 반영

    # 백그라운드 태스크 등록 — 응답 반환 후 실행
    background_tasks.add_task(send_welcome_email, user.email)

    return user  # 응답 모델 기준으로 반환

# 로그인 (JWT 방식)
@router.post(
    "/users/login",
    status_code=status.HTTP_200_OK
)
def login_user_handler(
    body: UserLoginRequest,
    session: Session = Depends(get_session),
):
    stmt = select(User).where(User.email == body.email)
    user = session.scalar(stmt)

    if not user:  # 사용자 존재 여부 검증
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="이메일 또는 비밀번호가 올바르지 않습니다")

    if not verify_password(body.password, user.hashed_password):  # 비밀번호 검증
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="이메일 또는 비밀번호가 올바르지 않습니다")

    # 인증 성공 → JWT 토큰 생성 (60분 유효)
    access_token = create_access_token(user_id=user.id, role=user.role, expires_minutes=60)
    return {"access_token": access_token}