# Plano de Implementação – Simulador de Impacto (Módulo 5)

## 1) Objetivo do Módulo
Transformar os resultados causais do Módulo 5 em uma ferramenta de decisão executiva capaz de responder, com linguagem de gestão, a perguntas do tipo:
- “Com impacto de **X%** na movimentação portuária, qual a variação esperada em PIB, empregos e receitas?”
- “Quais cenários são mais fortes ou frágeis?”
- “Qual o risco de reversão desse impacto?”

## 2) Entendimento do ponto crítico de modelagem
Hoje os modelos atuais estimam, de forma predominante:
- Impacto da movimentação portuária (`toneladas_antaq` / log) sobre desfechos socioeconômicos.

Sem um elo adicional de causalidade, não é metodologicamente correto afirmar, no estado atual, que:
- **“10% de investimento gera Y% de PIB”**.

### Regra mínima de negócio (atual, já implementada)
A simuladora de cenário no produto deverá, por padrão, operar com hipótese de **choque na atividade portuária** (não investimento), porque este é o canal já estimado.

## 3) O que já está implementado no código
- Backend:
  - Novos schemas em `backend/app/schemas/impacto_economico.py`:
    - `ImpactSimulationRequest`
    - `ImpactSimulationProjection`
    - `ImpactSimulationResponse`
  - Novo endpoint em `backend/app/api/v1/impacto_economico/router.py`:
    - `POST /api/v1/impacto-economico/analises/{analysis_id}/simulacao`
    - Regras de simulação:
      - converte coeficientes para % (com semi-elástico para variáveis `_log`)
      - projeto linear com `shock_intensity_pct`
      - referencia fixa inicial: `toneladas_antaq_log`
      - regra relativa para outcomes fora da referência
      - retorna `assumptions` + `executive_summary` + nível de confiança (`forte/moderada/fraca`)
- Frontend:
  - Tipos de API atualizados (`frontend/src/types/api.ts`).
  - Cliente de API atualizado (`frontend/src/api/impactoEconomico.ts`) com `simulateImpact`.
  - Interface no `Module5View.tsx` com card de “Simulador de Impacto”, entrada de choque e resumo executivo.

## 4) Arquitetura da simulação executiva (estado atual)
1. Usuário seleciona uma análise concluída (`analysis_id`).
2. Envia `shock_intensity_pct` e `target_outcomes`.
3. Backend usa `result_full` da análise e estima projeções por outcome em % para esse choque.
4. Frontend exibe:
   - texto explicativo de premissas
   - projeção por variável (valor e confiança)
   - texto executivo por linha (ex.: “Com choque de 10% ...")

## 5) Lacunas de modelagem para virar “investimento real”
Para responder perguntas do tipo investimento->PIB:
1. Construir base de dados de investimento por porto/município/ano e métrica de impacto físico correspondente.
2. Estimar estágio 1 (elasticidade de canal):
   - `Δln(toneladas_antaq) = η · Δln(investimento) + controles + FE`
3. Combinar com estágio 2 já existente (`outcome ~ β · ln(toneladas)`):
   - `Δoutcome% ≈ β * η * Δinvestimento%`
4. Registrar qualidade/identificação do estágio 1 (IV/FE/diagnósticos) para gerar confiança adequada.

## 6) Plano de implementação recomendado (sprintável)

### Sprint 1 – Corrigir base e contratos
- [ ] Criar contrato formal de simulação de investimento (schema + endpoint). 
  - Incluir `shock_mode`: `tonelagem` (hoje) e `investimento` (futuro).
- [ ] Incluir versão de modelo e metadados no retorno (`model_version`, `as_of`, `notes`).
- [ ] Normalizar mensagem de erro e warning para decisão gerencial.

### Sprint 2 – Robustecer backend
- [ ] Expandir endpoint de simulação com CI/intervalos por bootstrap ou delta de p/intervalo.
- [ ] Tratar ausência de resultado inline (`artifact_path`) com fallback amigável.
- [ ] Testes unitários para:
  - resposta vazia/inválida
  - outcome sem coeficiente
  - ratio de referência zero
  - output determinístico para `shock_intensity_pct` conhecido

### Sprint 3 – Camada de gestão (frontend)
- [ ] Card de resumo executivo no topo do Módulo 5 com padrão:
  - “Se investimento (ou movimentação) subir X%, esperado Y% em PIB, com confiança Z”.
- [ ] Painel de risco por output:
  - forte/moderada/fraca + alerta de premissa.
- [ ] Botão de cálculo único para múltiplos outcomes com tabela/mini-cards.
- [ ] Exportação JSON/CSV da simulação para apresentação.

### Sprint 4 – Evolução para investimento real
- [ ] Pipeline ETL de investimento + deflação + consistência temporal.
- [ ] Modelagem 1 (`η`) + armazenamento versionado.
- [ ] Novos payloads no simulador aceitando `investimento_reais` ou `delta_investimento_pct`.
- [ ] Explicação no frontend: distinção entre cenário baseado em movimentação e cenário baseado em investimento.

## 7) Critérios de aceite (DoD)
- Simulador deve responder em menos de 5s para análises já calculadas.
- Para cada output: mostrar efeito central e nível de confiança.
- Interface deve explicar pressupostos claramente em português executivo (sem ambiguidade causal).
- Não permitir inferência de investimento no backend atual sem estágio 1 explicitamente estimado.
- Pelo menos 1 teste backend de simulação e 1 fluxo E2E no frontend.

## 8) Decisão de implementação (recomendação)
1. **Curto prazo (imediato):** manter o simulador sobre choque de movimentação (já pronto no código atual).
2. **Médio prazo:** fechar bloco de comunicação gerencial (texto, confiança, risco).
3. **Longo prazo:** implantar modelo em 2 estágios para investimento->movimentação e então investimento->desfecho.
