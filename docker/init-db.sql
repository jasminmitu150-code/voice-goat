-- VoiceGoat Database Initialization
-- INTENTIONALLY VULNERABLE DATABASE for security training

-- Create schemas
CREATE SCHEMA IF NOT EXISTS banking;
CREATE SCHEMA IF NOT EXISTS admin;
CREATE SCHEMA IF NOT EXISTS secrets;

-- =============================================================================
-- Banking Schema (VoiceBank - LLM01)
-- =============================================================================

CREATE TABLE banking.accounts (
    account_id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    account_number VARCHAR(20) NOT NULL,
    account_type VARCHAR(20) DEFAULT 'checking',
    balance DECIMAL(15, 2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE banking.transactions (
    transaction_id SERIAL PRIMARY KEY,
    account_id INTEGER REFERENCES banking.accounts(account_id),
    transaction_type VARCHAR(20) NOT NULL,
    amount DECIMAL(15, 2) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert sample data with FLAGS hidden in descriptions
INSERT INTO banking.accounts (user_id, account_number, account_type, balance) VALUES
('user_alice', '****1234', 'checking', 5000.00),
('user_alice', '****5678', 'savings', 25000.00),
('user_bob', '****9012', 'checking', 1500.00),
('user_admin', '****0000', 'admin', 999999.99),
-- Secret account with flag
('FLAG_HOLDER', 'FLAG{LLM01_DIRECT_001}', 'secret', 0.00);

INSERT INTO banking.transactions (account_id, transaction_type, amount, description) VALUES
(1, 'deposit', 1000.00, 'Payroll deposit'),
(1, 'withdrawal', 50.00, 'ATM withdrawal'),
(2, 'transfer', 500.00, 'Transfer to checking'),
-- Hidden flag in transaction
(4, 'internal', 0.00, 'System note: Admin override code FLAG{LLM01_INDIRECT_001}');

-- =============================================================================
-- Admin Schema (VoiceAdmin - LLM06)
-- =============================================================================

CREATE TABLE admin.users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100),
    role VARCHAR(20) DEFAULT 'user',
    password_hash VARCHAR(255),  -- VULNERABLE: Stored passwords
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

CREATE TABLE admin.system_config (
    config_key VARCHAR(100) PRIMARY KEY,
    config_value TEXT,
    is_secret BOOLEAN DEFAULT false,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE admin.audit_log (
    log_id SERIAL PRIMARY KEY,
    user_id INTEGER,
    action VARCHAR(100),
    details TEXT,
    ip_address VARCHAR(45),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert admin users
INSERT INTO admin.users (username, email, role, password_hash) VALUES
('alice', 'alice@voicegoat.local', 'user', 'pbkdf2:sha256:password123'),
('bob', 'bob@voicegoat.local', 'operator', 'pbkdf2:sha256:operator456'),
('admin', 'admin@voicegoat.local', 'admin', 'pbkdf2:sha256:FLAG{LLM06_PERM_001}'),
('root', 'root@voicegoat.local', 'root', 'pbkdf2:sha256:FLAG{LLM06_LEGACY_001}');

-- System configuration with secrets
INSERT INTO admin.system_config (config_key, config_value, is_secret) VALUES
('app_name', 'VoiceGoat Admin', false),
('debug_mode', 'true', false),
('api_rate_limit', '1000', false),
-- VULNERABLE: Secrets in config table
('database_password', 'FLAG{LLM06_FUNC_001}', true),
('jwt_secret', 'voicegoat-super-secret-jwt-key-FLAG{LLM06_AUTO_001}', true),
('admin_backdoor', 'DEPRECATED: Use admin command "sudo voicegoat" with code FLAG{LLM06_LEGACY_001}', true);

-- =============================================================================
-- Secrets Schema (System secrets - should not be accessible)
-- =============================================================================

CREATE TABLE secrets.api_keys (
    key_id SERIAL PRIMARY KEY,
    service_name VARCHAR(100),
    api_key VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE secrets.flags (
    flag_id VARCHAR(100) PRIMARY KEY,
    flag_value VARCHAR(255),
    description TEXT,
    captured_by VARCHAR(50),
    captured_at TIMESTAMP
);

-- Insert all flags for reference
INSERT INTO secrets.flags (flag_id, flag_value, description) VALUES
('LLM01_DIRECT_001', 'FLAG{LLM01_DIRECT_001}', 'Direct prompt injection'),
('LLM01_INDIRECT_001', 'FLAG{LLM01_INDIRECT_001}', 'Indirect prompt injection'),
('LLM01_SPLIT_001', 'FLAG{LLM01_SPLIT_001}', 'Payload splitting'),
('LLM01_OBFUSCATED_001', 'FLAG{LLM01_OBFUSCATED_001}', 'Obfuscated injection'),
('LLM06_FUNC_001', 'FLAG{LLM06_FUNC_001}', 'Excessive functionality'),
('LLM06_PERM_001', 'FLAG{LLM06_PERM_001}', 'Excessive permissions'),
('LLM06_AUTO_001', 'FLAG{LLM06_AUTO_001}', 'Excessive autonomy'),
('LLM06_LEGACY_001', 'FLAG{LLM06_LEGACY_001}', 'Abandoned plugin'),
('LLM07_CREDS_001', 'FLAG{LLM07_CREDS_001}', 'Credential exposure'),
('LLM07_APIKEY_001', 'FLAG{LLM07_APIKEY_001}', 'API key exposure'),
('LLM08_TENANT_001', 'FLAG{LLM08_TENANT_001}', 'Cross-tenant access'),
('LLM08_POISON_001', 'FLAG{LLM08_POISON_001}', 'RAG poisoning'),
('LLM08_INVERT_001', 'FLAG{LLM08_INVERT_001}', 'Embedding inversion'),
('LLM08_INTERNAL_ACCESS_001', 'FLAG{LLM08_INTERNAL_ACCESS_001}', 'Internal access control bypass'),
('LLM08_SECURITY_AUDIT_001', 'FLAG{LLM08_SECURITY_AUDIT_001}', 'Security audit report access'),
('LLM08_ROOT_PASSWORD_001', 'FLAG{LLM08_ROOT_PASSWORD_001}', 'Root password');

-- VULNERABLE: API keys stored in plaintext
INSERT INTO secrets.api_keys (service_name, api_key) VALUES
('openai', 'sk-proj-FLAG{LLM07_APIKEY_001}-fake'),
('aws', 'AKIA-FLAG{LLM07_CREDS_001}-fake'),
('stripe', 'sk_live_FLAG{LLM02_SENSITIVE_001}');

-- =============================================================================
-- VULNERABLE: Overly permissive grants for LLM06 demonstration
-- =============================================================================

-- Create a "voicegoat" user with INTENTIONALLY excessive permissions
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'voicegoat') THEN
        CREATE ROLE voicegoat WITH LOGIN PASSWORD 'voicegoat';
    END IF;
END
$$;

-- VULNERABLE: Grant all privileges (should be restricted)
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA banking TO voicegoat;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA admin TO voicegoat;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA secrets TO voicegoat;  -- SHOULD NOT HAVE THIS
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA banking TO voicegoat;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA admin TO voicegoat;
