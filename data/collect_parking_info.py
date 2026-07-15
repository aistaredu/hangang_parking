import sys
import os

# sys.path.append()로 프로젝트 루트를 추가해야 임포트가 동작, 이 경로에서 모듈을 찾을 수 있게
# D:\kwu\hangang_parking\data\collect_parking_info.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 경로 추가 후 프로젝트 내 모듈 임포트 가능
from database.db_connection import SessionFactory
from models.models import ParkingInfo

# 한강공원 주차장 11개소 데이터 (상수)
HANGANG_LOTS = [
    # id=1: 뚝섬
    {"lot_name": "뚝섬한강공원주차장",   "district": "뚝섬지구",   "capacity": 458, "lat": 37.5302, "lng": 127.0688},
    # id=2: 여의도
    {"lot_name": "여의도한강공원주차장",  "district": "여의도지구", "capacity": 532, "lat": 37.5285, "lng": 126.9337},
    # id=3: 반포
    {"lot_name": "반포한강공원주차장",   "district": "반포지구",   "capacity": 390, "lat": 37.5126, "lng": 126.9995},
    # id=4: 잠원
    {"lot_name": "잠원한강공원주차장",   "district": "잠원지구",   "capacity": 155, "lat": 37.5166, "lng": 126.9994},
    # id=5: 망원
    {"lot_name": "망원한강공원주차장",   "district": "망원지구",   "capacity": 298, "lat": 37.5494, "lng": 126.8975},
    # id=6: 난지
    {"lot_name": "난지한강공원주차장",   "district": "난지지구",   "capacity": 610, "lat": 37.5663, "lng": 126.8906},
    # id=7: 강서
    {"lot_name": "강서한강공원주차장",   "district": "강서지구",   "capacity": 425, "lat": 37.5736, "lng": 126.8241},
    # id=8: 양화
    {"lot_name": "양화한강공원주차장",   "district": "양화지구",   "capacity": 124, "lat": 37.5454, "lng": 126.9101},
    # id=9: 이촌
    {"lot_name": "이촌한강공원주차장",   "district": "이촌지구",   "capacity": 303, "lat": 37.5210, "lng": 126.9726},
    # id=10: 잠실
    {"lot_name": "잠실한강공원주차장",   "district": "잠실지구",   "capacity": 390, "lat": 37.5200, "lng": 127.0818},
    # id=11: 광나루
    {"lot_name": "광나루한강공원주차장", "district": "광나루지구", "capacity": 450, "lat": 37.5492, "lng": 127.1266},
]

# 주차장 데이터 INSERT, 테이블에 삽입
def insert_parking_info():
    with SessionFactory() as session:
        for lot_data in HANGANG_LOTS:
            lot = ParkingInfo(
                lot_name=lot_data["lot_name"],
                district=lot_data["district"],
                capacity=lot_data["capacity"],
                lat=lot_data["lat"],
                lng=lot_data["lng"],
            )
            session.add(lot)
        session.commit() #세션에 add()된 모든 객체를 DB에 실제로 저장
        print(f"\n parking_info INSERT 완료: {len(HANGANG_LOTS)}개소")

# 직접 실행 시 동작, python data/collect_parking_info.py 로 실행할 때만 동작
if __name__ == "__main__":
    print("한강공원 주차장 기본 정보 수집")
    insert_parking_info()