# API GUIDE

## Base URL

- Local: `http://localhost:8000`
- Endpoint de API: `/api/v1`

## Autenticação

Use JWT no header:

```http
Authorization: Bearer <access_token>
```

### Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"admin123"}'
```

## Indicadores

### Query genérica

```bash
curl -X POST http://localhost:8000/api/v1/indicators/query \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"codigo_indicador":"IND-5.01","ano":2024}'
```

### Listar metadados

```bash
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/v1/indicators/metadata/IND-5.01
```

## Relatórios

### Indicador (DOCX/PDF/XLSX)

```bash
curl -X POST "http://localhost:8000/api/v1/reports/indicator/IND-5.01?format=pdf&ano=2024" \
  -H "Authorization: Bearer <token>" \
  --output indicador_2024.pdf
```

### Módulo (DOCX/PDF/XLSX)

```bash
curl -X POST "http://localhost:8000/api/v1/reports/module/5?format=xlsx&ano=2024" \
  -H "Authorization: Bearer <token>" \
  --output modulo5_2024.xlsx
```

## Onboarding

```bash
curl -X POST http://localhost:8000/api/v1/onboarding/register \
  -H "Content-Type: application/json" \
  -d '{
    "empresa":"Portos Exemplo S.A.",
    "cnpj":"12.345.678/0001-90",
    "plano":"pro",
    "nome_admin":"Administrador",
    "email_admin":"admin@porto.com",
    "senha_admin":"SenhaForte123!"
  }'
```

## Admin

### Listar tenants

```bash
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/admin/tenants
```

### Dashboard de uso

```bash
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/v1/admin/dashboard/usage
```

