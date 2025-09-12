import json
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from src.common.utils.logger import set_logger
from src.packages.db.connect import connection

from .config import TwoFAConfig
from .exceptions import TwoFANotEnabledException, TwoFAUserNotFoundException

LOGGER = set_logger("twofa.repository")


class TwoFARepository(ABC):
    """2FA 리포지토리 추상 클래스"""

    def __init__(self, config: TwoFAConfig):
        self.config = config

    @abstractmethod
    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """사용자 ID로 사용자 정보 조회"""
        pass

    @abstractmethod
    async def upsert_user_2fa_status(self, user_id: str, **kwargs) -> bool:
        """사용자의 2FA 상태 업데이트"""
        pass
    @abstractmethod
    async def get_user_2fa_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """사용자의 2FA 정보 조회"""
        pass

    @abstractmethod
    async def update_user_2fa_status(self, user_id: str, is_2fa_enabled: bool) -> bool:
        """사용자의 2FA 상태 업데이트"""
        pass


    @abstractmethod
    async def disable_2fa(self, user_id: str) -> bool:
        """2FA 비활성화"""
        pass

    @abstractmethod
    async def update_last_2fa_used(self, user_id: str, ip_address: str, user_agent: str) -> bool:
        """마지막 2FA 사용 시간 업데이트"""
        pass


class AdminTwoFARepository(TwoFARepository):
    """Admin용 2FA 리포지토리 구현체"""

    def __init__(self, config: TwoFAConfig):
        super().__init__(config)

    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """사용자 ID로 사용자 정보 조회"""
        try:
            async with connection() as session:
                query = f"""
                    SELECT
                        user_id,
                        is_2fa_enabled,
                        otp_secret,
                        backup_codes
                    FROM user_twofa
                    WHERE user_id = $1
                """
                result = await session.fetchrow(query, user_id)
            return dict(result) if result else None

        except Exception as e:
            LOGGER.error(f"get_user_by_id error: {e}")
            raise e

    async def upsert_user_2fa_status(
        self,
        user_id: str,
        otp_secret: str,
        backup_codes: str,
        is_2fa_enabled: bool
    ) -> bool:
        """사용자의 2FA 상태 업데이트"""
        try:
            async with connection() as session:
                # OTP 비밀키 암호화
                encrypted_otp_secret = self.config.encrypt_data(otp_secret) if otp_secret else None
                # 백업 코드는 배열로 직접 전달 (PostgreSQL 배열 타입)
                encrypted_backup_codes = self.config.encrypt_data(json.dumps(backup_codes))
                query = """
                    INSERT INTO user_twofa
                    (user_id, otp_secret, backup_codes, is_2fa_enabled)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (user_id) DO UPDATE SET
                        otp_secret = $2,
                        backup_codes = $3,
                        is_2fa_enabled = $4
                    WHERE user_twofa.user_id = $1
                    RETURNING user_id
                """
                return await session.execute(query, user_id, encrypted_otp_secret, encrypted_backup_codes, is_2fa_enabled)

        except Exception as e:
            LOGGER.error(f"update_user_2fa_status error: {e}")
            raise e

    async def get_user_2fa_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """사용자의 2FA 정보 조회"""
        user_info = await self.get_user_by_id(user_id)
        # 2FA가 활성화되지 않은 경우
        if not user_info:
            return None

        result = {
            'user_id': user_info['user_id'],
            'is_2fa_enabled': user_info['is_2fa_enabled'],
            'otp_secret': user_info['otp_secret'],
            'backup_codes': user_info['backup_codes'],
        }

        # OTP 비밀키 복호화
        if user_info.get('otp_secret'):
            try:
                result['otp_secret'] = self.config.decrypt_data(user_info['otp_secret'])
            except Exception as e:
                LOGGER.error(f"Failed to decrypt otp_secret: {e}")
                result['otp_secret'] = None

        # 백업 코드 복호화
        if user_info.get('backup_codes'):
            try:
                backup_codes_json = self.config.decrypt_data(user_info['backup_codes'])
                result['backup_codes'] = json.loads(backup_codes_json)
            except Exception as e:
                LOGGER.error(f"Failed to decrypt backup_codes: {e}")
                result['backup_codes'] = []

        return result


    async def update_user_2fa_status(self, user_id: str, is_2fa_enabled: bool) -> bool:
        """사용자의 2FA 상태 업데이트"""
        try:
            async with connection() as session:
                query = f"""
                    UPDATE user_twofa
                    set is_2fa_enabled = $2
                    WHERE user_id = $1
                """
                return await session.execute(query, user_id, is_2fa_enabled)
        except Exception as e:
            LOGGER.error(f"update_user_2fa_status error: {e}")
            raise e


    async def disable_2fa(self, user_idx: int) -> bool:
        """2FA 비활성화"""
        try:
            async with connection() as session:
                query = f"""
                    UPDATE admin_master
                    SET
                        is_2fa_enabled = false,
                        otp_secret = NULL,
                        backup_codes = NULL,
                        last_2fa_used_at = NULL
                    WHERE idx = $1
                        and status = 'Normal'
                """

                result = await session.execute(query, user_idx)
                return result == "UPDATE 1"

        except Exception as e:
            LOGGER.error(f"disable_2fa error: {e}")
            raise e

    async def update_last_2fa_used(
        self,
        user_id: str,
        ip_address: str,
        user_agent: str,
    ) -> bool:
        """마지막 2FA 사용 시간 업데이트"""
        try:
            async with connection() as session:
                query = f"""
                    INSERT INTO user_twofa_logs
                    (user_id, ip_address, user_agent)
                    VALUES ($1, $2, $3)
                """

                result = await session.execute(query, user_id, ip_address, user_agent)
                return result
        except Exception as e:
            LOGGER.error(f"update_last_2fa_used error: {e}")
            raise e
