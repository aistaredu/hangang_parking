# 예약 관련 API — 생성 · 목록 조회 · 취소
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette import status

from database.db_connection import get_session
from models.models          import Reservation, ParkingInfo
from schema.request         import ReservationCreateRequest
from schema.response        import ReservationResponse, ReservationDetailResponse
from auth.jwt               import decode_access_token

from routers.admin import expire_past_reservations   # 관리자 파일에서 가져오기

router = APIRouter(tags=["예약"])

bearer = HTTPBearer(auto_error=False)

# 로그인 필수

# 예약 생성
# POST /reservations
@router.post(
    "/reservations",
    response_model=ReservationResponse,  # 생성된 예약 정보 반환
    status_code=status.HTTP_201_CREATED,
)
def create_reservation_handler(
    body   : ReservationCreateRequest,
    session: Session = Depends(get_session),
    authorization: HTTPAuthorizationCredentials | None = Depends(bearer),
):
    #로그인 확인
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="로그인이 필요합니다",
        )
    token_data = decode_access_token(authorization.credentials) #Authorization 헤더에서 추출한 JWT 토큰 문자열
    user_id = token_data["user_id"]  # 토큰에서 사용자 ID 추출

    # 주차장 존재 여부 확인
    stmt = select(ParkingInfo).where(ParkingInfo.id == body.lot_id)
    lot = session.scalar(stmt) # 없으면 None 반환
    if not lot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="주차장을 찾을 수 없습니다",
        )
    # 예약 객체 생성 & DB 저장
    reservation = Reservation(
        user_id=user_id, # JWT에서 추출
        lot_id=body.lot_id,
        reserved_date=body.reserved_date,
        status="active",
    )
    session.add(reservation)
    session.commit() #DB에 저장
    session.refresh(reservation)  # DB가 생성한 id, created_at 값 반영
    return reservation  # ReservationResponse 형식으로 자동 변환

# 내 예약 목록 조회
# GET /reservations/me
# GET /reservations/me?reservation_status=active   (상태 필터)
# GET /reservations/me?reservation_status=cancelled
@router.get(
    "/reservations/me",
    response_model=list[ReservationDetailResponse],  # 주차장명 포함한 상세 응답
    status_code=status.HTTP_200_OK,
)
def get_my_reservations_handler(
    reservation_status: str | None = None,
    session: Session = Depends(get_session),
    authorization: HTTPAuthorizationCredentials | None = Depends(bearer),
):
    expire_past_reservations(session)

    # 로그인 확인
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="로그인이 필요합니다",
        )
    token_data = decode_access_token(authorization.credentials)  # Authorization 헤더에서 추출한 JWT 토큰 문자열
    user_id = token_data["user_id"]  # 토큰에서 사용자 ID 추출

    # 내 예약만 조회
    stmt = select(Reservation).where(Reservation.user_id == user_id)

    # 상태 필터 (선택적 추가 조건)
    if reservation_status:
        stmt = stmt.where(Reservation.status == reservation_status)

    # 최신 예약 먼저 정렬
    stmt = stmt.order_by(Reservation.created_at.desc())

    # 쿼리 실행 → ORM 객체 리스트로 변환
    reservations = session.execute(stmt).scalars().all()

    # 응답 데이터 조합
    result = []
    for r in reservations:
        result.append(ReservationDetailResponse(
            id=r.id,
            lot_id=r.lot_id,
            lot_name=r.lot.lot_name, # ORM relationship → ParkingInfo.lot_name
            reserved_date=r.reserved_date,
            status=r.status,
            created_at=r.created_at,
        ))
    return result


# 예약 취소
# DELETE /reservations/{reservation_id}
@router.delete(
    "/reservations/{reservation_id}",  #경로 변수
    status_code=status.HTTP_204_NO_CONTENT,
)
def cancel_reservation_handler(
        reservation_id: int, # URL의 {reservation_id} 값이 자동으로 매핑됨
        session: Session = Depends(get_session),
        authorization: HTTPAuthorizationCredentials | None = Depends(bearer),
):
    # 로그인 확인
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="로그인이 필요합니다",
        )
    token_data = decode_access_token(authorization.credentials)  # Authorization 헤더에서 추출한 JWT 토큰 문자열
    user_id = token_data["user_id"]  # 토큰에서 사용자 ID 추출

    # 본인 예약 조회
    stmt = select(Reservation).where(
        Reservation.id      == reservation_id,
        Reservation.user_id == user_id,  # 본인 예약만
    )
    reservation = session.execute(stmt).scalars().first() # 쿼리 실행 → ORM 객체 하나 반환

    # 취소 가능한 상태인지 확인
    if reservation:
        if reservation.status != "active":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, #요청 자체는 맞지만 처리할 수 없는 상태
                detail="취소 가능한 예약이 아닙니다",
            )
        # 소프트 삭제 (상태만 변경)
        # session.delete(reservation) 으로 실제 삭제하지 않고
        # status 컬럼만 'cancelled'로 변경
        reservation.status = "cancelled"
        session.commit()

        return
    # 해당 예약이 없거나 본인 예약이 아닌 경우
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="예약을 찾을 수 없습니다",
    )