# ML 혼잡도 예측 API
from datetime import date
import holidays as kr_holidays  # 한국 공휴일 계산 라이브러리

from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette import status

from database.db_connection import get_session
from models.models import ParkingInfo
from schema.request import PredictRequest
from schema.response import PredictResponse

router = APIRouter(tags=["예측"])

@router.post( # 혼잡도 예측 API
    "/predict",
    response_model=PredictResponse,
    status_code=status.HTTP_200_OK,
)
def predict_handler(
    body   : PredictRequest,     # { lot_id: int, target_date: date }
    request: Request,  # app.state.ml_model 접근용 — FastAPI Request 객체
    session: Session = Depends(get_session),
):
    """
    주차장 ID와 날짜를 받아서 ML 모델로 혼잡도를 예측
    처리 순서:
        1) 서버에 ML 모델이 로드되어 있는지 확인
        2) 주차장 정보(capacity 등) DB에서 조회
        3) 날짜 → 피처 벡터 자동 계산
        4) 모델.predict(X) 호출
        5) 혼잡도% + 잔여 면수 계산 후 반환
    """
    # ML 모델 확인
    # main.py lifespan에서 app.state.ml_model 에 로드 됨
    # getattr(객체, 속성명, 기본값): 속성이 없을 때 기본값 반환
    model = getattr(request.app.state, "ml_model", None) #ml_model 속성은 로드해 둔 머신러닝 모델
    if model is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, #서버는 살아있지만 서비스 불가 상태
            detail="ML 모델이 로드되지 않았습니다. ml/train.py 를 먼저 실행하세요.",
            # models_pkl/hangang_parking.pkl 파일이 없거나 로드 실패 시 발생
        )

    #주차장 정보 조회
    stmt = select(ParkingInfo).where(ParkingInfo.id == body.lot_id)
    lot = session.scalar(stmt)  # 없으면 None
    if not lot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="주차장을 찾을 수 없습니다",
        )
    # 날짜 -> 피처 자동 계산
    target = body.target_date  # date 객체, date(2026.7.4)
    day_of_week = target.isoweekday()  # 1(월) ~ 7(일) # MySQL DAYOFWEEK()는 1=일~7=토
    is_weekend = 1 if day_of_week >= 6 else 0  # 6=토, 7=일 → 주말
    week_of_year = target.isocalendar()[1]  # 연간 몇 번째 주 (1~53) , isocalendar(연도, 주차, 요일)

    # 공휴일 여부 확인
    is_holiday = 1 if target in kr_holidays.KR() else 0

    # 피처 벡터 구성
    # 학습 시 사용한 피처 순서와 반드시 동일해야
    # ml/train.py의 SELECT 컬럼 순서: lot_id, capacity, month, day_of_week,is_weekend, week_of_year, is_holiday

    X = [[
        body.lot_id,  # 주차장 ID (1~11)
        int(lot.capacity),  # 총 주차면수 (Decimal → int 변환)
        target.month,  # 월 (1~12)
        day_of_week,  # 요일 (1~7)
        is_weekend,  # 주말 여부 (0/1)
        week_of_year,  # 연간 주차 (1~53)
        is_holiday,  # 공휴일 여부 (0/1)
    ]]
    # X 형태: [[1, 458, 7, 6, 1, 33, 1]], 1행7열 형태, 2차원 리스트인 이유: scikit-learn은 (n_samples 행, n_features 열) 형태를 요구
    # 예측 실행, model.predict(X): 혼잡도 % 예측, 첫 번째 값 추출
    occupancy_pct = float(model.predict(X)[0])

    # occupancy_pct = max(0.0, min(100.0, occupancy_pct)) #모델이 0% 미만 또는 100% 초과로 예측하는 경우 보정

    # 잔여 면수 계산: 혼잡도 80% → 잔여 20% → 잔여 면수 = capacity × 0.20
    predicted_spaces = int(int(lot.capacity) * (1 - occupancy_pct / 100))

    # 응답 반환
    return PredictResponse(
        lot_id=body.lot_id,
        lot_name=lot.lot_name,
        target_date=body.target_date,
        capacity=int(lot.capacity),
        predicted_spaces=predicted_spaces,
        occupancy_pct=round(occupancy_pct, 1),  # 소수점 1자리로 반올림
    )