# 주차장 관련 API — CRUD 5개
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from starlette import status

from database.db_connection import get_session
from models.models import ParkingInfo
from schema.request import ParkingCreateRequest, ParkingUpdateRequest
from schema.response import ParkingInfoResponse, ParkingListResponse
from auth.jwt import decode_access_token

#라우터(router): 관련 API들을 한 파일로 묶은 단위
#라우팅(routing): 요청(HTTP메서드+URL)을 어떤 함수가 처리할지 연결하는 과정
router = APIRouter(tags=["주차장"])

# HTTPBearer(): 요청 헤더의 'Authorization: Bearer <토큰>' 을 자동으로 파싱하는 객체
# auto_error=False: Authorization 헤더가 없어도 오류 없이 None 반환
# 없으면 None, 있으면 HTTPAuthorizationCredentials 객체 반환
bearer = HTTPBearer(auto_error=False)

# 전체 주차장 목록 조회 (페이지네이션 포함), 로그인 불필요 — 누구나 조회 가능
@router.get( # GET /parking-lots?page=1&size=9
    "/parking-lots",
    response_model=ParkingListResponse, # 목록 + 총 개수 + 페이지 정보 반환
    status_code=status.HTTP_200_OK,
)
def get_parking_lots_handler(
    # Query(): URL 쿼리 파라미터 — ?page=1&size=9 형태로 전달
    page: int = Query(default=1,  ge=1,  description="페이지 번호 (기본: 1)"),
    size: int = Query(default=9,  ge=1,  le=100, description="페이지당 항목 수 (기본: 9)"),
    session: Session = Depends(get_session),
):
    #전체 주차장 수 조회
    total = session.scalar(select(func.count(ParkingInfo.id)))

    # 페이지네이션 계산
    offset = (page - 1) * size # 몇 번째 행부터 가져올지

    #데이터 조회
    stmt = (
        select(ParkingInfo)
        .order_by(ParkingInfo.id)  # id 오름차순 정렬
        .offset(offset) #앞의 offset개 행 건너뜀
        .limit(size) #최대 size개만 가져옴
    )
    lots = session.execute(stmt).scalars().all() #쿼리를 실제 DB에 전달해 실행, 결과를 ORM 객체 리스트로 변환
    return ParkingListResponse(total=total, page=page, size=size, items=lots)

# 단일 주차장 조회
@router.get(
    "/parking-lots/{lot_id}", # {lot_id}: 경로 변수 — URL에서 추출해 함수 매개변수로 전달
    response_model=ParkingInfoResponse,
    status_code=status.HTTP_200_OK,
)
def get_parking_lot_handler(
    lot_id : int,
    session: Session = Depends(get_session),
):
    stmt = select(ParkingInfo).where(ParkingInfo.id == lot_id)
    lot = session.execute(stmt).scalars().first() #첫 번째 결과만 반환, 없으면 None
    if lot:
        return lot
    raise HTTPException( # 조회 실패 시 예외 처리
        status_code=status.HTTP_404_NOT_FOUND,
        detail="주차장을 찾을 수 없습니다",
    )

# 주차장 등록 (관리자 전용)
@router.post(
    "/parking-lots",
    response_model=ParkingInfoResponse,
    status_code=status.HTTP_201_CREATED, # 생성 성공
)
def create_parking_lot_handler(
    body   : ParkingCreateRequest, #요청 본문
    session: Session = Depends(get_session),
    authorization: HTTPAuthorizationCredentials | None = Depends(bearer),
    # Depends(bearer): 요청 전에 HTTPBearer를 먼저 실행 → Authorization 헤더 파싱
    # 헤더가 있으면 HTTPAuthorizationCredentials 객체, 없으면 None
):
    #관리자 권한 확인
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, # 401: 인증 안 됨 (로그인 필요)
            detail="로그인이 필요합니다",
        )
    token_data = decode_access_token(authorization.credentials)  #authorization.credentials: 실제 JWT 토큰 문자열
    if token_data["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, # 403: 인증은 됐지만 권한 없음 (로그인은 했지만 관리자 아님)
            detail="관리자 권한이 필요합니다",
        )

    #주차장 객체 생성 & 저장
    lot = ParkingInfo(
        lot_name=body.lot_name,
        district=body.district,
        capacity=body.capacity,
        lat=body.lat,
        lng=body.lng,
    )
    session.add(lot)  # 세션에 등록 (아직 DB에 저장 안 됨)
    session.commit()  # DB에 실제 저장 (SQL INSERT 실행)
    session.refresh(lot)  # DB가 생성한 id, created_at 값을 lot 객체에 반영
    return lot

# 주차장 수정 (관리자 전용)
@router.patch(
    "/parking-lots/{lot_id}",
    response_model=ParkingInfoResponse,
    status_code=status.HTTP_200_OK,
)
def update_parking_lot_handler(
    lot_id : int,
    body   : ParkingUpdateRequest,
    session: Session = Depends(get_session),
    authorization: HTTPAuthorizationCredentials | None = Depends(bearer),
):
    # 관리자 권한 확인
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,  # 401: 인증 안 됨 (로그인 필요)
            detail="로그인이 필요합니다",
        )
    token_data = decode_access_token(authorization.credentials)  # authorization.credentials: 실제 JWT 토큰 문자열
    if token_data["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,  # 403: 인증은 됐지만 권한 없음 (로그인은 했지만 관리자 아님)
            detail="관리자 권한이 필요합니다",
        )
    stmt = select(ParkingInfo).where(ParkingInfo.id == lot_id)
    lot  = session.execute(stmt).scalars().first()

    if lot:
        #수정 허용 필드만 선택적으로 업데이트
        # body.model_dump():Pydantic 모델을 dict로 변환, exclude_unset=True: 클라이언트가 실제로 보낸 필드만 포함
        update_data = body.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(lot, key, value)  # lot.lot_name = value 와 동일
        session.commit()
        return lot
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="주차장을 찾을 수 없습니다")

# 주차장 삭제 (관리자 전용)
@router.delete(
    "/parking-lots/{lot_id}",
    status_code=status.HTTP_204_NO_CONTENT, #요청은 성공했지만 반환할 본문이 없음
)
def delete_parking_lot_handler(
    lot_id : int,
    session: Session = Depends(get_session),
    authorization: HTTPAuthorizationCredentials | None = Depends(bearer),
):
    # 관리자 권한 확인
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,  # 401: 인증 안 됨 (로그인 필요)
            detail="로그인이 필요합니다",
        )
    token_data = decode_access_token(authorization.credentials)  # authorization.credentials: 실제 JWT 토큰 문자열
    if token_data["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,  # 403: 인증은 됐지만 권한 없음 (로그인은 했지만 관리자 아님)
            detail="관리자 권한이 필요합니다",
        )
    stmt = select(ParkingInfo).where(ParkingInfo.id == lot_id)
    lot = session.execute(stmt).scalars().first()
    if lot:
        session.delete(lot)  # 세션에서 삭제 대상으로 지정
        session.commit()  # DB에서 실제 삭제 (SQL DELETE 실행)
        return  # 204이므로 본문 없이 반환
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="주차장을 찾을 수 없습니다")




