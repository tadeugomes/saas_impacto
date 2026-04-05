# Plano de Implementacao - Calculadora de Impacto (Modulo 5)

## 1. Objetivo
Transformar os resultados causais do Modulo 5 em saidas executivas para gestores:

1. Responder com clareza: "Se investirmos X, qual impacto esperado em Y (PIB, empregos, comercio)?"
2. Mostrar impacto em percentual e em valor absoluto.
3. Exibir faixa de incerteza (conservador, base, otimista).
4. Registrar premissas e versoes dos coeficientes para auditoria.

## 2. Problema de modelagem e solucao
### 2.1 Problema
Hoje os modelos causais estimam principalmente o elo:

- Movimentacao portuaria -> Outcomes (PIB, emprego, comercio)

Sem um elo explicito:

- Investimento -> Movimentacao

Nao e metodologicamente correto afirmar diretamente:

- "10% de investimento gera Y% de PIB"

### 2.2 Solucao (modelo em 2 estagios)
Implementar transmissao causal em dois estagios:

1. Estagio 1 (novo): `Delta ln(toneladas) = eta * Delta ln(investimento) + controles + FE municipio + FE ano`
2. Estagio 2 (ja existente): `Delta ln(outcome) = beta * Delta ln(toneladas)`

Composicao para calculadora:

- `Delta outcome(%) ~ beta * eta * Delta investimento(%)`

## 3. Escopo funcional
### 3.1 Resumo executivo no frontend (gestor)
Exibir no topo do Modulo 5:

1. Impacto esperado (%)
2. Impacto esperado absoluto (R$, empregos, US$)
3. Nivel de confianca (forte, moderada, fraca)
4. Faixa IC95% (conservador, base, otimista)
5. Texto explicativo automatico em linguagem de negocio

Exemplo de texto:

- "Com aumento de 10% no investimento, o modelo estima variacao de Y% no PIB (IC95%: A% a B%)."

### 3.2 Calculadora de impacto
Entradas:

1. Investimento planejado (R$)
2. Tipo de entrada de transmissao:
3. Modo estimado (usa eta calibrado)
4. Modo premissa (usuario informa impacto esperado em movimentacao)
5. Horizonte (1, 3, 5 anos)
6. Metodo causal base (did, iv, panel_iv, event_study, compare)
7. Outcome(s) alvo

Saidas:

1. Impacto em PIB (% e R$)
2. Impacto em empregos (% e absoluto)
3. Impacto em comercio (% e US$)
4. Faixa de incerteza por cenario
5. Premissas usadas + versao dos coeficientes

## 4. Contratos tecnicos (proposta)
### 4.1 Endpoint de simulacao
`POST /api/v1/impacto-economico/simulacoes`

Payload minimo:

```json
{
  "tenant_id": "uuid",
  "id_instalacao": "Santos",
  "treated_ids": ["3548500"],
  "control_ids": ["3509502", "3518800"],
  "method": "did",
  "outcomes": ["pib_log", "empregos_totais_log"],
  "treatment_year": 2023,
  "horizonte_anos": 3,
  "investimento_reais": 1000000000,
  "modo_transmissao": "estimado",
  "delta_toneladas_percentual_premissa": null
}
```

Response minimo:

```json
{
  "modo_transmissao": "estimado",
  "coeficientes": {
    "beta": 0.18,
    "beta_ci_lower": 0.05,
    "beta_ci_upper": 0.31,
    "eta": 0.40,
    "eta_ci_lower": 0.22,
    "eta_ci_upper": 0.58,
    "versao_beta": "2026-02-15.did.v1",
    "versao_eta": "2026-02-20.fe.v1"
  },
  "entrada": {
    "delta_investimento_percentual": 10.0
  },
  "impactos": [
    {
      "outcome": "pib_log",
      "impacto_percentual_base": 0.72,
      "impacto_percentual_conservador": 0.11,
      "impacto_percentual_otimista": 1.80,
      "impacto_absoluto_base": 125000000.0,
      "unidade_absoluta": "BRL"
    }
  ],
  "mensagem_executiva": "Com aumento de 10% no investimento, o impacto estimado no PIB e de 0.72% (IC95%: 0.11% a 1.80%).",
  "observacoes": [
    "Resultado depende da validade dos modelos beta e eta.",
    "Caso modo_transmissao=premissa, resultado nao representa estimativa causal completa do estagio 1."
  ]
}
```

## 5. Backlog tecnico (Jira-ready)

## EPIC M5-E1 - Dados e Modelo de Transmissao (eta)
| ID | Story | SP | Criterio de aceite |
|---|---|---:|---|
| M5-101 | Ingerir base de investimentos portuarios por municipio/ano | 8 | Tabela padronizada com `id_municipio`, `ano`, `investimento_real`, `fonte`, `qualidade_dado` |
| M5-102 | Deflacionar investimentos e gerar `Delta ln(investimento)` | 5 | Pipeline com validacoes de tipo e integridade temporal |
| M5-103 | Estimar modelo FE para `Delta ln(toneladas) ~ Delta ln(investimento)` | 8 | Saida com `eta`, `std_err`, `p_value`, `ci95`, `n_obs` |
| M5-104 | Diagnosticos de estabilidade e sensibilidade do estagio 1 | 5 | Relatorio com flag de confianca: strong/moderate/weak |
| M5-105 | Expor consulta de `eta` versionado por porto/periodo | 3 | Endpoint com versao, validade, metadados e fallback |

## EPIC M5-E2 - Backend de Simulacao de Impacto
| ID | Story | SP | Criterio de aceite |
|---|---|---:|---|
| M5-201 | Criar endpoint `POST /impacto-economico/simulacoes` | 8 | Recebe entradas e retorna payload de impacto completo |
| M5-202 | Implementar motor de composicao `beta * eta * Delta investimento` | 8 | Funciona para PIB, empregos, comercio e massa salarial |
| M5-203 | Implementar cenarios conservador/base/otimista com IC95% | 5 | Response com ponto central + limites inferior/superior |
| M5-204 | Implementar modo premissa quando eta nao estiver disponivel | 3 | API retorna `modo_transmissao=premissa` e aviso explicito |
| M5-205 | Persistir trilha de auditoria da simulacao | 5 | Log com parametros, coeficientes, versoes, usuario e timestamp |

## EPIC M5-E3 - Frontend Executivo e Calculadora
| ID | Story | SP | Criterio de aceite |
|---|---|---:|---|
| M5-301 | Criar card "Resumo para Gestor" no topo do Modulo 5 | 5 | Frase executiva com impacto %, absoluto e confianca |
| M5-302 | Criar UI da calculadora de impacto | 8 | Entradas validadas e UX clara para usuario nao tecnico |
| M5-303 | Exibir faixa de incerteza por cenario | 5 | Grafico/tabela com conservador, base e otimista |
| M5-304 | Adicionar avisos metodologicos em linguagem de negocio | 3 | Mostra diferenca entre modo estimado e modo premissa |
| M5-305 | Exportar simulacao para DOCX/JSON | 5 | Relatorio inclui formulas, coeficientes e limitacoes |

## EPIC M5-E4 - Governanca e Operacao
| ID | Story | SP | Criterio de aceite |
|---|---|---:|---|
| M5-401 | Criar model registry para beta/eta | 5 | Migration + leitura por API + controle de versao |
| M5-402 | Monitorar latencia, erros e uso da calculadora | 3 | Dashboard operacional com alertas basicos |
| M5-403 | Job de recalibracao periodica de eta | 3 | Execucao agendada com historico e idempotencia |
| M5-404 | Politica de fallback automatico por qualidade | 3 | Quando qualidade insuficiente, forcar modo premissa |

## EPIC M5-E5 - QA, UAT e Rollout
| ID | Story | SP | Criterio de aceite |
|---|---|---:|---|
| M5-501 | Testes unitarios backend (formulas, cenarios, fallback) | 5 | Cobertura dos fluxos criticos de simulacao |
| M5-502 | Testes E2E frontend (estimado e premissa) | 5 | Fluxo ponta-a-ponta validado |
| M5-503 | UAT com roteiro para gestores | 3 | Checklist de entendimento e usabilidade aprovado |
| M5-504 | Rollout com feature flag por tenant | 3 | Ativacao gradual e rollback controlado |

## 6. Dependencias
1. E2 depende de E1 para operar em modo estimado.
2. E3 pode iniciar antes com mock e modo premissa.
3. E5 inicia apos API de simulacao e tela principal estabilizadas.

## 7. Sequencia sugerida por sprint
### Sprint 1
1. M5-101
2. M5-102
3. M5-103
4. M5-201

### Sprint 2
1. M5-104
2. M5-105
3. M5-202
4. M5-204

### Sprint 3
1. M5-203
2. M5-205
3. M5-301
4. M5-302

### Sprint 4
1. M5-303
2. M5-304
3. M5-305
4. M5-401
5. M5-402

### Sprint 5
1. M5-403
2. M5-404
3. M5-501
4. M5-502
5. M5-503
6. M5-504

## 8. Definicao de pronto (DoD)
1. Simulacao responde impacto percentual e absoluto para ao menos PIB e empregos.
2. Faixa de incerteza visivel em todos os resultados exibidos para gestor.
3. Sistema funciona em modo estimado e modo premissa.
4. Todas as simulacoes registram premissas, versoes de coeficientes e timestamp.
5. Testes unitarios e E2E dos fluxos criticos passando no CI.

## 9. Riscos e mitigacoes
1. Risco: baixa qualidade de dados de investimento.
2. Mitigacao: score de qualidade + fallback automatico para modo premissa.
3. Risco: leitura incorreta de causalidade por usuarios finais.
4. Mitigacao: texto executivo padrao + badge de confianca + avisos metodologicos.
5. Risco: alta variabilidade dos coeficientes.
6. Mitigacao: cenarios por IC95% e recalibracao periodica.

## 10. Proximos passos imediatos
1. Validar com Produto e Econometria os contratos de entrada/saida da simulacao.
2. Quebrar os cards em tickets por squad (Dados, Backend, Frontend, QA).
3. Iniciar Sprint 1 com M5-101, M5-102, M5-103 e M5-201.

