import sys
import os
import time                          # API 호출 간격 조절 (time.sleep)

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # 프로젝트 루트를 Python 경로에 추가

import requests                     # HTTP API 호출 라이브러리
import xml.etree.ElementTree as ET  # XML 응답 파싱 (info API는 xml 포맷)
from collections import defaultdict # 키 없어도 기본값 반환하는 딕셔너리 (합산용)
from dotenv import load_dotenv      # .env 파일 로드
from sqlalchemy import select       # ORM 조회 쿼리 생성
from database.db_connection import SessionFactory
from models.models import ParkingInfo, ParkingDaily

# 환경변수 로드 & API 설정
load_dotenv()
API_KEY = os.getenv("SEOUL_API_KEY")
BASE_URL = f"http://openapi.seoul.go.kr:8088/{API_KEY}/xml/TbParkingInfoView" # API 공통 주소
# 실제 호출 시 BASE_URL/{시작행}/{끝행}/ 을 뒤에 붙인다

# 세부 주차장명 → parking_info.id 매핑 딕셔너리
LOT_NAME_MAP = {
    "뚝섬1주차장"        : 1,
    "뚝섬2주차장"        : 1,
    "뚝섬3주차장"        : 1,
    "뚝섬4주차장"        : 1,

    "여의도1주차장"      : 2,
    "여의도2주차장"      : 2,
    "여의도3주차장"      : 2,
    "여의도4주차장"      : 2,
    "여의도5주차장"      : 2,

    "반포1주차장"       : 3,
    "반포2,3주차장"     : 3,

    "잠원1주차장"       : 4,
    "잠원2-6주차장"     : 4,

    "망원1주차장"       : 5,
    "망원2주차장"       : 5,
    "망원4주차장"       : 5,

    "난지1,2,3,4주차장" : 6,

    "강서1주차장"       : 7,

    "양화1주차장"       : 8,
    "양화2주차장"       : 8,
    "양화3주차장"       : 8,

    "이촌1주차장"       : 9,
    "이촌2주차장"       : 9,
    "이촌3주차장"       : 9,
    "이촌4주차장"       : 9,

    "잠실1주차장"       : 10,
    "잠실2,3주차장"     : 10,

    "광나루1,2주차장"   : 11,
    "광나루3주차장"     : 11,
    "광나루4주차장"     : 11,
}

# lot_id → 공원 기본 정보 (이름/지구/좌표) — DB INSERT 시 사용
LOT_INFO = {
    1 : {"lot_name": "뚝섬한강공원주차장",   "district": "뚝섬지구",   "lat": 37.5302, "lng": 127.0688},
    2 : {"lot_name": "여의도한강공원주차장",  "district": "여의도지구", "lat": 37.5285, "lng": 126.9337},
    3 : {"lot_name": "반포한강공원주차장",   "district": "반포지구",   "lat": 37.5126, "lng": 126.9995},
    4 : {"lot_name": "잠원한강공원주차장",   "district": "잠원지구",   "lat": 37.5166, "lng": 126.9994},
    5 : {"lot_name": "망원한강공원주차장",   "district": "망원지구",   "lat": 37.5494, "lng": 126.8975},
    6 : {"lot_name": "난지한강공원주차장",   "district": "난지지구",   "lat": 37.5663, "lng": 126.8906},
    7 : {"lot_name": "강서한강공원주차장",   "district": "강서지구",   "lat": 37.5736, "lng": 126.8241},
    8 : {"lot_name": "양화한강공원주차장",   "district": "양화지구",   "lat": 37.5454, "lng": 126.9101},
    9 : {"lot_name": "이촌한강공원주차장",   "district": "이촌지구",   "lat": 37.5210, "lng": 126.9726},
    10: {"lot_name": "잠실한강공원주차장",   "district": "잠실지구",   "lat": 37.5200, "lng": 127.0818},
    11: {"lot_name": "광나루한강공원주차장", "district": "광나루지구", "lat": 37.5492, "lng": 127.1266},
}

# get_total_count() — 전체 데이터 건수 조회
def get_total_count() -> int:
    url = f"{BASE_URL}/1/1/"
    res = requests.get(url, timeout=10)
    root = ET.fromstring(res.text)                       # XML 문자열 → 트리 객체
    return int(root.findtext("list_total_count", "0"))   # 30  전체 주차장 건수

# fetch_page(start, end) — API 페이지 단위 호출
def fetch_page(start: int, end: int) -> list:
    url = f"{BASE_URL}/{start}/{end}/"
    try:
        res = requests.get(url, timeout=30)
        root = ET.fromstring(res.text)                   # XML 파싱
        rows = root.findall("row")                       # <row> 요소 목록
        return rows
    except Exception as e:
        print(f" {start}~{end} 호출 오류: {e}")
        return []

# rows_to_capacity(rows) — 세부 주차장 → 공원 단위 면수 합산
def rows_to_capacity(rows: list) -> dict:
    capacity = defaultdict(int) # defaultdict(int): 존재하지 않는 키 접근 시 자동으로 0 초기화
    for row in rows:
        lot_name = str(row.findtext("PKLT_TYPE", "")).strip() # 세부 주차장명
        cnt_raw = row.findtext("PRK_CNT", "0")                # 주차 면수

        lot_id = LOT_NAME_MAP.get(lot_name) # 주차장 매핑
        if not lot_id:
            continue # 한강공원이 아닌 다른 주차장이 섞여있을 경우
        try: # 데이터 변환
            capacity[lot_id] += int(cnt_raw) # 공원 전체 합산, 같은 공원 면수를 누적 덧셈
        except (ValueError, TypeError):
            continue
    return capacity

# insert_info(capacity, session) — DB INSERT (기존 전체 삭제 후 재삽입)
def insert_info(capacity: dict, session) -> int:
    inserted = 0 # 새로 삽입한 건수

    deleted = session.query(ParkingInfo).delete() # 기존 레코드 전체 삭제
    if deleted:
        print(f"  기존 {deleted}개 레코드 삭제")

    for lot_id, info in LOT_INFO.items():
        actual_capacity = capacity.get(lot_id, 0) # 매핑 없으면 0

        if actual_capacity == 0:
            print(f"  lot_id={lot_id} {info['lot_name']}: 면수 0 (API 미매핑 확인 필요)")

        # 새 데이터 삽입
        session.add(ParkingInfo(
            lot_name=info["lot_name"],
            district=info["district"],
            capacity=actual_capacity,
            lat=info["lat"],
            lng=info["lng"],
        ))
        inserted += 1
    return inserted

# update_capacity(capacity, session) — capacity 컬럼만 수정 (parking_daily 보존)
def update_capacity(capacity: dict, session) -> tuple:
    updated = 0 # 실제로 수정한 건수
    skipped = 0 # 변경 없거나 매핑 없어 스킵한 건수

    lots = session.execute(
        select(ParkingInfo).order_by(ParkingInfo.id)
    ).scalars().all()

    for lot in lots:
        new_cap = capacity.get(lot.id, 0) # 새 면수
        if new_cap == 0 or lot.capacity == new_cap: # 매핑 없거나 값 동일하면
            skipped += 1
            continue
        lot.capacity = new_cap # 면수만 수정
        updated += 1
    return updated, skipped

# collect() — 전체 데이터 수집 메인 함수
def collect():
    print("한강공원 주차장 기본 정보 수집")
    print("서비스: TbParkingInfoView")

    # 전체 건수 확인 → 한 번에 전체 조회 → 공원 단위 합산
    # parking_daily 데이터가 있으면 FK 제약 때문에 삭제 불가 → capacity만 update

    # 전체 건수 확인
    total = get_total_count() # 30건
    print(f"총 {total:,}건 조회")

    # 전체 데이터를 한 번에 호출 (건수가 적어 페이지 분할 불필요)
    rows = fetch_page(1, total)
    print(f"{len(rows)}개 row 수신")

    # 세부 주차장 → 공원 단위 면수 합산
    capacity = rows_to_capacity(rows)

    # 공원별 합산 면수 출력
    print("\n공원별 합산 면수:")
    for lot_id, cap in sorted(capacity.items()):
        lot_name = LOT_INFO.get(lot_id, {}).get("lot_name", f"lot_id={lot_id}")
        print(f"  {lot_name}: {cap}면")

    with SessionFactory() as session: # 전체 수집을 하나의 세션으로 처리
        # parking_daily에 데이터가 있으면 FK 제약으로 INSERT(전체 삭제) 불가
        daily_count = session.query(ParkingDaily).count()

        if daily_count > 0:
            # daily 데이터 보존 → capacity만 안전하게 수정
            print(f"\nparking_daily에 {daily_count:,}건 존재 → capacity만 업데이트")
            upd, skp = update_capacity(capacity, session)
            session.commit() # 변경사항 저장
            print(f"수집 완료! 수정 {upd}건 / 스킵 {skp}건")
        else:
            # 빈 테이블 → 전체 삭제 후 재삽입
            print("\nparking_info INSERT 중...")
            ins = insert_info(capacity, session)
            session.commit() # 변경사항 저장
            print(f"수집 완료! 삽입 {ins}건")

    verify()

# verify() — parking_info 테이블 현황 출력
def verify():
    with SessionFactory() as session:
        lots = session.execute(
            select(ParkingInfo).order_by(ParkingInfo.id)
        ).scalars().all()

        print(f"\n[parking_info 현황] 총 {len(lots)}개소")
        for lot in lots:
            print(
                f"  {lot.id:>3}. {lot.lot_name:<24} "
                f"{lot.capacity:>5}면  "
                f"{float(lot.lat):>9.4f}  {float(lot.lng):>10.4f}"
            )

# 직접 실행 시 동작
if __name__ == "__main__":
    collect() # 전체 수집 실행
