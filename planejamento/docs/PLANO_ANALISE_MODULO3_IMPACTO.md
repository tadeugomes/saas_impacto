# Plano de análise do Módulo 3 — Impacto em Emprego e Trabalho

**Escopo:** Módulo 3 (Recursos Humanos)  
**Data:** 2026-02-22  
**Objetivo:** transformar a leitura descritiva em análise de impacto econômico com perguntas de negócio objetivas, mantendo execução com dados reais de RAIS/ANTAQ e deixando trilha para uso de matriz I-O.

## 1) Perguntas de negócio de impacto

1. **Quanto o porto X (município Y) gera de emprego por ano?**
   - Empregos diretos, indiretos e induzidos.
2. **Quanto cada 1.000 toneladas movimentadas impacta em empregos?**
   - Retorno trabalho por tonelada no município.
3. **Qual o impacto de um choque de carga (ex.: +10% ou +20% no volume)?**
   - Variação esperada de empregos e produtividade.
4. **Qual a participação dos empregos portuários no total local?**
   - Share de empregos diretos no total municipal.
5. **Qual a sensibilidade temporal dos efeitos?**
   - Variação anual (`Δ`) e elasticidade emprego- tonagem.

## 2) Arquitetura analítica proposta

### Fase 0 — Entrega com dados reais (sem I‑O regional completo)

- **RAIS (base real):** `basedosdados.br_me_rais.microdados_vinculos`
  - empregos diretos: `COUNT(*)` com CNAEs portuários
  - empregados totais: `COUNT(*)` sem filtro CNAE
  - filtros: `id_municipio`, `ano`, `vinculo_ativo_3112 = 1`
- **ANTAQ (base real):** `antaqdados.br_antaq_estatistico_aquaviario.v_carga_metodologia_oficial`
  - tonelagem: `SUM(vlpesocargabruta_oficial)` por `municipio`/`ano`
- **Mapeamento porto → município:** usar tabela de vínculo já existente no serviço (`PORT_TO_IBGE_MAPPING`) para entradas por instalação e fallback por município explícito.

### Fase 1 — Ponte para matriz I‑O

1. Ingerir matriz I‑O em mart (setores ↔ setores).
2. Mapear CNAE 2 (RAIS) para setores da matriz.
3. Calcular choque setorial (`Δ` demanda final por tonelada/custo/logística).
4. Aplicar Leontief / multiplicadores de emprego por setor e agregar para município.
5. Devolver decomposição por `direto / indireto / induzido` com incerteza.

## 3) Indicadores propostos (bloco de impacto do módulo 3)

### Bloco A — Impacto absoluto

1. **Empregos diretos do porto no município**
   - Entrada: `id_instalacao` ou `id_municipio`, `ano`
   - Saída: `empregos_diretos`, `nome_municipio`, `ano`
2. **Empregos totais do município**
   - Entrada: `id_municipio`, `ano`
   - Saída: `empregos_totais`
3. **Participação do emprego portuário**
   - `empregos_diretos / empregos_totais`

### Bloco B — Retorno por produtividade

4. **Emprego por carga**
   - `empregos_diretos / tonelagem` (e por 1.000 t)
5. **Produtividade por emprego (já disponível)**
   - `tonelagem / empregos_diretos` e validação de consistência anual

### Bloco C — Impacto agregado

6. **Empregos indiretos e induzidos (proxy)**
   - Aplicar multiplicador de literatura com range (metodologia explicitamente não causal).
7. **Elasticidade (ou sensibilidade) emprego-tonelagem**
   - `Δempregos_diretos / Δtonelagem` com janela de 3 anos móveis.
8. **Cenários de choque**
   - Pergunta de negócio: *“Se tonelagem subir X%, qual o novo total de empregos?”*
   - Retornar linha base, cenário e delta.

## 3.1) Modelo operacional (mínimo funcional)

- Para cada `id_municipio` e `ano`:

1. `empregos_diretos_portuarios`

```sql
COUNT(*) FILTER (CNAE portuário) AS empregos_diretos
```

2. `empregos_totais`

```sql
COUNT(*) AS empregos_totais
```

3. `tonelagem_bruta`

```sql
SUM(vlpesocargabruta_oficial) AS tonelagem_bruta
```

4. `empregos_por_milhao_toneladas`

```text
empregos_diretos / (tonelagem_bruta/1_000_000)
```

5. `participacao_emprego_local`

```text
empregos_diretos * 100 / empregos_totais
```

6. `empregos_indiretos_estimados` e `empregos_induzidos_estimados` (proxy)

```text
empregos_indiretos = empregos_diretos * k_indireto
empregos_induzidos = empregos_diretos * k_induzido
emprego_total_estimado = empregos_diretos + empregos_indiretos + empregos_induzidos
```

7. `cenario_delta_emprego` (quando `delta_tonelagem_pct` informado)

```text
delta_empregos_diretos = empregos_diretos * (delta_tonelagem_pct / 100)
delta_empregos_indiretos = empregos_indiretos * (delta_tonelagem_pct / 100)
delta_empregos_induzidos = empregos_induzidos * (delta_tonelagem_pct / 100)
delta_emprego_total = delta_empregos_diretos + delta_empregos_indiretos + delta_empregos_induzidos
```

- Sempre retornar `correlacao_ou_proxy = true` e texto de limitação metodológica no payload.

## 4) Perguntas adicionais de valor (opcionais)

- Quem ganha mais impacto por tonelada: diretoria local, região metropolitana ou cluster setorial?
- Quais CNAEs do entorno logístico são os mais expostos ao choque portuário?
- Qual o custo por emprego (R$/emprego criado) no cenário corrente e no cenário de choque?

## 5) Regras de interpretação

- Todas as saídas de impacto **direto/indireto/induzido via coeficiente** devem portar o flag:
  - `correlacao_ou_proxy: true`
  - `metodo: "RAIS+ANTAQ (proxy literário)"` ou `metodo: "I-O (futuro)"`.
- Nunca misturar inferência causal com causalidade real:
  - mensagem padrão: “não causal / associativo”.
- Sempre reportar `n_obs`, período usado e cobertura (`municipio/instalação sem dados`).

## 6) Critérios de aceite para Fase 0

1. Endpoint do bloco de impacto aceita `id_instalacao` e `id_municipio`.
2. Consulta para município válido retorna `200` com estrutura:
   - `empregos_diretos`, `empregos_totais`, `empregos_por_milhao_toneladas`,
     `empregos_indiretos_estimados`, `empregos_induzidos_estimados`,
     `emprego_total_estimado`.
3. Consulta com série insuficiente retorna `data=[]` (sem 500).
4. Validação de consistência por município de teste (`3`) com RAIS e ANTAQ reais mostra valores não nulos e coerentes.
5. Interface de interpretação apresenta:
   - indicador absoluto,
   - indicador de eficiência,
   - cenário de choque (ex.: +10% tonelagem).

## 7) Validação real e operação

- Criar script:
  - `scripts/check_module3_real_access.py`
  - Executa `dry_run` de custo e consulta limitada (`LIMIT`) para:
    - empregos diretos por porto/município (`RAIS`)
    - empregos totais (`RAIS`)
    - tonelagem por município (`ANTAQ`)
    - indicadores derivados por tonelada
- Registrar divergência esperada entre base operacional e painel em `warning` de qualidade (sem quebrar consulta).

### Esqueleto de workflow (fases)

1. **Sprint 1:** contratos/metadata + script de validação real + endpoint mínimo (bloco A).
2. **Sprint 2:** bloco B e cenários de choque + cards interpretativos no frontend.
3. **Sprint 3:** bloco C com proxy de multiplicadores + painel de incerteza.
4. **Sprint 4+ (opcional):** Fase I‑O completa com matriz e cálculo por cadeia.
