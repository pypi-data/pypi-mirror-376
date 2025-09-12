-- HotPartners 2FA Package Database Schema
-- PostgreSQL용 스키마 파일

-- 사용자 2FA 테이블
CREATE TABLE IF NOT EXISTS user_twofa (
    idx SERIAL PRIMARY KEY,
    user_id VARCHAR(255) PRIMARY KEY,
    otp_secret TEXT,
    backup_codes TEXT,  -- JSON 문자열로 저장
    is_2fa_enabled BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2FA 사용 로그 테이블
CREATE TABLE IF NOT EXISTS user_twofa_logs (
    idx SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user_twofa(user_id) ON DELETE CASCADE
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_user_twofa_enabled ON user_twofa(is_2fa_enabled);
CREATE INDEX IF NOT EXISTS idx_user_twofa_logs_user_id ON user_twofa_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_user_twofa_logs_created_at ON user_twofa_logs(created_at);