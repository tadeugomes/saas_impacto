Orientações para Desenvolvedores — SaaS Multi-Tenant

Stack: FastAPI (Python, async) + React/Vue + PostgreSQL + BigQuery + Quarto + Redis/S3 (ou GCS)

1) Arquitetura (revista para múltiplas fontes, com BigQuery no centro analítico)

Frontend (React/Vue): dashboards responsivos; filtros dinâmicos; export local (PNG/PDF) e acionamento de relatórios.

Backend (FastAPI):

APIs REST/GraphQL (REST prioritário); async.

Camada de serviços que orquestra leitura em múltiplas fontes:

BigQuery (DW analítico principal): consultas em marts materializadas/particionadas.

PostgreSQL (operacional do app): autenticação, multi-tenancy, preferências, auditoria, filas de relatórios.

Outras fontes (quando houver): arquivos brutos (S3/GCS), APIs públicas e bases setoriais.

Integrações BigQuery: service account por ambiente; location coerente (US ou southamerica-east1) e, quando necessário, espelhamento para evitar cross-region.

Armazenamento de arquivos: S3/GCS para relatórios e exports (URLs assinadas).

Cache e fila: Redis para cache de consultas e job queue (Celery/RQ).

Observabilidade: OpenTelemetry + logs estruturados (tenant-aware) + métricas (latência, bytes processados, taxa de acerto de cache).

Padrão de acesso a dados (resumo)

Frontend → FastAPI (com token).

FastAPI valida org_id/user_id/roles → monta contexto.

Consulta preferencialmente BigQuery.marts (nunca varrer fato bruto em tempo real).

Resultado paginado + cache (Redis).

Exposição segura ao frontend.

Nota: PostgreSQL não é repositório analítico. Ele guarda metadados, configurações e controle de acesso; as consultas pesadas vivem no BigQuery.

2) Composição de Dashboards (sem “um dashboard por cliente”)

Únicos e parametrizáveis: o frontend envia filtros e escolhas (colunas, agrupamentos, ordenações).

Persistência de “visões” do usuário no PostgreSQL (nome, JSON de configuração).

Backend aplica isolamento e só retorna dados autorizados do tenant.

3) Segurança & Multi-Tenancy

Autenticação: OAuth2/OIDC (authlib/fastapi-users), JWT curto + refresh, chaves rotacionadas (JWKS).

Autorização: roles/claims (ex.: {org_id, user_id, scopes}) com verificação no service layer.

RLS / Isolamento de dados:

PostgreSQL: RLS habilitado, política USING (org_id = current_setting('app.org_id')::uuid).

BigQuery: filtros obrigatórios por tenant incorporados às views/marts (ex.: colunas tenant_key ou segregação física por dataset/projeto, conforme contrato).

Middleware de contexto: SET app.org_id (Postgres) e binding de parâmetros (BigQuery) em todas as consultas.

Rate limit & quotas: por org/usuário para endpoints de dados e geração de relatórios.

Testes anti-vazamento: suíte automatizada com tenants A/B executando as mesmas queries.

4) Exportação e Relatórios (Quarto no backend)

Export leve (frontend): PNG/SVG/PDF via Plotly/Chart.js + html2canvas/jspdf (uso pontual).

Relatórios ricos (backend/Quarto):

Frontend envia filtros + contexto → FastAPI enfileira job (Redis/Celery).

Worker executa script Python, consulta BigQuery.marts, renderiza .qmd (Quarto) em PDF/Word/HTML.

Upload em S3/GCS; retorno de URL assinada ao cliente.

Reprodutibilidade: versionar template .qmd, registrar hash de parâmetros e SQL utilizados.

5) Fluxo resumido

Usuário filtra no React/Vue.

FastAPI valida e consulta BigQuery.marts (com isolamento).

Renderização de gráficos/tabelas no navegador.

Para relatório completo, job Quarto → arquivo final para download.

6) Boas práticas adicionais

Auditoria completa: quem acessou o quê, quando e com quais filtros (guardar payload resumido).

Validação no backend: nunca confiar em filtros do cliente; impor filtros obrigatórios de tenant e limites de dimensão.

Componentização: gráficos e tabelas como componentes reutilizáveis; design system (MUI/Chakra/Tailwind).

7) Camada de Dados (BigQuery-first, multi-fontes)

Sem detalhar indicadores core agora. Abaixo, apenas a espinha de dados para suportá-los posteriormente.

Camadas no BigQuery:

raw_ext/landing: ingestão bruta (ANTAQ, Comex, CAGED/RAIS, PIB, Siconfi, IPCA, etc.).

staging: limpeza/normalização, chaves IBGE/CNAE/NCM, tipos e datas.

core: fatos/dimensões consolidados (granularidades definidas por tema).

marts: views/tabelas materializadas voltadas às consultas do app.

Particionamento & clusterização: por data/ano e chaves de junção; sem cross-region; atenção a custos (bytes processados).

Catálogo de fontes: tabela de metadados no Postgres com owner, frequência, SLA, última atualização, checksum.

Pipelines: Cloud Scheduler/Composer ou DBT + GitOps; alertas de quebra de esquema e atrasos.

8) API Design (FastAPI)

Padrões REST limpos com paginação cursor-based; fields e include[] para sparse fieldsets.

Contracts (OpenAPI) com exemplos por tenant e schemas de filtros.

Headers de contexto: correlação (trace-id), versão de indicador, consistency watermark (ex.: “dados até 2025-10”).

9) Observabilidade, Custos e Confiabilidade

Métricas principais: latência p95 por endpoint, acerto de cache, bytes processados por consulta (BQ), tempo médio de relatório, taxa de erro.

Alertas: falhas de pipeline, fila de relatórios congestionada, estouro de orçamento BQ.

Backups & retenção: Postgres (dump), objetos (versões), disaster recovery.

10) Segurança, LGPD & Acessibilidade

PII: evitar tráfego/armazenamento de dados pessoais; expor apenas agregados.

Criptografia: em repouso (KMS) e em trânsito (TLS).

Acessibilidade: WCAG AA; i18n (pt-BR/en).

Pentest & SAST/DAST: antes de ir a clientes públicos.

