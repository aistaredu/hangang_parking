# 데이터베이스 연결 설정

from sqlalchemy import create_engine # 엔진(engine): 데이터베이스와의 실제 연결을 관리하는 객체
from sqlalchemy.orm import sessionmaker # 세션(session): ORM이 데이터베이스와 상호작용할 때 사용하는 작업 단위
from dotenv import load_dotenv
import os

load_dotenv()   # .env 파일 로드 → os.getenv()로 값을 읽을 수 있게 된다

# 데이터베이스 연결 URL 구성
# 형식: mysql+pymysql://사용자명:비밀번호@호스트:포트/데이터베이스명
DATABASE_URL = (
    f"mysql+pymysql://"
    f"{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT', '3306')}"
    f"/{os.getenv('DB_NAME')}?charset=utf8mb4"
)

# 엔진 생성
# 데이터베이스와 통신할 수 있는 엔진
# echo=True: 실행되는 SQL 쿼리가 터미널 로그로 출력됨
engine = create_engine(DATABASE_URL, echo=True)

# SessionFactory()를 호출할 때마다 새 세션 생성
SessionFactory = sessionmaker(
    autocommit=False, # 개발자가 commit()을 호출해야 변경 사항이 확정됨
    autoflush=False, # 개발자가 flush()를 호출해야 쿼리가 실행됨
    bind=engine, # 이 세션이 사용할 데이터베이스 엔진 지정
)

# 세션 생성 함수
# 요청이 들어올 때마다 새로운 데이터베이스 세션을 생성하고
# API 처리가 끝나면 자동으로 세션을 정리 (with 문이 처리)
# 라우터에서 Depends(get_session)으로 주입받아 사용
def get_session():
    with SessionFactory() as session:
        yield session
