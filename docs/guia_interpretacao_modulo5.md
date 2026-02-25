# Guia de Interpretação do Módulo 5 — Impacto Econômico Regional

Objetivo: transformar o output técnico dos indicadores em leitura de negócio, com atenção especial aos resultados causais.

## 1) Regra de leitura geral

Para cada indicador, valide em ordem:
1. **Unidade e escopo** (município, período, base territorial).
2. **Cobertura de dados** (anos disponíveis, população de observações, nulidade).
3. **Consistência entre período e contexto** (série curta = menor robustez).
4. **Regras de qualidade** (`>=0`, `%` em faixa, `correlação` em `[-1,1]`, sem NaN/Inf em regressões).

## 2) Interpretação dos indicadores não causais (IND-5.x)

| Indicador | O que representa | Interpretação |
|---|---|---|
| `IND-5.01` PIB Municipal | Valor total do PIB municipal | Quanto maior = maior escala econômica local. Compare com ano anterior e municípios de perfil similar. |
| `IND-5.02` PIB per Capita | PIB dividido pela população | Melhor proxy de renda média municipal. Crescimento real com cautela: comparar ajuste de preços se necessário. |
| `IND-5.03` População | População residente | Base de contexto para indicadores per capita. Variação depende de censo/estimativas e limites administrativos. |
| `IND-5.04`, `IND-5.05` | Estrutura setorial | Mudanças de composição podem indicar reestruturação produtiva local. |
| `IND-5.06` Intensidade Portuária | Tonelada / PIB | Indica exposição logística. Alto valor = maior volume físico por unidade econômica. |
| `IND-5.07` Intensidade Comercial | Comércio exterior / PIB | Mede exposição comercial externa relativa ao tamanho econômico local. |
| `IND-5.08` Concentração Emprego Portuário | % empregos portuários no total | Quanto maior, maior dependência do ciclo portuário no mercado de trabalho. |
| `IND-5.09` Concentração Salarial | % massa salarial portuária no total | Sensibilidade de renda local ao segmento portuário. |
| `IND-5.10` Crescimento PIB | Variação anual do PIB | Taxa positiva significa expansão do ano contra ano anterior (sem sinalizar causalidade direta). |
| `IND-5.11` Crescimento Tonelagem | Variação anual ANTAQ | Mede dinâmica física de movimentação. |
| `IND-5.12` Crescimento Empregos | Variação anual de empregos portuários | Indica dinâmica laboral do segmento; pode ser sazonal com ruído de cadastro. |
| `IND-5.13` Crescimento Comércio | Variação anual do comércio exterior | Exp/Imp agregado por município. |
| `IND-5.18` Participação no PIB Regional | PIB municipal / PIB micro-região | Mede concentração territorial dentro da microrregião. |
| `IND-5.19` Crescimento Relativo ao UF | ΔPIB munícipio – ΔPIB estado | Valor positivo = município cresce mais que a média estadual. |
| `IND-5.20` Razão Emprego Total/Portuário | Emprego total ÷ emprego portuário | Mais alto = maior “massa total” em relação à base portuária; atenção na unidade de análise. |
| `IND-5.21` Índice de Concentração Portuária | Índice composto de dependência/concentração | Use em comparação relativa entre municípios e para ranking. |

## 3) Interpretação dos blocos causais (quando usados)

### 3.1. DiD / DID (Diff-in-Differences)

- **`coef` / `att` positivo**: aumento do resultado no grupo tratado pós-evento em relação ao controle.
- **`coef` negativo**: redução relativa.
- **`p-value` baixo (`<0.05`)**: evidência estatística mais forte (não prova causalidade sozinho).
- **Checagem essencial**: tendência pré-tratamento semelhante entre tratados e controles.

### 3.2. Event Study (TWFE com leads/lags)

- **Períodos pré (`-1`, `-2`, …):** devem ficar perto de zero para suporte de identificação.
- **Períodos pós:** trajetórias consistentes e estáveis aumentam credibilidade.
- **Sinais voláteis** sem base mecânica podem refletir choque não modelado.

### 3.3. IV / 2SLS e Panel IV

- **Coeficiente**: efeito associado ao instrumento (se válido).
- **F-Statistic da primeira etapa**: baixo valor indica instrumento fraco.
- **Validade do instrumento**: premissa central; sem ela o número não é confiável.

### 3.4. Synthetic Control (SCM)

- Compare trajetória do município tratado com o contra-factual sintético.
- **RMSPE pré-tratamento baixo** fortalece a confiança.
- Maior gap positivo/persistente no pós pode apoiar efeito positivo de intervenção.

## 4) Como tratar `coef=None` e `p=N/A` (não falha do sistema)

Essa resposta ocorre quando o método não consegue estimar no recorte:
- série curta,
- pouca variação,
- controles insuficientes,
- filtros com janela que deixa poucas observações.

Nesses casos, não concluir “sem impacto”; concluir “indisponível neste recorte” e rodar:
- janela mais longa,
- recorte mais robusto de municípios,
- ou comparação com outros métodos.

## 5) Semáforo de confiança para decisão

- **🟢 Forte**: sinais coerentes em 2+ métodos + pré-tendência plausível + cobertura de dados adequada.
- **🟡 Moderado**: método único com efeito plausível, mas sem apoio de checagens.
- **🟥 Fraco**: resultados com baixa base de dados, pre-trend ruim, indicador com baixo poder estatístico.

## 6) Checklist de entrega ao tomador de decisão

Para cada análise do Módulo 5, entregue:
1. valor atual + tendência 3-5 anos,
2. comparação com pares/controle,
3. bloco causal (se aplicável) e qualidade estatística,
4. limitações explícitas (fonte, recorte temporal, hipóteses),
5. conclusão executiva (efeito observado, grau de confiança, próximo teste recomendado).

