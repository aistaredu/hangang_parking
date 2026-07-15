import requests
import json
import os
from dotenv import load_dotenv

#API가 실제로 어떤 데이터를 반환하는지 확인
load_dotenv()
API_KEY = os.getenv("SEOUL_API_KEY")
# url = f"http://openapi.seoul.go.kr:8088/{API_KEY}/json/TbUseDaystatusView/1/3/"
#
# res = requests.get(url, timeout=10) # API 호출
# print(json.dumps(res.json(), ensure_ascii=False, indent=2)) # 응답 출력, 응답 본문(JSON 문자열) → 파이썬 딕셔너리로 변환

#API가 반환하는 주차장명(PKLT_NM)의 전체 목록
url = f"http://openapi.seoul.go.kr:8088/{API_KEY}/json/TbUseDaystatusView/1/1000/"
res  = requests.get(url, timeout=30)
data = res.json()

rows = data["TbUseDaystatusView"]["row"]
names = sorted(set(r["PKLT_NM"] for r in rows)) # set(): 중복 제거,
dates = sorted(set(r["DT"] for r in rows))
print(f"총 {len(rows)}건")
print(f"\n날짜 범위: {dates[0]} ~ {dates[-1]}")
print(f"\n주차장명 목록 ({len(names)}개):")
for n in names:
    print(f"  {n}")