"""
HotPartners 2FA Package Database Schema Manager
"""

import asyncio
import logging
from pathlib import Path
from typing import Any, Callable, Optional

LOGGER = logging.getLogger(__name__)

class TwoFASchemaManager:
    """2FA 데이터베이스 스키마 관리자"""

    def __init__(self, connection_func: Callable, admin_connection_func: Optional[Callable] = None):
        """
        스키마 관리자 초기화

        Args:
            connection_func: 일반 사용자 데이터베이스 연결 함수
            admin_connection_func: 관리자 데이터베이스 연결 함수 (선택사항)
        """
        self.connection_func = connection_func
        self.admin_connection_func = admin_connection_func

    async def create_tables(self, schema_file: Optional[str] = None) -> bool:
        """
        필요한 테이블들을 생성합니다

        Args:
            schema_file: 사용자 정의 스키마 파일 경로 (선택사항)

        Returns:
            bool: 성공 여부
        """
        try:
            # 스키마 파일 경로 결정
            if schema_file:
                schema_path = Path(schema_file)
            else:
                # 패키지 내부 스키마 파일 사용
                package_dir = Path(__file__).parent
                schema_path = package_dir / "sql" / "schema.sql"

            if not schema_path.exists():
                LOGGER.error(f"스키마 파일을 찾을 수 없습니다: {schema_path}")
                return False

            # 스키마 파일 읽기
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema_sql = f.read()

            # 일반 사용자 테이블 생성
            async with self.connection_func() as session:
                await session.execute(schema_sql)
                LOGGER.info("사용자 2FA 테이블이 생성되었습니다")

            # 관리자 테이블이 필요한 경우
            if self.admin_connection_func:
                async with self.admin_connection_func() as session:
                    await session.execute(schema_sql)
                    LOGGER.info("관리자 2FA 테이블이 생성되었습니다")

            return True

        except Exception as e:
            LOGGER.error(f"테이블 생성 중 오류가 발생했습니다: {e}")
            return False

    async def check_tables_exist(self) -> dict:
        """
        필요한 테이블들이 존재하는지 확인합니다

        Returns:
            dict: 테이블 존재 여부 정보
        """
        try:
            async with self.connection_func() as session:
                # PostgreSQL에서 테이블 존재 확인
                query = """
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name IN ('user_twofa', 'user_twofa_logs', 'admin_twofa', 'admin_twofa_logs')
                """
                result = await session.fetch(query)
                existing_tables = [row['table_name'] for row in result]

                required_tables = ['user_twofa', 'user_twofa_logs']
                admin_tables = ['admin_twofa', 'admin_twofa_logs']

                return {
                    'user_tables': {
                        'user_twofa': 'user_twofa' in existing_tables,
                        'user_twofa_logs': 'user_twofa_logs' in existing_tables,
                    },
                    'admin_tables': {
                        'admin_twofa': 'admin_twofa' in existing_tables,
                        'admin_twofa_logs': 'admin_twofa_logs' in existing_tables,
                    },
                    'all_required_exist': all(
                        table in existing_tables for table in required_tables
                    ),
                    'admin_required_exist': all(
                        table in existing_tables for table in admin_tables
                    ) if self.admin_connection_func else True,
                }

        except Exception as e:
            LOGGER.error(f"테이블 확인 중 오류가 발생했습니다: {e}")
            return {}

    async def drop_tables(self, include_admin: bool = False) -> bool:
        """
        테이블들을 삭제합니다 (주의: 데이터가 모두 삭제됩니다)

        Args:
            include_admin: 관리자 테이블도 삭제할지 여부

        Returns:
            bool: 성공 여부
        """
        try:
            drop_sql = """
                DROP TABLE IF EXISTS user_twofa_logs CASCADE;
                DROP TABLE IF EXISTS user_twofa CASCADE;
            """

            if include_admin:
                drop_sql += """
                    DROP TABLE IF EXISTS admin_twofa_logs CASCADE;
                    DROP TABLE IF EXISTS admin_twofa CASCADE;
                """

            async with self.connection_func() as session:
                await session.execute(drop_sql)
                LOGGER.info("사용자 2FA 테이블이 삭제되었습니다")

            if include_admin and self.admin_connection_func:
                async with self.admin_connection_func() as session:
                    await session.execute(drop_sql)
                    LOGGER.info("관리자 2FA 테이블이 삭제되었습니다")

            return True

        except Exception as e:
            LOGGER.error(f"테이블 삭제 중 오류가 발생했습니다: {e}")
            return False
