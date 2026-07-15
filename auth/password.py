# 비밀번호 해싱 모듈

from pwdlib import PasswordHash  # 비밀번호 해싱과 검증 로직을 한곳에서 일관되게 관리

password_hasher = PasswordHash.recommended() #현재 권장하는 해싱 알고리즘(argon2)으로 설정 객체 생성

# 평문 비밀번호 → 복원할 수 없는 해시 문자열로 변환 (회원가입 시 사용)
# 해시값만 DB에 저장되고 평문 비밀번호는 시스템 내부에 남지 않는다
def hash_password(plain_password: str) -> str:
    return password_hasher.hash(plain_password)

# 평문 비밀번호와 DB에 저장된 해시값을 비교 (로그인 시 사용)
# 반환값 True: 비밀번호 일치 (로그인 성공) / False: 불일치 (로그인 실패)
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hasher.verify(plain_password, hashed_password) 