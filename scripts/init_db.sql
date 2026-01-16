-- =====================================================
-- Schema Inicial - SaaS Impacto Portuário
-- Multi-tenancy com Row Level Security (RLS)
-- =====================================================

-- Extensões necessárias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =====================================================
-- Tabela: Tenants (Organizações)
-- =====================================================
CREATE TABLE IF NOT EXISTS tenants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nome VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    cnpj VARCHAR(20) UNIQUE,
    ativo BOOLEAN DEFAULT true,
    plano VARCHAR(50) DEFAULT 'basic',  -- basic, pro, enterprise

    -- Configurações de isolamento de dados
    bq_project_filter VARCHAR(100),
    instalacoes_permitidas TEXT,  -- JSON array: ["SP01", "RJ02"]

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índices
CREATE INDEX idx_tenants_slug ON tenants(slug);
CREATE INDEX idx_tenants_ativo ON tenants(ativo);

-- =====================================================
-- Tabela: Users
-- =====================================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    nome VARCHAR(255) NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,

    ativo BOOLEAN DEFAULT true,
    roles TEXT[] DEFAULT ARRAY['viewer']::TEXT[],  -- admin, analyst, viewer

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE,

    UNIQUE(tenant_id, email)
);

-- Índices
CREATE INDEX idx_users_tenant_id ON users(tenant_id);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_ativo ON users(ativo);

-- =====================================================
-- Tabela: Dashboard Views (visões salvas pelos usuários)
-- =====================================================
CREATE TABLE IF NOT EXISTS dashboard_views (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    nome VARCHAR(255) NOT NULL,
    configuracao JSONB NOT NULL,  -- Filtros, layout, etc.
    is_default BOOLEAN DEFAULT false,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índices
CREATE INDEX idx_dashboard_views_tenant_id ON dashboard_views(tenant_id);
CREATE INDEX idx_dashboard_views_user_id ON dashboard_views(user_id);

-- =====================================================
-- Tabela: Audit Log (auditoria completa)
-- =====================================================
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,

    action VARCHAR(100) NOT NULL,  -- login, view_indicator, export_report, etc.
    resource_type VARCHAR(100),    -- indicator, dashboard, report
    resource_id VARCHAR(100),

    request_payload JSONB,
    response_status INTEGER,

    ip_address INET,
    user_agent TEXT,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índices
CREATE INDEX idx_audit_logs_tenant_id ON audit_logs(tenant_id);
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);
-- Índice para pesquisa recente
CREATE INDEX idx_audit_logs_tenant_created ON audit_logs(tenant_id, created_at DESC);

-- =====================================================
-- ROW LEVEL SECURITY (RLS) - Multi-tenancy
-- =====================================================

-- Habilitar RLS nas tabelas principais
ALTER TABLE tenants ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE dashboard_views ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

-- Políticas para tenants (apenas admin pode ver todos, simplificado)
CREATE POLICY tenants_all ON tenants
    FOR ALL
    USING (true);

-- Política para users: só ver do próprio tenant
CREATE POLICY users_tenant_isolation ON users
    FOR ALL
    USING (
        tenant_id = current_setting('app.current_tenant_id', true)::UUID
    );

-- Política para dashboard_views: só ver do próprio tenant
CREATE POLICY dashboard_views_tenant_isolation ON dashboard_views
    FOR ALL
    USING (
        tenant_id = current_setting('app.current_tenant_id', true)::UUID
    );

-- Política para audit_logs: só ver do próprio tenant
CREATE POLICY audit_logs_tenant_isolation ON audit_logs
    FOR ALL
    USING (
        tenant_id = current_setting('app.current_tenant_id', true)::UUID
    );

-- =====================================================
-- Funções de Apoio
-- =====================================================

-- Função para setar contexto do tenant (chamada pelo middleware)
CREATE OR REPLACE FUNCTION set_tenant_context(tenant_id UUID)
RETURNS void AS $$
BEGIN
    PERFORM set_config('app.current_tenant_id', tenant_id::TEXT, false);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger para garantir timestamp de updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Aplicar trigger em todas as tabelas com updated_at
CREATE TRIGGER update_tenants_updated_at BEFORE UPDATE ON tenants
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_dashboard_views_updated_at BEFORE UPDATE ON dashboard_views
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- Dados Iniciais (Seed)
-- =====================================================

-- Tenant de exemplo
INSERT INTO tenants (nome, slug, cnpj, plano, instalacoes_permitidas)
VALUES (
    'Organização Exemplo',
    'organizacao-exemplo',
    NULL,
    'pro',
    '["SP01", "RJ02", "SC01"]'::JSONB->>0  -- Exemplo: JSON array de instalações
) ON CONFLICT (slug) DO NOTHING;

-- User admin de exemplo (senha: admin123)
-- NOTA: Em produção, gerar hash via Python: passlib.hash.bcrypt.hash("admin123")
INSERT INTO users (tenant_id, email, nome, hashed_password, roles)
SELECT
    id,
    'admin@exemplo.com',
    'Administrador',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyWuiVqW.vq6',  -- admin123
    ARRAY['admin', 'analyst', 'viewer']::TEXT[]
FROM tenants
WHERE slug = 'organizacao-exemplo'
ON CONFLICT (tenant_id, email) DO NOTHING;

-- =====================================================
-- Finalização
-- =====================================================

-- Comentários de tabela
COMMENT ON TABLE tenants IS 'Organizações/tenants do sistema SaaS';
COMMENT ON TABLE users IS 'Usuários do sistema com isolamento por tenant';
COMMENT ON TABLE dashboard_views IS 'Visões de dashboard salvas pelos usuários';
COMMENT ON TABLE audit_logs IS 'Auditoria completa de ações no sistema';

-- Função para verificar RLS
CREATE OR REPLACE FUNCTION check_rls()
RETURNS TABLE(table_name TEXT, enabled BOOLEAN) AS $$
BEGIN
    RETURN QUERY
    SELECT
        schemaname||'.'||tablename AS table_name,
        rowsecurity AS enabled
    FROM pg_tables
    WHERE schemaname = 'public'
        AND tablename IN ('users', 'dashboard_views', 'audit_logs')
    ORDER BY tablename;
END;
$$ LANGUAGE plpgsql;

-- Testar RLS: SELECT * FROM check_rls();
