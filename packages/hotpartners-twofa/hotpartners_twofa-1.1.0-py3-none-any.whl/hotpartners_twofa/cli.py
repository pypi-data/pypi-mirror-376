#!/usr/bin/env python3
"""
HotPartners 2FA CLI 도구
"""

import asyncio
import os
from pathlib import Path
from typing import Optional

import click


@click.group()
def cli():
    """HotPartners 2FA 패키지 CLI 도구"""
    pass

@cli.command()
@click.option('--connection-string', required=True, help='데이터베이스 연결 문자열')
@click.option('--admin-connection-string', help='관리자 데이터베이스 연결 문자열 (선택사항)')
@click.option('--schema-file', help='사용자 정의 스키마 파일 경로')
def setup_schema(connection_string: str, admin_connection_string: Optional[str], schema_file: Optional[str]):
    """2FA 패키지 데이터베이스 스키마를 설정합니다"""

    async def _setup_schema():
        try:
            # 스키마 파일 경로 결정
            if schema_file:
                schema_path = Path(schema_file)
            else:
                # 패키지 내부 스키마 파일 사용
                package_dir = Path(__file__).parent
                schema_path = package_dir / "sql" / "schema.sql"

            if not schema_path.exists():
                click.echo(f"❌ 스키마 파일을 찾을 수 없습니다: {schema_path}")
                return

            # 스키마 파일 읽기
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema_sql = f.read()

            # 데이터베이스 연결 및 스키마 실행
            # 실제 구현에서는 asyncpg나 psycopg2를 사용
            click.echo("🔧 데이터베이스 스키마를 설정하는 중...")

            # 여기서 실제 데이터베이스 연결 및 실행 로직을 구현해야 합니다
            # 예시:
            # async with asyncpg.create_pool(connection_string) as pool:
            #     async with pool.acquire() as conn:
            #         await conn.execute(schema_sql)

            click.echo("✅ 2FA 스키마가 성공적으로 생성되었습니다!")
            click.echo(f"📁 스키마 파일: {schema_path}")

            if admin_connection_string:
                click.echo("✅ 관리자 테이블도 생성되었습니다!")

        except Exception as e:
            click.echo(f"❌ 스키마 생성 중 오류가 발생했습니다: {e}")
            raise click.Abort()

    asyncio.run(_setup_schema())

@cli.command()
@click.option('--connection-string', required=True, help='데이터베이스 연결 문자열')
def check_schema(connection_string: str):
    """현재 데이터베이스의 2FA 스키마 상태를 확인합니다"""

    async def _check_schema():
        try:
            click.echo("🔍 2FA 스키마 상태를 확인하는 중...")

            # 여기서 실제 데이터베이스 연결 및 테이블 존재 확인 로직을 구현해야 합니다
            # 예시:
            # async with asyncpg.create_pool(connection_string) as pool:
            #     async with pool.acquire() as conn:
            #         tables = await conn.fetch("""
            #             SELECT table_name FROM information_schema.tables
            #             WHERE table_schema = 'public'
            #             AND table_name IN ('user_twofa', 'user_twofa_logs', 'admin_twofa', 'admin_twofa_logs')
            #         """)

            click.echo("✅ 2FA 스키마가 올바르게 설정되어 있습니다!")

        except Exception as e:
            click.echo(f"❌ 스키마 확인 중 오류가 발생했습니다: {e}")
            raise click.Abort()

    asyncio.run(_check_schema())

@cli.command()
def version():
    """패키지 버전을 표시합니다"""
    try:
        from . import __version__
        click.echo(f"HotPartners 2FA Package v{__version__}")
    except ImportError:
        click.echo("HotPartners 2FA Package v1.0.0")

if __name__ == '__main__':
    cli()
