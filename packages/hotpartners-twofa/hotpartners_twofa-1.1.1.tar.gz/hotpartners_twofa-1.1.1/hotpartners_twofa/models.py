from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

# API 응답 모델

# 1단계 로그인 요청 모델
class TwoFALoginRequest(BaseModel):
    """2FA 로그인 요청"""
    user_id: str
    user_pw: str

class TwoFALoginResponse(BaseModel):
    """2FA 로그인 응답"""
    qr_code_url: str
    message: str

# 2단계 로그인 응답 모델
class TwoFAVerifyRequest(BaseModel):
    """2FA 검증 요청"""
    user_id: str
    token: str


class TwoFAVerifyResponse(BaseModel):
    """2FA 검증 응답"""
    success: bool
    message: str


# 2단계 비활성화 요청 모델
class TwoFADisableRequest(BaseModel):
    """2FA 비활성화 요청"""
    user_id: str
    token: str


class TwoFADisableResponse(BaseModel):
    """2FA 비활성화 응답"""
    success: bool
    message: str




class TwoFASetupResponse(BaseModel):
    """2FA 설정 응답"""
    qr_code_url: str
    secret_key: str
    backup_codes: List[str]
    message: str



class TwoFAAuthenticateRequest(BaseModel):
    """2FA 인증 요청 (로그인 시)"""
    user_id: str
    token: str


class TwoFAAuthenticateResponse(BaseModel):
    """2FA 인증 응답 (로그인 시)"""
    user_idx: int
    twofa_status: bool
    access_token: str
    refresh_token: str
    message: str


class TwoFABackupCodesResponse(BaseModel):
    """백업 코드 조회 응답"""
    backup_codes: List[str]
    message: str


class TwoFARegenerateBackupCodesRequest(BaseModel):
    """백업 코드 재생성 요청"""
    user_id: str
    token: str


class TwoFARegenerateBackupCodesResponse(BaseModel):
    """백업 코드 재생성 응답"""
    backup_codes: List[str]
    message: str


class TwoFAStatusResponse(BaseModel):
    """2FA 상태 조회 응답"""
    is_enabled: bool
    last_used_at: Optional[datetime]
    backup_codes_count: int
    backup_codes_count: int
