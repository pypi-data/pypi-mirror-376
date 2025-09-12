import os

from cryptography.fernet import Fernet

from src.common.conf.settings import settings

# 인증앱에서 보일 이름
TWOFA_ISSUER_NAME: str = os.getenv('TWOFA_ISSUER_NAME', 'HotPartners')
# 인증시간 허용 윈도우 1 -> 30초 2 -> 앞뒤 30초 더 허용
TWOFA_WINDOW_SIZE: int = int(os.getenv('TWOFA_WINDOW_SIZE', '2'))
# 백업 코드 개수
TWOFA_BACKUP_CODES_COUNT: int = int(os.getenv('TWOFA_BACKUP_CODES_COUNT', '8'))
# 최대 재시도 횟수
TWOFA_MAX_RETRY_ATTEMPTS: int = int(os.getenv('TWOFA_MAX_RETRY_ATTEMPTS', '5'))
# 재시도 5분
TWOFA_RETRY_WINDOW_MINUTES: int = int(os.getenv('TWOFA_RETRY_WINDOW_MINUTES', '5'))
# 관리자 테이블 이름


class TwoFAConfig:
    def __init__(self):
        self.FERNET_KEY = settings.FERNET_KEY
        self.TWOFA_ISSUER_NAME = TWOFA_ISSUER_NAME
        self.TWOFA_WINDOW_SIZE = TWOFA_WINDOW_SIZE
        self.TWOFA_BACKUP_CODES_COUNT = TWOFA_BACKUP_CODES_COUNT
        self.TWOFA_MAX_RETRY_ATTEMPTS = TWOFA_MAX_RETRY_ATTEMPTS
        self.TWOFA_RETRY_WINDOW_MINUTES = TWOFA_RETRY_WINDOW_MINUTES
        self.fernet = Fernet(self.FERNET_KEY)


    def get_fernet_key(self):
        return self.FERNET_KEY

    def get_twofa_issuer_name(self):
        return self.TWOFA_ISSUER_NAME

    def get_twofa_window_size(self):
        return self.TWOFA_WINDOW_SIZE

    def get_twofa_backup_codes_count(self):
        return self.TWOFA_BACKUP_CODES_COUNT

    def get_twofa_max_retry_attempts(self):
        return self.TWOFA_MAX_RETRY_ATTEMPTS

    def get_twofa_retry_window_minutes(self):
        return self.TWOFA_RETRY_WINDOW_MINUTES

    def encrypt_data(self, data: str) -> str:
        """주어진 데이터를 암호화합니다."""
        return self.fernet.encrypt(data.encode()).decode()

    def decrypt_data(self, encrypted_data: str) -> str:
        """암호화된 데이터를 복호화합니다."""
        return self.fernet.decrypt(encrypted_data.encode()).decode()