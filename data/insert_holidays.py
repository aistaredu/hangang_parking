#   Python의 holidays 라이브러리를 사용해 2022~2024년 한국 공휴일(대체공휴일 포함)을 holidays 테이블에 자동으로 삽입

import sys
import os
# 프로젝트 루트를 Python 경로에 추가 data/ 폴더에서 database/, models/ 임포트를 위해 필요
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import holidays as kr_holidays_lib
from sqlalchemy import select, func           # ORM 쿼리 도구
from database.db_connection import SessionFactory
from models.models import Holiday             # 공휴일 ORM 모델

# insert_holidays() — 공휴일 데이터 INSERT
def insert_holidays(years: list = [2022, 2023, 2024]):
    kr = kr_holidays_lib.KR(years=years) # 반환값 :  date(2024, 1, 2)  : "New Year's Day (substituted)" 대체공휴일
    with SessionFactory() as session:
        inserted = 0  # 새로 삽입한 공휴일 수
        skipped = 0  # 이미 있어서 스킵한 공휴일 수
        for d, name in sorted(kr.items()):
            #PrimaryKey이므로 중복 삽입 시 DB 오류가 발생
            stmt = select(Holiday).where(Holiday.holiday_date == d) #같은 날짜가 이미 테이블에 있는지 확인
            exists = session.scalar(stmt) #단일 결과를 반환

            if exists:
                skipped += 1
                continue
            session.add(Holiday(holiday_date=d, holiday_name=name))
            inserted += 1
        session.commit()
        print(
            f"\n 완료: {inserted}개 삽입 / "
            f"{skipped}개 스킵 ")


# 직접 실행 시 동작
if __name__ == "__main__":
    print("한국 공휴일 삽입 (2022~2024년)")
    insert_holidays()

