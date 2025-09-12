import base64
import secrets
import string
from datetime import datetime, timedelta
from io import BytesIO
from typing import Any, Dict, List

import bcrypt
import pyotp
import qrcode
from fastapi import Request

from src.apps.server.exception import ErrorCode, JSendError
from src.common.utils.auth import issue_tokens
from src.common.utils.logger import set_logger

from .exceptions import (
    TwoFAInvalidTokenException,
    TwoFANotEnabledException,
    TwoFAUserNotFoundException,
)
from .models import (
    TwoFAAuthenticateResponse,
    TwoFABackupCodesResponse,
    TwoFADisableResponse,
    TwoFALoginResponse,
    TwoFARegenerateBackupCodesResponse,
    TwoFASetupResponse,
    TwoFAStatusResponse,
    TwoFAVerifyResponse,
)
from .repository import TwoFARepository

LOGGER = set_logger("twofa.service")


class TwoFAService:
    """2FA 서비스 클래스"""

    def __init__(self, repository: TwoFARepository):
        self.repository = repository
        self.config = repository.config

    def _generate_backup_codes(self, count: int = 8) -> List[str]:
        """백업 코드 생성"""
        if count == 8:  # 기본값인 경우 설정값 사용
            count = self.config.get_twofa_backup_codes_count()

        backup_codes = []
        for _ in range(count):
            # 8자리 대문자 + 숫자 조합
            code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
            backup_codes.append(code)

        return backup_codes

    def _generate_qr_code(self, secret: str, user_id: str) -> str:
        """QR 코드 생성"""
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(
            name=user_id,
            issuer_name=self.config.get_twofa_issuer_name()
        )

        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buf = BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)

        # Base64 인코딩하여 반환
        return base64.b64encode(buf.getvalue()).decode()

    async def verify_2fa_login(
        self,
        request: Request,
        user_id: str,
        user_pw: str
    ) -> TwoFALoginResponse:
        """2FA 로그인"""
        try:
            # 접속 IP 추출
            client_ip = request.client.host if request.client else "unknown"
            forwarded_for = request.headers.get("X-Forwarded-For")
            real_ip = request.headers.get("X-Real-IP")
            request_ip = real_ip or (forwarded_for.split(',')[0].strip() if forwarded_for else None) or client_ip

            LOGGER.info(
                f"""
                    ["2FA login request_ip: {request_ip}"]
                """
            )
            if not user_id or not user_pw:
                raise TwoFAUserNotFoundException()

            # 1. 사용자 존재 확인
            user_info = await self.repository.get_user_by_id(
                user_id=user_id
            )
            if not user_info:
                raise TwoFAUserNotFoundException()

            check_pw = bcrypt.checkpw(
                user_pw.encode("utf-8"), user_info["password"].encode("utf-8")
            )
            if not check_pw:
                raise TwoFAUserNotFoundException()

            LOGGER.info(
                f"""
                    ["2FA login user_info: {user_info['id']}"]
                """
            )

            # 2. 이미 2FA가 활성화된 경우 조기 종료
            if user_info.get('is_2fa_enabled'):
                return TwoFALoginResponse(
                    qr_code_url="",
                    message="1단계 인증 완료 되었습니다. 2단계 인증을 진행해주세요."
                )

            LOGGER.info(
                f"""
                    ["QR code 인증 필요"]
                    ["2FA login user: {user_info['id']}"]
                """
            )

            # 3. 2FA 설정 시작
            ret =  await self.setup_2fa(user_id)
            return TwoFALoginResponse(
                qr_code_url=ret.qr_code_url,
                message=ret.message
            )

        except Exception as e:
            LOGGER.error(f"login_2fa error: {e}")
            raise JSendError(
                code=ErrorCode.Common.INTERNAL_SERVER_ERROR[0],
                message=str(e),
            )

    async def setup_2fa(self, user_id: str) -> TwoFASetupResponse:
        """2FA 설정 시작"""
        try:
            # OTP 비밀키 생성
            secret = pyotp.random_base32()

            # 백업 코드 생성
            backup_codes = self._generate_backup_codes()

            # QR 코드 생성
            qr_code_base64 = self._generate_qr_code(secret, user_id)

            # DB에 저장 (아직 활성화 되지 않음)
            ret = await self.repository.upsert_user_2fa_status(
                user_id=user_id,
                otp_secret=secret,
                backup_codes=backup_codes,
                is_2fa_enabled=False
            )
            if not ret:
                raise JSendError(
                    code=ErrorCode.Common.INTERNAL_SERVER_ERROR[0],
                    message="2FA 설정에 실패했습니다.",
                )

            LOGGER.info(f"2FA setup initiated for user: {user_id}")

            return TwoFASetupResponse(
                qr_code_url=f"data:image/png;base64,{qr_code_base64}",
                secret_key=secret,
                backup_codes=backup_codes,
                message="2FA 설정을 시작했습니다. QR 코드를 스캔하고 6자리 코드를 입력하세요."
            )

        except Exception as e:
            LOGGER.error(f"setup_2fa error: {e}")
            raise JSendError(
                code=ErrorCode.Common.INTERNAL_SERVER_ERROR[0],
                message=str(e),
            )

    async def verify_2fa_setup(
        self,
        user_id: str,
        token: str
    ) -> TwoFAVerifyResponse:
        """2FA 로그인 2단계 검증"""
        try:
            # 사용자 2FA 정보 조회
            user_2fa_info = await self.repository.get_user_2fa_info(user_id)
            if not user_2fa_info:
                raise TwoFAUserNotFoundException()

            # 이미 활성화된 경우
            if user_2fa_info.get('is_2fa_enabled'):
                return TwoFAVerifyResponse(
                    success=True,
                    message="2FA가 이미 활성화되었습니다."
                )

            # OTP 검증
            secret = user_2fa_info.get('otp_secret')
            if not secret:
                raise TwoFAInvalidTokenException("2FA 설정이 완료되지 않았습니다.")

            totp = pyotp.TOTP(secret)
            if not totp.verify(token, valid_window=self.config.get_twofa_window_size()):
                raise TwoFAInvalidTokenException()

            # 2FA 활성화
            await self.repository.update_user_2fa_status(
                user_id=user_id,
                is_2fa_enabled=True
            )

            LOGGER.info(f"2FA enabled for user: {user_id}")

            return TwoFAVerifyResponse(
                success=True,
                message="2FA가 성공적으로 활성화되었습니다."
            )

        except Exception as e:
            LOGGER.error(f"verify_2fa_setup error: {e}")
            raise JSendError(
                code=ErrorCode.Common.INTERNAL_SERVER_ERROR[0],
                message=str(e),
            )

    async def authenticate_2fa(
        self,
        request: Request,
        user_id: str,
        token: str
    ) -> bool:
        """2FA 인증 (로그인 시)"""
        try:
            # 1. 먼저 해당 유저 2FA 설정 여부 확인 -> 처음 등록하는 경우에는 is_2fa_enabled가 False이므로 함 처리해야 함
            is_2fa_enabled = await self.verify_2fa_setup(
                user_id=user_id,
                token=token
            )
            if not is_2fa_enabled.success:
                raise TwoFANotEnabledException()

            user_2fa_info = await self.repository.get_user_2fa_info(user_id)
            if not user_2fa_info:
                raise TwoFAUserNotFoundException()

            # OTP 검증
            secret = user_2fa_info.get('otp_secret')
            if not secret:
                raise TwoFAInvalidTokenException("2FA 설정이 완료되지 않았습니다.")

            totp = pyotp.TOTP(secret)
            if not totp.verify(token, valid_window=self.config.get_twofa_window_size()):
                raise TwoFAInvalidTokenException()

            # 마지막 2FA 사용 시간 업데이트
            await self.repository.update_last_2fa_used(
                user_id=user_id,
                ip_address=request.client.host if request.client else "unknown",
                user_agent=request.headers.get("User-Agent", "unknown")
            )
            LOGGER.info(f"2FA authentication successful for user: {user_id}")
            return True
        except Exception as e:
            LOGGER.error(f"authenticate_2fa error: {e}")
            return False

    async def disable_2fa(self, user_id: str, token: str) -> TwoFADisableResponse:
        """2FA 비활성화"""
        try:
            # 사용자 2FA 정보 조회
            user_2fa_info = await self.repository.get_user_2fa_info(user_id)
            if not user_2fa_info:
                raise TwoFAUserNotFoundException()

            # OTP 검증
            secret = user_2fa_info.get('otp_secret')
            if not secret:
                raise TwoFAInvalidTokenException("2FA 설정이 완료되지 않았습니다.")

            totp = pyotp.TOTP(secret)
            if not totp.verify(token, valid_window=self.config.get_twofa_window_size()):
                raise TwoFAInvalidTokenException()

            # 2FA 비활성화
            await self.repository.disable_2fa(user_2fa_info['user_idx'])

            LOGGER.info(f"2FA disabled for user: {user_id}")

            return TwoFADisableResponse(
                success=True,
                message="2FA가 성공적으로 비활성화되었습니다."
            )

        except Exception as e:
            LOGGER.error(f"disable_2fa error: {e}")
            raise JSendError(
                code=ErrorCode.Common.INTERNAL_SERVER_ERROR[0],
                message=str(e),
            )

    async def get_backup_codes(self, user_id: str) -> TwoFABackupCodesResponse:
        """백업 코드 조회"""
        try:
            user_2fa_info = await self.repository.get_user_2fa_info(user_id)
            if not user_2fa_info:
                raise TwoFAUserNotFoundException()

            backup_codes = user_2fa_info.get('backup_codes', [])

            return TwoFABackupCodesResponse(
                backup_codes=backup_codes,
                message="백업 코드를 조회했습니다."
            )

        except Exception as e:
            LOGGER.error(f"get_backup_codes error: {e}")
            raise JSendError(
                code=ErrorCode.Common.INTERNAL_SERVER_ERROR[0],
                message=str(e),
            )


    async def get_2fa_status(self, user_id: str) -> TwoFAStatusResponse:
        """2FA 상태 조회"""
        try:
            user_info = await self.repository.get_user_by_id(user_id)
            if not user_info:
                raise TwoFAUserNotFoundException()

            is_enabled = user_info.get(user_info['is_2fa_enabled'], False)
            last_used = user_info.get(user_info['last_2fa_used'])

            backup_codes_count = 0
            if is_enabled:
                try:
                    user_2fa_info = await self.repository.get_user_2fa_info(user_id)
                    if user_2fa_info:
                        backup_codes_count = len(user_2fa_info.get('backup_codes', []))
                except:
                    pass

            return TwoFAStatusResponse(
                is_enabled=is_enabled,
                last_used_at=last_used,
                backup_codes_count=backup_codes_count
            )

        except Exception as e:
            LOGGER.error(f"get_2fa_status error: {e}")
            raise JSendError(
                code=ErrorCode.Common.INTERNAL_SERVER_ERROR[0],
                message=str(e),
            )
