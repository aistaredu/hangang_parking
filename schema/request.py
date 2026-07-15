# API 요청 본문 검증 모델
# 요청(Request) 모델 = 클라이언트 → 서버로 보내는 데이터 구조 정의
# Pydantic이 자동으로 타입 검증, 규칙 검증, JSON 문자열 → Python 객체 자동 변환 처리

import re
from datetime import date
from pydantic import BaseModel, EmailStr, Field, field_validator

# 주차장 등록 요청 모델 (POST /parking-lots)
class ParkingCreateRequest(BaseModel):
    lot_name: str = Field(..., min_length=1, max_length=60, description="주차장명") #...: 필수 입력
    district: str = Field(..., min_length=1, max_length=30, description="지구명")
    capacity: int = Field(..., gt=0, description="총 주차면수 (0보다 커야 함)") # gt=0는 0보다 커야 함
    lat: float = Field(..., ge=-90, le=90, description="위도 (-90 ~ 90)") #ge 이상
    lng: float = Field(..., ge=-180, le=180, description="경도 (-180 ~ 180)") #le 이하

# 주차장 수정 요청 모델 (PATCH /parking-lots/{lot_id})
#수정할 필드만 선택적으로 전송, 보내지 않은 필드는 None이 되고, 기존값을 그대로 유지
class ParkingUpdateRequest(BaseModel):
    lot_name: str | None = None # None: 이 필드를 수정하지 않음을 의미
    district: str | None = None
    capacity: int | None = Field(None, gt=0) # None 허용, 값이 있으면 0보다 커야 함
    lat: float | None = Field(None, ge=-90, le=90)
    lng: float | None = Field(None, ge=-180, le=180)

# 회원 가입 요청 모델
class UserSignUpRequest(BaseModel):
    email: EmailStr = Field(..., description="사용자 이메일 주소")# EmailStr: pydantic 이메일 전용 타입 — @ 포함 여부 등 형식 자동 검증
    password: str = Field(..., min_length=8, description="비밀번호(평문 입력)")
    name: str = Field(..., min_length=1, max_length=50, description="이름")

    @field_validator("password")  # password 필드 값이 입력될 때 이 함수 자동 실행
    def validate_password(cls, value): # cls: 클래스 자신 (인스턴스 메서드가 아닌 클래스 메서드)
        if not re.search(r"[A-Z]", value): # value: password 필드에 실제로 입력된 값
            raise ValueError("비밀번호에는 대문자가 최소 1개 포함되어야 합니다.")
        if not re.search(r"[a-z]", value):
            raise ValueError("비밀번호에는 소문자가 최소 1개 포함되어야 합니다.")
        if not re.search(r"[0-9]", value):
            raise ValueError("비밀번호에는 숫자가 최소 1개 포함되어야 합니다.")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", value):
            raise ValueError("비밀번호에는 특수문자가 최소 1개 포함되어야 합니다.")
        return value # 검증 실패 시 422 Unprocessable Entity 자동 반환

#로그인 요청 모델
class UserLoginRequest(BaseModel):
    email: EmailStr = Field(..., description="사용자 이메일 주소")
    password: str = Field(..., min_length=8, description="비밀번호(평문 입력)")


#  예약 생성 요청 모델
class ReservationCreateRequest(BaseModel):
    lot_id: int = Field(..., ge=1, le=11, description="예약할 주차장 ID (1~11)") # 1 이상 11 이하 — 한강공원 주차장 ID 범위
    reserved_date: date = Field(..., description="예약 날짜 (YYYY-MM-DD)")

# 예약 상태 수정 요청 모델
class ReservationUpdateRequest(BaseModel):
    status: str | None = None # 허용값: "active" / "completed" / "cancelled"
    # None이면 수정하지 않음

# ML  혼잡도 예측 요청 모델
class PredictRequest(BaseModel):
    lot_id: int = Field(..., ge=1, le=11, description="주차장 ID (1~11)")
    target_date: date = Field(..., description="예측할 날짜 (YYYY-MM-DD)")
