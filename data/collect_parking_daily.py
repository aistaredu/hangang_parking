import sys
import os
import time # API 호출 간격 조절 (time.sleep)

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # 프로젝트 루트를 Python 경로에 추가

import requests                     # HTTP API 호출 라이브러리
from datetime import datetime       # 날짜 문자열 → date 객체 변환
from collections import defaultdict # 키 없어도 기본값 반환하는 딕셔너리 (합산용)
from dotenv import load_dotenv      # .env 파일 로드
from sqlalchemy import select       # ORM 조회 쿼리 생성
from database.db_connection import SessionFactory
from models.models import ParkingInfo, ParkingDaily

# 환경변수 로드 & API 설정
load_dotenv()
API_KEY = os.getenv("SEOUL_API_KEY")
BASE_URL = f"http://openapi.seoul.go.kr:8088/{API_KEY}/json/TbUseDaystatusView" #API 공통 주소
# 실제 호출 시 BASE_URL/{시작행}/{끝행}/ 을 뒤에 붙인다

#세부 주차장명 → parking_info.id 매핑 딕셔너리
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

    "난지1,2,3,4주차장" : 6,

    "강서1주차장"       : 7,

    "양화1주차장"       : 8,
    "양화2주차장"       : 8,
    "양화3주차장"       : 8,

    "이촌1주차장"       : 9,
    "이촌2주차장"       : 9,
    "이촌3주차장"       : 9,

    "잠실1주차장"       : 10,
    "잠실2,3주차장"     : 10,

    "광나루1,2주차장"   : 11,
    "광나루3주차장"     : 11,
    "광나루4주차장"     : 11,
}

# get_total_count() — 전체 데이터 건수 조회
def get_total_count() -> int:
    url = f"{BASE_URL}/1/1/"
    res = requests.get(url, timeout=10)
    data = res.json()
    return data.get("TbUseDaystatusView", {}).get("list_total_count", 0) # 61767  전체 데이터 건수

# fetch_page(start, end) — API 페이지 단위 호출
def fetch_page(start: int, end: int) -> list:
    url = f"{BASE_URL}/{start}/{end}/"
    try:
        res = requests.get(url, timeout=30)
        data = res.json()
        rows = data.get("TbUseDaystatusView", {}).get("row", [])
        return rows
    except Exception as e:
        print(f" {start}~{end} 호출 오류: {e}")
        return []

# rows_to_daily(rows) — 세부 주차장 → 공원 단위 합산
def rows_to_daily(rows: list) -> dict:
    daily = defaultdict(int) # defaultdict(int): 존재하지 않는 키 접근 시 자동으로 0 초기화
    for row in rows:
        lot_name = str(row.get("PKLT_NM", "")).strip() #주차장명
        count_raw = row.get("PRK_CNTOM", 0) #이용대수
        dt_str = str(row.get("DT", "")) #날짜 문자열

        lot_id = LOT_NAME_MAP.get(lot_name) #주차장 매핑
        if not lot_id:
            continue #한강공원이 아닌 다른 주차장이 섞여있을 경우
        try: #데이터 변환
            use_date = datetime.strptime(dt_str, "%Y/%m/%d").date() #날짜 문자열 파싱, date():객체에서 날짜만 추출
            daily_count = int(float(count_raw)) # int 변환
        except (ValueError, TypeError):
            continue
        daily[(lot_id, use_date)] += daily_count #공원 전체 합산, 같은 날짜에 이용대수를 누적 덧셈
    return daily

# insert_daily(daily, session) — DB INSERT
def insert_daily(daily: dict, session) -> tuple:
    inserted = 0 # 이번 페이지에서 새로 삽입한 건수
    skipped = 0  # 이미 있어서 스킵한 건수

    for (lot_id, use_date), daily_count in daily.items():
        stmt = select(ParkingDaily).where(
            ParkingDaily.lot_id == lot_id,
            ParkingDaily.use_date == use_date,
        )
        exists = session.scalar(stmt)
        if exists:
            skipped += 1
            continue
        #새 데이터 삽입
        session.add(ParkingDaily(
            lot_id=lot_id,
            use_date=use_date,
            daily_count=daily_count,
        ))
        inserted += 1
    return inserted, skipped

# collect() — 전체 데이터 수집 메인 함수
def collect():
    print("한강공원 주차장 일별 데이터 수집")
    print("서비스: TbUseDaystatusView")

    #1000건 단위로 페이지 계산
    #페이지마다 fetch_page() → rows_to_daily() → insert_daily()
    #10페이지(10,000건)마다 자동 commit

    # 전체 건수 확인
    total = get_total_count() #61767건
    page_size = 1000  # 한 번 API 호출 시 가져올 행 수 (최대 1000)

    # 총 페이지 수 계산(올림)
    total_pages = (total + page_size - 1) // page_size #62페이지
    print(f"총 {total:,}건 / {page_size}건씩 {total_pages}페이지")

    total_inserted = 0
    total_skipped = 0

    with SessionFactory() as session: # 전체 수집을 하나의 세션으로 처리
        for page in range(total_pages): # 페이지마다 1000건의 데이터 수집
            #행 범위 계산  page=0: start=1,    end=1000   page=1: start=1001, end=2000
            start = page * page_size + 1
            end = min(start + page_size - 1, total) #page=61: start=61001, end=61767

            #API 호출
            rows = fetch_page(start, end)
            if not rows:
                print(f"  [{page + 1}/{total_pages}] 데이터 없음, 스킵")
                continue
            # 세부 주차장 → 공원 단위 합산
            daily = rows_to_daily(rows)

            # DB INSERT
            ins, skp = insert_daily(daily, session)

            session.commit() # 페이지 단위로 commit

            total_inserted += ins
            total_skipped += skp

            ##프로그레스 바 표시
            pct = (page + 1) / total_pages * 100
            bar = "█" * int(pct / 5) #0~100%를 0~20 단계로 변환
            print(f"  [{bar:<20}] {page + 1}/{total_pages} | +{ins}건 삽입 | {skp}건 스킵", end="\r")
            time.sleep(0.1) #API 부하 방지  0.1초 대기

    print(f"\n\n수집 완료! 삽입 {total_inserted:,}건 / 스킵 {total_skipped:,}건")

# 직접 실행 시 동작
if __name__ == "__main__":
    collect() #전체 수집 실행