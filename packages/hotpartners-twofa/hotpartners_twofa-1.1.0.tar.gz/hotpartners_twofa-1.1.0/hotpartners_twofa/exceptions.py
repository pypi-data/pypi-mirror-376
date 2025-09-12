class TwoFAException(Exception):
    """2FA 기본 예외 클래스"""
    pass

class TwoFAUserNotFoundException(TwoFAException):
    """사용자를 찾을 수 없는 경우"""
    def __init__(self, message: str = "사용자 정보가 존재하지 않습니다."):
        self.message = message
        super().__init__(self.message)


class TwoFAInvalidTokenException(TwoFAException):
    """잘못된 2FA 토큰"""
    def __init__(self, message: str = "유효하지 않은 2FA 토큰 입니다."):
        self.message = message
        super().__init__(self.message)



class TwoFANotEnabledException(TwoFAException):
    """2FA가 활성화되지 않은 경우"""
    def __init__(self, message: str = "2FA가 활성화 되지 않았습니다."):
        self.message = message
        super().__init__(self.message)




class TwoFAMaxRetryExceededException(TwoFAException):
    """최대 재시도 횟수 초과"""
    def __init__(self, message: str = "Maximum retry attempts exceeded"):
        self.message = message
        super().__init__(self.message)


class TwoFABackupCodeNotFoundException(TwoFAException):
    """백업 코드를 찾을 수 없는 경우"""
    def __init__(self, message: str = "Backup code not found"):
        self.message = message
        super().__init__(self.message)


class TwoFASetupRequiredException(TwoFAException):
    """2FA 설정이 필요한 경우"""
    def __init__(self, message: str = "2FA setup required"):
        self.message = message
        super().__init__(self.message)

