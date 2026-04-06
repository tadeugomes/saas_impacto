# Roadmap: Elasticidade Fiscal Porto-Específica

## Status atual

A implementação atual usa **elasticidade média do setor** estimada por OLS log-log
com efeitos fixos de porto, usando dados de 22 portos × 2018-2024.

A calculadora usa o **baseline real** do porto selecionado (ISS do ano mais recente
das DFs), mas aplica o **coeficiente médio** do setor — não um coeficiente porto-específico.

## Por que não implementar regressão porto-específica ainda

Com ~7 observações por porto (2018-2024), a regressão individual produz:
- Intervalos de confiança extremamente amplos
- R² instável
- P-valores frequentemente não-significativos

Regra empírica mínima: **≥ 10 observações** por porto para regressão confiável.

## Critérios para ativar regressão porto-específica

1. **Temporal**: série histórica de ≥ 10 anos por porto.
   Com os dados atuais (2018-), isso será possível a partir de 2028 (com dados de 2027).

2. **OU expansão retroativa**: inclusão de dados históricos 2010-2017 de fontes alternativas
   (SICONFI/FINBRA histórico, TCE estaduais, solicitações diretas aos operadores).

3. **Critério de qualidade** para o toggle na UI:
   - `n_obs >= 10`
   - `p_value < 0.10`
   - `abs(beta_porto - beta_setor) / beta_setor < 0.30`

## Mudanças de arquitetura quando ativado

### Backend (`fiscal_elasticity_service.py`)

Adicionar método:
```python
def compute_porto_elasticity(porto: str, df: pd.DataFrame) -> dict | None:
    sample = df[df["porto"] == porto].copy()
    if len(sample) < 10:
        return None
    # OLS simples sem FE (porto único)
    model = smf.ols("log_trib ~ log_ton", data=sample).fit(cov_type="HC3")
    beta = model.params["log_ton"]
    # ... retornar resultado
```

### Endpoint `/elasticidade` — novo campo na response:
```json
"elasticidade_por_porto": {
  "Porto do Pecém": {"beta": 0.74, "n_obs": 7, "disponivel": false, "motivo": "n < 10"},
  "Portos do Paraná": {"beta": 0.81, "n_obs": 7, "disponivel": false, "motivo": "n < 10"}
}
```

### Frontend — toggle na calculadora:
```tsx
<label>
  <input type="radio" name="elastMode" value="setor" checked /> Elasticidade do setor (recomendado)
</label>
<label>
  <input type="radio" name="elastMode" value="porto" disabled={!portoHasSpecific} />
  Porto-específica {!portoHasSpecific && "(dados insuficientes)"}
</label>
```

### Alerta de divergência:
Se `abs(beta_porto - beta_setor) / beta_setor > 0.30`, exibir:
> ⚠ A elasticidade estimada para este porto diverge 35% da média do setor.
> Use com cautela — pode refletir características atípicas ou ruído amostral.

## Fonte alternativa para expansão retroativa

- **SICONFI/STN histórico**: ISS por município desde 2013 via API.
  Limitação: agrega todos os serviços do município, não só porto.
- **Relatórios anuais antigos**: alguns operadores publicaram DFs desde 2010.
  Requer coleta manual.
- **Abordagem híbrida**: usar FINBRA ISS × participação estimada do porto
  (via % do pessoal ocupado no setor portuário pela RAIS).

## Próxima revisão

Data sugerida para reavaliação: **abril de 2027** (com dados de 2026 disponíveis → n=9).
Data para ativação se dados retroativos não disponíveis: **abril de 2029** (n=11).
