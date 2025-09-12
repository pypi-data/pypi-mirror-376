"""
2FA 데코레이터
=============

기존 로그인 함수에 2FA 기능을 추가하는 간단한 데코레이터
"""

import functools
from typing import Callable

from fastapi import HTTPException

from src.common.utils.logger import set_logger

from .config import TwoFAConfig
from .repository import AdminTwoFARepository
from .service import TwoFAService

LOGGER = set_logger("twofa.decorator")


def login_2fa_decorator(func: Callable) -> Callable:
    """
    로그인 함수에 2FA 기능을 추가하는 데코레이터

    반드시 들어가야 할 body 파라미터
    - user_id : str
    - token  : str

    반환값은 반드시 JsendResponse 형식으로 반환해야 합니다.
    status: "success"
    data:
        "twofa_status": True,
        "qr_code_url": "",
        "message": "2FA 로그인 인증이 성공했습니다.",
    }

    Usage:
        @twofa_decorator
        async def signin_partner_admin(user_id: str, user_pw: str, request_ip: str = None):
            # 기존 로그인 로직
            return SigninOutput(...)
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            # 2FA 서비스 생성
            config = TwoFAConfig()
            twofa_service = TwoFAService(AdminTwoFARepository(config))
            LOGGER.info("2FA Decorator: 기존 로그인 함수 실행")

            # 요청에서 user_id와 token 추출
            if 'request' in kwargs and kwargs['request']:
                body = await kwargs['request'].json()
                token = body.get('token')
                user_id = body.get('user_id')
            else:
                token = None
                user_id = None

            if not user_id:
                raise HTTPException(status_code=400, detail="user_id가 필요합니다.")

            # 기존 로그인 함수 실행
            login_result = await func(*args, **kwargs)
            if hasattr(login_result, 'status') and login_result.status != 'success':
                return login_result

            # 2FA 처리
            try:
                user_2fa_info = await twofa_service.repository.get_user_2fa_info(user_id)
                #1 등록된 유저가 없으면 2fa 등록
                if not user_2fa_info:
                    setup_result = await twofa_service.setup_2fa(user_id)
                    return {
                        "status": "success",
                        "data": {
                            "qr_code_url": setup_result.qr_code_url,
                            "message": "2FA 설정이 필요합니다. QR 코드를 스캔하고 6자리 코드를 입력하세요."
                        }
                    }

                is_2fa_enabled = user_2fa_info.get('is_2fa_enabled', False)

                # 2FA 토큰이 제공된 경우 검증
                if token:
                    LOGGER.info(f"2FA Decorator: 2FA 토큰 검증 시도 - user_id: {user_id}")
                    verify_result = await twofa_service.authenticate_2fa(
                        user_id=user_id,
                        token=token,
                        request=kwargs['request']
                    )

                    if verify_result:
                        LOGGER.info(f"2FA Decorator: 2FA 검증 성공 - user_id: {user_id}")
                        result_dict = login_result.dict() if hasattr(login_result, 'dict') else login_result
                        result_dict['data'].update({
                            "qr_code_url": "",
                            "message": "2FA 로그인 인증이 성공했습니다.",
                        })
                        return result_dict
                    else:
                        LOGGER.warning(f"2FA Decorator: 2FA 토큰 일치하지 않음 - user_id: {user_id}")
                        raise HTTPException(status_code=401, detail="2FA 토큰이 일치하지 않습니다.")

                # 2FA 토큰이 제공되지 않은 경우
                if is_2fa_enabled:
                    # 2FA가 활성화된 경우 - 토큰 요청
                    LOGGER.info(f"2FA Decorator: 2FA가 활성화된 사용자 - user_id: {user_id}")
                    return {
                        "status": "success",
                        "data": {
                            "qr_code_url": '',
                            "message": "1단계 로그인이 완료되었습니다. 2단계 2FA 로그인을 진행해주세요."
                        }
                    }
                else:
                    # 2FA가 비활성화된 경우 - QR 코드 생성
                    LOGGER.info(f"2FA Decorator: 2FA가 비활성화된 사용자 - user_id: {user_id}")
                    setup_result = await twofa_service.setup_2fa(user_id)
                    return {
                        "status": "success",
                        "data": {
                            "qr_code_url": setup_result.qr_code_url,
                            "message": "2FA 설정이 필요합니다. QR 코드를 스캔하고 6자리 코드를 입력하세요."
                        }
                    }
            except Exception as e:
                LOGGER.warning(f"2FA Decorator: 2FA 처리 중 오류 - user_id: {user_id}, error: {e}")
                raise e
        except Exception as e:
            LOGGER.error(f"2FA Decorator error: {e}")
            raise e

    return wrapper