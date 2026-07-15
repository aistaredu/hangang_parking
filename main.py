# 한강공원 주차장 예측 웹앱
import os
import joblib
from pathlib import Path
from contextlib import asynccontextmanager # 파이썬 비동기 컨텍스트 매니저 # 애플리케이션 시작과 종료 시점에 실행할 코드를 정의

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

# DB 엔진과 ORM Base 클래스
from database.db_connection import engine
from database.orm import Base

from models.models import ParkingInfo, ParkingDaily, Holiday, User, Reservation
import models

# 라우터 임포트
from routers.user        import router as user_router
from routers.parking     import router as parking_router
from routers.reservation import router as reservation_router
from routers.predict     import router as predict_router
from routers.admin       import router as admin_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        #서버 시작 시 실행
        Base.metadata.create_all(bind=engine) # 테이블 생성 지시: 이미 존재하는 테이블은 건너뛰고 없는 테이블만 생성
        print("✅ DB 테이블 자동 생성 완료")
    except Exception as e:
        print(f"DB 초기화 실패(앱은 계속 실행): {e}")
    #ML 모델 로드
    # 서버를 시작할 때 머신러닝 모델이 메모리에 준비되고 이후 각 API 요청에서는 이미 로드된 모델을 바로 사용할 수 있다
    # app.state: FastAPI 앱 전체에서 공유하는 저장 공간
    # 모든 라우터에서 request.app.state.ml_model 로 접근 가능
    model_path = Path("models_pkl/hangang_parking.pkl") #파일의 경로 객체를 생성, pickle파일은 학습이 완료된 머신러닝 모델 저장
    if model_path.exists(): #경로에 실제로 파일이 존재하는지 확인
        app.state.ml_model = joblib.load(model_path) #저장되어 있던 머신러닝 모델 파일을 다시 읽어와서 전역 상태 저장소에 저장
        print(f" ML 모델 로드 완료: {model_path}")
    else:
        app.state.ml_model = None
        print(f"  ML 모델 없음 : {model_path}")

    yield  # yield를 기준으로 시작/종료 코드를 나눈다
    # 서버 종료 시 실행
    print("서버 종료")

# FastAPI 앱 생성
app = FastAPI(
    title      = "한강공원 주차장 예측 API",
    version    = "1.0.0",
    lifespan   = lifespan, #없으면 테이블 생성 안 됨, # lifespan — 서버 시작/종료 처리
)

# 라우터 등록
app.include_router(parking_router) #주차장 CRUD
app.include_router(user_router) #회원가입·로그인

app.include_router(reservation_router) # 내 예약
app.include_router(predict_router)  #ML 예측

app.include_router(admin_router)  #관리자 API


# 미들웨어 등록
# 세션 미들웨어: 요청 처리 과정에서 세션을 생성하고 쿠키를 통해 세션을 유지
# 서버만 알고 있는 secret_key로 세션 쿠키를 서명하고 검증
# pip install itsdangerous  ← 쿠키에 저장되는 세션 데이터를 서명하는 라이브러리
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY", "hangang-session-secret"),
)

# CORS 미들웨어: 브라우저가 다른 출처(포트) 서버에 요청하는 것을 허용
# 예) index.html(5500)에서 FastAPI(8000)으로 fetch 요청 시 브라우저가 차단 → 이걸 풀어줌
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 출처 허용 (개발용, 배포 시 도메인 지정)
    allow_methods=["*"],
    allow_headers=["*"],
)


# 정적 파일 서빙 - static/ 폴더의 HTML/CSS/JS 파일을 웹에서 접근 가능하게 제공
# http://127.0.0.1:8000/static/index.html
app.mount("/static", StaticFiles(directory="static"), name="static")

# 기본 엔드포인트
@app.get("/", tags=["기본"])
def root():
    return {"message": "한강공원 주차장 예측 API", "docs": "/docs"}

@app.get("/health", tags=["기본"])
def health():
    """헬스 체크 — Railway 배포 플랫폼이 서버 상태 확인 시 사용"""
    return {"status": "ok"}

# 직접 실행 시 uvicorn 서버 시작
# python main.py 로 실행할 때만 동작
if __name__ == "__main__":
    import os
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True) #fastapi dev