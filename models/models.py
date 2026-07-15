# ORM 모델 정의

#   ORM 모델 = 파이썬 클래스로 DB 테이블을 표현
#   이 파일의 클래스 1개 = MySQL 테이블 1개
#   클래스 속성 1개 = 테이블 컬럼 1개

from datetime import datetime, date
from sqlalchemy import (
    Integer, String, Boolean,
    ForeignKey, DateTime, Date, Numeric,
    UniqueConstraint, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
# Mapped      : 이 속성이 ORM에 의해 관리되는 칼럼임을 나타내는 타입 힌트, 이 속성의 파이썬 타입 선언
# mapped_column: 파이썬 클래스의 속성을 데이터베이스 칼럼으로 연결하는 함수
from database.orm import Base  # ORM 부모 클래스 — 이걸 상속해야 SQLAlchemy가 테이블로 인식

# ParkingInfo — 주차장 기본 정보
class ParkingInfo(Base):
    __tablename__ = "parking_info"
    # 컬럼 정의
    id: Mapped[int] = mapped_column( #실제 DB 컬럼 설정
        Integer,
        primary_key=True,
        autoincrement=True, #자동으로 1씩 증가
    )
    lot_name: Mapped[str] = mapped_column(
        String(60),
        nullable=False,  # NOT NULL: 반드시 값이 있어야 함
    )
    district: Mapped[str] = mapped_column( # 지구명
        String(30),
        nullable=False,
    )
    capacity: Mapped[int] = mapped_column( # 총 주차면수
        Integer,
        nullable=False,
    )
    lat: Mapped[float] = mapped_column( #위도
        Numeric(10, 7),  # DECIMAL(10,7): 소수점 7자리
        nullable=False,
    )
    lng: Mapped[float] = mapped_column( #경도
        Numeric(10, 7),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(), #MySQL 서버의 NOW() 자동 실행
        nullable=False,
    )
    #ORM 관계 설정 (Relationship)
    #SQL JOIN 없이 관련 객체에 파이썬 속성으로 접근할 수 있게 해준다.
    #lot = session.get(ParkingInfo, 1)
    #lot.daily_records  → 이 주차장의 모든 일별 데이터 리스트
    #lot.reservations   → 이 주차장의 모든 예약 리스트
    daily_records: Mapped[list["ParkingDaily"]] = relationship(
        back_populates="lot", # ParkingDaily.lot 과 양방향 연결
        cascade="all, delete-orphan", # 주차장 삭제 시 일별 데이터도 함께 삭제
    )
    reservations: Mapped[list["Reservation"]] = relationship(
        back_populates="lot",  # Reservation.lot 과 양방향 연결
    )

# ParkingDaily — 일별 이용 현황 (ML 학습 핵심 데이터)
class ParkingDaily(Base):
    __tablename__ = "parking_daily"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lot_id: Mapped[int] = mapped_column( # 어느 주차장 데이터인지
        ForeignKey("parking_info.id"), # 외래키: parking_info 테이블의 id 참조
        nullable=False,
    )
    use_date: Mapped[date] = mapped_column(
        Date, # DATE 타입: 날짜만 저장
        nullable=False,
    )
    daily_count: Mapped[int] = mapped_column( # 당일 총 입차 대수
        Integer,
        nullable=False,
    )
    # 같은 날(use_date) 같은 주차장(lot_id) 데이터는 1개만 허용
    # DB 수준에서 중복 INSERT를 방지
    __table_args__ = (
        UniqueConstraint("lot_id", "use_date", name="uq_lot_date"),
    )
    # ORM 관계: daily.lot → 이 데이터가 속한 주차장 객체
    lot: Mapped["ParkingInfo"] = relationship(
        back_populates="daily_records",
    )

# Holiday — 공휴일
class Holiday(Base):
        __tablename__ = "holidays"

        holiday_date: Mapped[date] = mapped_column(
            Date,
            primary_key=True,
        )
        holiday_name: Mapped[str] = mapped_column(
            String(50), # 예) "설날"
            nullable=False,
        )

# User — 회원
class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(
            String(255),
            unique=True, # UNIQUE: 같은 이메일로 중복 가입 불가
            index=True,  # INDEX 생성: 이메일로 조회할 때 속도 향상
            nullable=False,
        )
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="user", # "user": 일반 사용자 / "admin": 관리자
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )
    # ORM 관계: user.reservations → 이 회원의 예약 목록
    reservations: Mapped[list["Reservation"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",  # 회원 삭제 시 예약도 함께 삭제
    )

# Reservation — 예약
class Reservation(Base):
    __tablename__ = "reservation"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.id"), # user 테이블의 id 참조
        nullable=False,
    )
    lot_id: Mapped[int] = mapped_column(
        ForeignKey("parking_info.id"),  # parking_info 테이블의 id 참조
        nullable=False,
    )
    reserved_date: Mapped[date] = mapped_column( # 예약 날짜
        Date,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="active",  # "active": 예약중 / "completed": 완료 / "cancelled": 취소
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )
    # ORM 관계 양방향 연결
    # reservation.user → 예약한 회원 객체
    # reservation.lot  → 예약된 주차장 객체
    user: Mapped["User"] = relationship(back_populates="reservations")
    lot: Mapped["ParkingInfo"] = relationship(back_populates="reservations")


