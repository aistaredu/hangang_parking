# 모든 모델을 여기서 임포트
# main.py에서 "from models.models import ..." 대신 # "import models" 한 줄로 모든 모델을 Base.metadata에 등록
from models.models import ParkingInfo, ParkingDaily, Holiday, User, Reservation