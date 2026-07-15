# API 응답 본문 모델
#응답(Response) 모델 = 서버 → 클라이언트로 돌려주는 데이터 구조 정의

from datetime import datetime, date
from pydantic import BaseModel, ConfigDict

# 공통 기반 클래스
class BaseResponse(BaseModel): #obj.lot_name 처럼 객체의 속성(attribute)으로 값을 읽도록 허용
    model_config = ConfigDict(from_attributes=True)  #from_attributes=True: ORM 객체를 Pydantic이 직접 읽을 수 있게 허용

# 주차장 단일 조회 응답 모델
class ParkingInfoResponse(BaseResponse):
    id: int
    lot_name: str
    district: str
    capacity: int
    lat: float
    lng: float

# 주차장 목록 + 페이지네이션 응답 모델
class ParkingListResponse(BaseResponse): #GET /parking-lots?page=1&size=9 에서 사용
    total: int
    page: int
    size: int
    items: list[ParkingInfoResponse]

# 회원가입 성공 응답 모델
class UserSignUpResponse(BaseResponse):
    id: int
    email: str
    name: str
    created_at: datetime

# 예약 생성 응답 모델
class ReservationResponse(BaseResponse):
    id: int
    lot_id: int
    reserved_date: date
    status: str
    created_at: datetime

# 내 예약 목록 응답 모델
class ReservationDetailResponse(BaseResponse):
    id: int
    lot_id: int
    lot_name: str
    reserved_date: date
    status: str
    created_at: datetime

# ML 예측 결과 응답 모델
class PredictResponse(BaseResponse):
    lot_id: int
    lot_name: str
    target_date: date
    capacity: int
    predicted_spaces: int
    occupancy_pct: float






