# JWT 토큰 생성 & 검증 모듈

import jwt
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status
from dotenv import load_dotenv
import os

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY", "hangang-secret-key")  # 토큰 서명에 사용할 비밀키 (.env에서 관리)
ALGORITHM  = "HS256"  # 서명 알고리즘

def create_access_token(user_id: int, role: str, expires_minutes: int = 60):
    payload = {
        "user_id": user_id,  # 사용자 식별 정보
        "role": role,  # 권한 정보 ("user" / "admin")
        "exp": datetime.now(timezone.utc) + timedelta(minutes=expires_minutes), #토큰 만료 시각 — 만료되면 재로그인 필요
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)  # 토큰 생성 및 반환

def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM]) # jwt.decode()는 서명 검증과 만료 시간 검사를 자동으로 수행
        return {
            "user_id": payload["user_id"],
            "role": payload.get("role", "user"),
        }
    except jwt.ExpiredSignatureError: # 토큰 만료
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError: # 서명 불일치 또는 형식 오류
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

