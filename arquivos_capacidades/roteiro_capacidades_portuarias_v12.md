**Roteiro metodológico para análise de capacidades em terminais portuários**

## Introdução

Capacidade portuária é o volume máximo de carga que um terminal pode movimentar em determinado período, em condições normais de operação, considerados os recursos físicos e operacionais disponíveis. O conceito foi sistematizado pela UNCTAD (1985) na publicação Port Development: a Handbook for Planners in Developing Countries e consolidado no Port Reform Toolkit do Banco Mundial (World Bank, 2007). A capacidade não é uma propriedade isolada de nenhum subsistema: é uma propriedade emergente do sistema como um todo, determinada pelo elo mais restritivo entre as áreas funcionais que o compõem, conforme a Teoria das Restrições (Goldratt, 1990).

O sistema portuário é composto por três áreas funcionais interdependentes. O cais (berços, equipamentos de movimentação e estruturas de acostagem) determina o fluxo de carga entre o navio e a terra e opera como ponto de conversão entre o modo aquático e o modo terrestre. A armazenagem (silos, armazéns, tanques, pátios e retroárea) determina a capacidade de retenção transitória de carga entre o cais e o acesso terrestre; sua rotatividade condiciona diretamente a produtividade efetiva do cais. A hinterlândia (portarias de acesso rodoviário e ferroviário, balanças, pátios de triagem e ramais ferroviários internos) determina a velocidade de entrada e saída de carga do perímetro portuário e, quando congestionada, eleva o tempo de permanência da carga e comprime a capacidade dinâmica de todo o sistema.

A capacidade de um porto não é definida por uma única variável: depende da interação entre o cais (berços, equipamentos de carga e descarga), as estruturas de armazenagem (silos, armazéns, tanques, pátios), o canal de acesso aquaviário (profundidade, regime de maré, balizamento) e os sistemas de acesso terrestre (vias rodoviárias, ramais ferroviários, portarias). O elo mais restritivo entre esses subsistemas determina o throughput máximo efetivo, conforme a lógica da Teoria das Restrições (ToC).

A heterogeneidade dos terminais portuários exige que a metodologia seja adaptável. Portos exportadores de commodities agrícolas com corredores ferroviários de longa distância requerem análises de capacidade de linha férrea que vão além do perímetro do cais. Portos de carga geral com acesso exclusivamente rodoviário demandam modelos de tráfego detalhados nas vias lindeiras. Portos urbanos com operações mistas de cruzeiro e carga precisam contabilizar a sobreposição de berços entre passageiros e carga. Portos administrados por autarquias estaduais com sistemas gerenciais consolidados frequentemente já dispõem de indicadores operacionais calculados que dispensam o recálculo a partir dos dados brutos. Este roteiro incorpora essas variações como condições de aplicação de cada passo.

O roteiro está organizado em onze passos sequenciais. Cada passo especifica os dados de entrada necessários, as fórmulas aplicadas, os parâmetros que exigem calibração local e as fontes de informação recomendadas. As fontes recorrentes são o Estatístico Aquaviário da ANTAQ (que registra, para cada atracação, o tipo de navio, o tipo de carga, a classe de embarcação por DWT, o berço utilizado, as toneladas movimentadas e os tempos operacionais), os relatórios de gestão da autoridade portuária, os Planos de Desenvolvimento e Zoneamento (PDZ) e os contratos de arrendamento.

Em portos com sistemas gerenciais consolidados, como Paranaguá, os indicadores operacionais já calculados pela autoridade portuária podem ser adotados diretamente, desde que a série histórica seja auditável e consistente com os registros da ANTAQ.

# 1. Estrutura do capítulo de capacidade

## 1.1. Lógica metodológica

O capítulo de capacidade está organizado em três blocos analíticos sequenciais. O primeiro estima a capacidade de cada subsistema de forma independente: cais (Passos 1 a 3), armazenagem (Passos 4 e 5) e hinterlândia (Passo 6). O segundo consolida os resultados por meio da integração sistêmica (Passo 7), que identifica o elo mais restritivo do sistema portuário pelo critério da Teoria das Restrições. O terceiro projeta a capacidade para os horizontes de planejamento (Passos 8 e 9) e compara o resultado com as curvas de demanda (Passo 10), identificando o ano de saturação de cada subsistema.

A análise é realizada por perfil de carga j (contêiner, carga geral, granel agrícola, granel industrial, líquido a granel, entre outros) e por horizonte temporal t (ano-base, 2030, 2040, 2050). A fórmula de integração sistêmica é C_sistema(j,t) = min(C_cais, C_arm, C_hint) para cada combinação de j e t (Eq. 13). Quando um subsistema não opera o perfil de carga analisado, como em porto sem acesso ferroviário para granel agrícola, o termo correspondente é removido da expressão.

## 1.2. Formatos de apresentação dos resultados

Os resultados do capítulo de capacidade são apresentados em três formatos. O primeiro é o Quadro 5, o quadro-síntese de consolidação sistêmica, que organiza em uma única tabela as capacidades de todos os subsistemas, a capacidade sistêmica resultante e a demanda projetada para cada perfil de carga e horizonte temporal. O quadro-síntese permite identificar visualmente o elo mais restritivo e o ano de saturação de cada subsistema. O segundo formato é o gráfico de Capacidade × Demanda, especificado no Passo 10, que apresenta as curvas de capacidade sistêmica e de demanda projetada em um mesmo eixo temporal, identificando o ponto de cruzamento (ano de saturação) e a magnitude do déficit projetado. O terceiro formato aplica-se à análise de hinterlândia: mapa de acessos que representa os eixos rodoviários e ferroviários com os volumes de fluxo estimados e os pontos de congestionamento identificados.

## 1.3. Aspectos analíticos centrais

A análise de capacidade aborda três aspectos que não se esgotam no cálculo das fórmulas. O primeiro é a identificação de gargalos: a Eq. 13 aponta diretamente o elo mais restritivo por período e perfil de carga; quando o gargalo se desloca ao longo do tempo, por exemplo do cais para a armazenagem após ampliação de berços, esse deslocamento deve ser explicitado. O segundo aspecto é a análise dos níveis de serviço: os indicadores BOR observado versus BOR admissível, o nível de serviço ferroviário (razão entre fluxo estimado e capacidade da linha) e a taxa de utilização do sistema de armazenagem informam se o terminal opera próximo ao limite de congestionamento. O terceiro é a aderência à demanda: a comparação entre capacidade sistêmica calculada e curvas de demanda projetada (cenário de referência e cenários alternativos) determina a janela de folga operacional e o prazo estimado para saturação, embasando as recomendações de investimento.

## 1.4. Análise sistêmica integrada: cais como elemento estruturante e interdependência dos subsistemas

A capacidade efetiva do terminal deve ser definida a partir da análise integrada das suas áreas funcionais. O cais constitui, em geral, o principal elemento estruturante do sistema portuário: a movimentação só ocorre quando há berço disponível, equipamento operacional e navio atracado. Os subsistemas de armazenagem e hinterlândia são dimensionados a partir do throughput que o cais pode gerar, e suas capacidades devem ser referenciadas a esse valor. A relação de dependência, porém, é bidirecional: a armazenagem com baixa rotatividade impede a liberação de área para novos lotes, reduzindo a produtividade efetiva do cais; congestionamento no gate e filas externas ao porto atrasam a retirada de carga, elevam o dwell time e comprimem a capacidade dinâmica de todo o sistema. A análise deve avaliar essas interdependências de forma sistêmica, evitando o cálculo isolado de cada subsistema sem verificação da consistência mútua.

Quando a armazenagem se configura como elo limitante, a análise deve incorporar o número máximo de giros operacionais viáveis, considerando os condicionantes que elevam o dwell time efetivo além do tempo de permanência da carga: (i) tempo de formação de lotes, que é o intervalo mínimo entre o início do preenchimento do silo ou armazém e o início da operação de carga para o navio; (ii) tempo de limpeza das estruturas entre lotes de produtos diferentes ou com exigências de higiene específicas (fertilizantes, açúcar, farelo de soja); (iii) intervalos de manutenção das instalações (calibração de balanças, limpeza de fossos de moegas, manutenção de transportadores); e (iv) restrições de segregação de produtos incompatíveis que impedem o uso integral da capacidade nominal. O dwell time efetivo (DT_ef = DT_permanencia + T_lote + T_limpeza + T_manutencao) produz um giro real inferior ao giro nominal, e a CD deve ser recalculada com DT_ef em vez de DT. O dwell time de equilíbrio que eliminaria a restrição é: DT_eq = CE × DOA / C_cais.

## 1.5. Fluxo metodológico consolidado

O Quadro 13 apresenta o fluxo metodológico consolidado do roteiro, organizado em seis fases sequenciais que cobrem desde a coleta dos dados primários e secundários até a elaboração do diagnóstico final e da memória de cálculo. As fases são interdependentes: cada saída alimenta a etapa seguinte, e a consistência entre parâmetros e cenários deve ser verificada ao final da Fase 4 antes de prosseguir para a projeção.

**Quadro 13:** Fluxo metodológico consolidado: fases, etapas, atividades e saídas

  -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  **Fase**   **Etapa**                              **Passos**    **Atividades e procedimentos**                                                                                                                                                                                                                                     **Saída esperada**
  ---------- -------------------------------------- ------------- ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ ------------------------------------------------------------------------------------------------------------
  1          Coleta de dados                        Passo 1       Levantamento de dados físicos dos berços e equipamentos; download do Estatístico Aquaviário ANTAQ; aplicação do questionário aos terminais (Quadro 9); coleta de dados meteorológicos e hidrográficos (INMET, DHN) para cálculo de H_cli                           Base de dados bruta organizada por subsistema; Matriz de Origem dos Dados (Quadro 9) preenchida

  2          Tratamento e validação                 Passo 1       Exclusão de replicatas do Estatístico ANTAQ (groupby IMO + timestamps); cálculo de Ta, T_op, Inop.Pré e Inop.Pós; filtragem por IQR; cálculo de Lm e prancha por grupo; aplicação dos fatores de conversão TEU e CEU (Quadro 8)                                    Parâmetros operacionais depurados (Planilha 2); série histórica limpa por perfil de carga

  3          Cálculo de capacidade por subsistema   Passos 2--7   Cálculo de H_ef (Eq. 1c, Quadro 12); aplicação das Eqs. 1a ou 1b (C_cais) e valoração de parâmetros (Quadros 6 e 10); ajuste de cruzeiros (Eq. 3); cálculo de CE e CD (Eqs. 4--5, Quadro 7); verificação do canal (Eq. 7); cálculo de C_rod e C_fer (Eqs. 8--12)   C_cais(j), C_arm(j), C_hint(j) para o Cenário Atual (ano-base)

  4          Integração sistêmica                   Passo 9       Aplicação da Eq. 13 para cada perfil de carga j e horizonte t: C_sistema(j,t) = min(C_cais, C_arm, C_hint); identificação do elo restritivo; preenchimento do Quadro 5 (quadro-síntese)                                                                            C_sistema(j,t) e elo restritivo identificado por perfil/horizonte; Quadro 5 preenchido

  5          Projeção e cenários                    Passo 10      Parametrização do Cenário Futuro: ganhos de eficiência, modernização e investimentos do PIT; elaboração da tabela de premissas; recalibração das equações para cada horizonte; confronto com demanda projetada (PNLP/Plano Mestre)                                 C_sistema por cenário e horizonte; gráfico Capacidade × Demanda; ano de saturação identificado

  6          Análise final e memória                Passo 11      Identificação de gargalos; análise de níveis de serviço (BOR, LOS, utilização ferroviária); verificação de aderência à demanda; elaboração da memória de cálculo com planilhas de apoio (Planilhas 1 a 5)                                                          Diagnóstico de capacidade completo; memória de cálculo rastreável; recomendações de investimento ou gestão
  -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Fonte: elaboração própria.

# 2. Passo 1: Levantamento e organização dos dados primários do cais

O ponto de partida da análise é o levantamento das características físicas e operacionais de cada berço. Os dados necessários são:

\(a\) Características físicas: comprimento útil de cada berço (m), profundidade junto ao berço (m), calado máximo admissível por tipo de embarcação (m). Fonte: cadastro de berços da autoridade portuária, complementado pela Portaria de Tráfego Marítimo vigente e por dados gerais disponíveis no sítio da autoridade portuária.

\(b\) Equipamentos: tipo (guindastes, shiploaders, esteiras, bombas, moegas, sugadores), capacidade nominal (t/h ou moves/h), ano de fabricação, operador responsável. Fonte: autoridade portuária ou operador do terminal. Em portos com arrendatários múltiplos, coletar diretamente com cada operador por meio de fichas padronizadas.

\(c\) Indicadores operacionais históricos: lote médio por atracação (Lm, em t ou TEU), prancha média operacional (P, em t/h ou moves/h), tempos inoperantes pré-operação e pós-operação (h), tempo de operação (h), tempo total atracado (Ta, h) e intervalo entre atracacões sucessivas (a, clearance, tipicamente 3,0 a 3,5h). Fonte: Estatístico Aquaviário da ANTAQ, depurado por ano-base, por terminal e por grupo de carga.

\(d\) Parâmetros de benchmark: índice máximo de ocupação admitida (BOR) e produtividade de referência por tipo de carga e sistema operacional. Fonte: quadros de referência de BOR e de produtividade apresentados no Passo 2 (UNCTAD, 1985; PIANC, 2014; benchmarks ANTAQ).

As fontes primárias variam conforme o modelo de gestão. Em portos operados por terminais arrendados sem centralização de dados, a coleta junto a cada operador é obrigatória; em portos com gestão centralizada, a autoridade portuária frequentemente fornece os dados consolidados. Em qualquer caso, a conferência cruzada entre os dados fornecidos pelos operadores e os registros do Estatístico Aquaviário da ANTAQ é procedimento de validação obrigatório.

## 2.1. Fatores de conversão de unidades

A consistência das unidades de medida ao longo do roteiro depende da aplicação correta de fatores de conversão para os dois tipos de operação com unidades padronizadas internacionalmente: terminais de contêineres e terminais Ro-Ro. O Quadro 8 especifica os fatores de referência e os procedimentos de calibração local.

**Quadro 8:** Fatores de conversão de unidades: TEU e CEU

  ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  **Fator**             **Definição**                                                                                                                  **Valor de referência**                                                                     **Aplicação**                                                                                         **Procedimento de calibração**
  --------------------- ------------------------------------------------------------------------------------------------------------------------------ ------------------------------------------------------------------------------------------- ----------------------------------------------------------------------------------------------------- ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  TEU                   Unidade padrão de contêiner de 20 pés; converte número de caixas em TEU                                                        1,40--1,65 TEU/caixa                                                                        Terminais de contêineres: cálculo de Lm (TEU/atracação) e capacidade (TEU/ano)                        Calcular média histórica de TEU/caixa com o Estatístico ANTAQ (campo TEU ÷ número de atracacões por grupo); valor de referência setorial: 1,55 para portos de carga mista

  CEU                   Car Equivalent Unit: unidade padrão de veículo para operações Ro-Ro; converte unidades heterogêneas em equivalente-automóvel   1 automóvel = 1 CEU; 1 ônibus = 3 CEU; 1 caminhão leve = 2 CEU; 1 caminhão pesado = 4 CEU   Terminais Ro-Ro e automotivos: cálculo de Lm (CEU/atracação) e capacidade (CEU/ano)                   Adotar tabela de equivalências do operador ou armador; quando não disponível, obter mix de veículos via questionário ao arrendatário

  Fator de peso TEU→t   Peso médio por TEU (tara + carga) para conversão de unidades volumétricas em gravimétricas                                     10--14 t/TEU                                                                                Necessário quando curvas de demanda estão em toneladas e capacidade calculada em TEU, ou vice-versa   Calcular: movimentação total (t) ÷ movimentação total (TEU) do Estatístico ANTAQ; valor padrão quando não disponível: 12 t/TEU
  ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Fonte: ANTAQ; UNCTAD (1985); prática setorial.

## 2.2. Matriz de origem dos dados

Para garantir rastreabilidade e transparência metodológica, cada dado utilizado deve ser classificado quanto à sua origem: primária, coletada diretamente junto aos terminais por meio de questionários ou visitas de campo, ou secundária, obtida de bases públicas ou documentos oficiais. A distinção entre as duas categorias determina o procedimento de validação exigido: dados primários requerem conferência com fonte documental secundária disponível; dados secundários requerem conferência com a realidade operacional do terminal, obtida por questionário ou visita. O Quadro 9 apresenta a matriz de origem para os dados exigidos por este roteiro.

**Quadro 9:** Matriz de origem dos dados: categoria, fonte e validação

  ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  **Dado**                                                                  **Categoria**            **Fonte**                                         **Instrumento de coleta**                                                                **Validação cruzada**
  ------------------------------------------------------------------------- ------------------------ ------------------------------------------------- ---------------------------------------------------------------------------------------- ------------------------------------------------------------------------------------------------------------------------------
  Características físicas dos berços (comprimento, profundidade, calado)    Secundária               PDZ, cadastro da AP                               Consulta ao sistema de gestão portuária (SGP) ou similar                                 Portaria de Tráfego Marítimo vigente; levantamento de campo quando divergente

  Tipo e capacidade nominal dos equipamentos                                Primária                 Operador / arrendatário                           Questionário padronizado aplicado ao terminal                                            Especificação técnica do fabricante; relatório de inspeção; confronto com produtividade observada no Estatístico ANTAQ

  Movimentação histórica por atracação (lote, tempos operacionais, berço)   Secundária               Estatístico Aquaviário ANTAQ                      Download via API ou portal ANTAQ; recorte por porto e período                            Conferência com relatórios operacionais da AP; tratamento de replicatas (Passo 1)

  BOR histórico e indicadores de ocupação                                   Secundária ou Primária   ANTAQ / sistema gerencial da AP                   Cálculo a partir do Estatístico ANTAQ ou download direto do sistema da AP                Se AP usa metodologia própria, verificar compatibilidade com os procedimentos deste roteiro; documentar metodologia adotada.

  Área de armazenagem e densidade de estocagem (A_util, ρ, f_s)             Primária                 Operador / arrendatário                           Questionário + levantamento de campo                                                     Confronto com PDZ, contrato de arrendamento e planta atualizada do armazém ou pátio

  Dias de permanência da carga (DOA)                                        Primária                 Operador / arrendatário                           Questionário; registros de sistema TOS ou RFID quando disponíveis                        Validar com dados de faturamento de armazenagem; comparar com DOA de terminais similares

  Dados de hinterlândia (contagens, V/C, PEF)                               Secundária               DNIT / PRF (rodovias); ANTT / EPL (ferrovias)     Download de documentos públicos; contagem primária quando não existir contagem recente   Confronto dos volumes estimados com movimentação do Estatístico ANTAQ desagregada por modal

  Projetos do PIT e obras programáveis                                      Secundária               EPL (Plano Mestre); ANTAQ (editais e contratos)   Download de documentos públicos; consulta direta à AP                                    Confirmar status de execução, cronograma e parâmetros de capacidade previstos com a autoridade portuária
  ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Fonte: elaboração própria.

## 2.3. Tratamento de replicatas

\[Nota técnica\] Recomendação: incluir etapa de conciliação cruzada entre as bases da autoridade portuária local e da ANTAQ antes do tratamento estatístico. As duas fontes divergem sistematicamente em campos como data de desatracação e tipo de carga, e a ausência de critério de prevalência pode propagar erros para os indicadores derivados.

A base de dados do Estatístico Aquaviário da ANTAQ pode conter registros duplicados para a mesma operação, especialmente em cargas conteinerizadas, onde a ANTAQ frequentemente registra a mesma atracação em múltiplas linhas. Antes de calcular indicadores, é obrigatório identificar e consolidar replicatas. O procedimento consiste em agrupar os registros pelo conjunto de campos IMO da embarcação, Data da Chegada, Data da Atracacão, Data do Início da Operação, Data do Término da Operação e Data da Desatracação. Para cada grupo, somar a movimentação (t ou TEU) e manter apenas um registro. A ausência desse tratamento gera dupla contagem de atracacões e distorce os indicadores de tempo e produtividade.

## 2.4. Cálculo dos tempos operacionais

A partir dos 5 timestamps da ANTAQ por atracação, calcular os seguintes tempos (em horas):

**(a) Tempo inoperante pré-operação (Inop.Pré**): data do Início da Operação menos Data da Atracacão. Compreende o período entre a atracação do navio e o início efetivo da operação de carga.

**(b) Tempo de operação (T_op**): data do Término da Operação menos Data do Início da Operação.

**(c) Tempo inoperante pós-operação (Inop.Pós**): data da Desatracação menos Data do Término da Operação.

**(d) Tempo de espera (Line-up**): data da Atracacão menos Data da Chegada. Não compõe o tempo atracado, mas é indicador de nível de serviço.

\(e\) Produtividade por atracação: movimentação (t ou TEU) dividida pelo Tempo de operação (t/h ou TEU/h). Registros com Tempo de operação igual a zero ou negativo devem ser descartados.

## 2.5. Depuração estatística dos indicadores operacionais

\[Nota técnica\] Recomendação: incorporar a prancha mínima regulamentada como filtro de depuração adicional. Operações com produtividade inferior à prancha contratual indicam anomalia operacional (greve, quebra de equipamento, condição climática não registrada) e devem ser sinalizadas antes da inferência estatística.

Os tempos operacionais e a produtividade extraídos da ANTAQ apresentam valores atípicos (outliers) causados por registros errôneos, paralisações prolongadas ou operações atípicas. A depuração é realizada pelo método do intervalo interquartil (IQR), aplicado separadamente a cada combinação de terminal, berço, tipo de carga, sentido (embarcado/desembarcado) e navegação (longo curso/cabotagem). O procedimento é:

\(1\) Para cada grupo, calcular o primeiro quartil (Q1) e o terceiro quartil (Q3) da variável.

\(2\) Calcular IQR = Q3 − Q1.

\(3\) Definir o limite inferior (L_inf = Q1 − 1,5 × IQR) e o limite superior (L_sup = Q3 + 1,5 × IQR).

\(4\) Calcular a média da variável utilizando apenas as observações contidas no intervalo \[L_inf, L_sup\].

A depuração por IQR é aplicada a três variáveis: Inop.Pré, Produtividade e Inop.Pós. As médias depuradas resultantes são os parâmetros de entrada para o cálculo de capacidade no Passo 2. Esse tratamento assegura que os parâmetros operacionais reflitam a operação típica do terminal, sem distorção por eventos pontuais. O registro da depuração (quantidade de observações descartadas, limites utilizados) deve constar na memória de cálculo.

# 3. Passo 2: Cálculo da capacidade teórica do cais e indicadores de ocupação

A capacidade teórica do cais expressa a movimentação máxima anual do conjunto de berços, medida em toneladas por ano (t/ano) ou em TEU por ano para terminais de contêineres. Duas formulações são aplicáveis, conforme a disponibilidade e o formato dos dados operacionais.

Entende-se por capacidade de cais a quantidade máxima de carga, expressa em toneladas por ano (t/ano) ou em TEU por ano, que pode ser movimentada pelos berços do terminal em determinado período, dados os recursos físicos (comprimento e profundidade do cais, número de berços), os equipamentos de movimentação e as horas efetivamente disponíveis para operação. A expressão em toneladas aplica-se a graneis sólidos, graneis líquidos e carga geral; em TEU, a terminais de contêineres.

## 3.1. Três níveis de capacidade de cais

A análise de capacidade do cais distingue três níveis: (a) capacidade recomendada, calculada com a taxa de ocupação admissível dos berços (TUB_adm) como limitador, conforme os parâmetros do Quadro 1; representa o teto operacional sustentável sem degradação do nível de serviço; (b) capacidade observada, correspondente à movimentação registrada no ano de referência, calculada a partir dos dados do Estatístico Aquaviário da ANTAQ; indica a utilização real dos berços e serve como base para calibração dos parâmetros das Eqs. 1a e 1b; e (c) capacidade projetada adotada, calculada com os parâmetros projetados para cada horizonte de planejamento (ganhos de produtividade, modernização de equipamentos, alteração de mix de cargas), conforme o Passo 10. A diferença entre a capacidade recomendada e a capacidade observada indica o potencial de ganho sem novos investimentos em infraestrutura.

Os parâmetros empregados nas equações deste passo são apresentados com símbolo, definição, unidade de medida, fonte primária e procedimento de obtenção nos Quadros 6, 7 e 10. Os parâmetros de indisponibilidade climática são detalhados no Quadro 12. Nenhum índice ou indicador empregado no modelo de cálculo deve ser utilizado sem que seu significado, unidade e fonte estejam registrados nesses quadros ou na memória de cálculo do estudo.

## 3.2. Critério de segmentação dos trechos de cais

A capacidade teórica do cais (C_cais) é calculada por trecho, entendido como o conjunto de berços com características operacionais homogêneas quanto à tipologia de carga, ao equipamento de movimentação, ao regime jurídico de uso e às restrições físicas. A definição dos trechos precede o cálculo e deve ser explicitada e justificada no estudo. O Quadro 14 apresenta os cinco critérios que orientam essa segmentação.

**Quadro 14:** Critérios de segmentação dos trechos de cais

  ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  **Critério de segmentação**      **Regra operacional**                                                                                                                                                                                                                                                                                      **Exemplo de aplicação**
  -------------------------------- ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- -------------------------------------------------------------------------------------------------------------------------------
  Tipologia de carga               Cada perfil de carga (granel sólido, granel líquido, contêiner, carga geral, Ro-Ro/automotivo) forma trecho distinto quando os berços não forem operacionalmente intercanbiáveis para o mesmo perfil. A agregação de berços com perfis distintos produz média de produtividade sem respaldo operacional.   Terminal com berços de soja e de fertilizante: dois trechos se o shiploader não opera com fertilizante a granel.

  Equipamento de movimentação      Berços com equipamentos de produtividades não comparáveis (guindaste STS portainer, guindaste móvel, Equipamento de movimentação shiploader,, grab, braço de carregamento) são tratados como trechos distintos, pois P_i varia de forma não uniforme entre equipamentos.                                   Berço com guindaste STS fixo e berço adjacente com guindaste móvel: dois trechos, ainda que no mesmo terminal de contêineres.

  Regime jurídico de uso           Berços de uso privativo exclusivo, arrendados e de uso público apresentam distribuições de chegada de navios e valores de BOR_adm distintos. Agregá-los invalidaria o parâmetro BOR_adm derivado pela fórmula de Erlang-C.                                                                                 Cais público com atendimento a múltiplos usuários e berço arrendado com tráfego cativo: dois trechos.

  Restrições físicas               Diferença de comprimento de berço superior a 20% ou de calado disponível superior a 1 m justifica segmentação, pois o perfil de navio atendido (Lm e Ta na Eq. 1b) difere materialmente entre berços.                                                                                                      Berço com calado de 12 m e berço adjacente com 16 m na mesma face de cais: dois trechos.

  Indisponibilidade diferenciada   Berços com diferença superior a 10% em H_ef --- decorrente de H_cli, H_mnt ou H_nav distintos --- formam trechos separados. Agregar berços com H_ef heterogêneos produz estimativa de capacidade enviesada e de difícil rastreabilidade.                                                                   Berço abrigado e berço exposto ao regime de ventos no mesmo terminal: H_cli distintos impõem dois trechos.
  ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Fonte: elaboração própria.

## 3.2.1. Tratamento de berços conjugados: regra de conversão para berço-equivalente

O cálculo da capacidade de cais pelas Eqs. 1a e 1b pressupõe que cada berço opera como unidade discreta e independente. Em terminais que recebem navios cujo comprimento total (LOA) excede o comprimento do berço individual, uma única embarcação pode ocupar dois ou mais berços adjacentes, bloqueando-os simultaneamente para outras operações. Essa configuração, denominada operação em berço conjugado, distorce o número de berços operacionais (b) e a taxa de ocupação de berço (BOR) se não for tratada explicitamente no cálculo.

Para que a capacidade estimada reflita a disponibilidade real do cais, o roteiro requer a aplicação de um fator de conjugação (F_conj) nos trechos onde tais operações são recorrentes. O procedimento tem quatro etapas.

Etapa 1, identificação. A partir do Estatístico Aquaviário da ANTAQ e dos registros operacionais da autoridade portuária, identificar as atracações em que o LOA do navio resultou na ocupação simultânea de N berços físicos (N \> 1). Todas as atracações do trecho de cais, dentro do período de análise, devem ser classificadas quanto ao número de berços ocupados.

Etapa 2, cálculo do fator de conjugação. Para cada trecho de cais e para cada perfil de carga j, calcular F_conj como a média ponderada do número de berços físicos ocupados por atracação, ponderada pelo tempo de permanência: F_conj = soma(N_berços x T_atracação) / soma(T_atracação), onde N_berços é o número de berços físicos ocupados pela atracação e T_atracação é o tempo de permanência no berço. O cálculo deve ser realizado por perfil de carga j, de modo consistente com a segmentação definida no Passo 3 do roteiro. Quando não há conjugação, F_conj = 1.

Etapa 3, ajuste do número de berços operacionais. O número de berços (b) utilizado na Eq. 1b e no cálculo do BOR (Eq. 2a) deve ser substituído por b_efetivo = b_físico / F_conj. Esse ajuste reduz o denominador do cálculo de capacidade proporcionalmente ao grau de conjugação observado. O lote médio (Lm) e o tempo atracado (Ta) não requerem ajuste, pois já são medidos por operação (navio), e não por berço individual.

Etapa 4, recálculo de BOR e C_cais. Com b_efetivo, recalcular o BOR pela Eq. 2a e a C_cais pela Eq. 1b. A memória de cálculo deve registrar explicitamente o valor de F_conj adotado, o número de atracações conjugadas identificadas, o período de referência e a fonte dos dados utilizados.

A ausência desse tratamento tende a superestimar a capacidade do cais e a subestimar o BOR observado, porque o modelo contaria berços como disponíveis quando, na prática, estão bloqueados por uma atracação conjugada. O registro do F_conj na memória de cálculo permite que o resultado seja auditado e atualizado quando a frota atendida pelo terminal se alterar.

## 3.3. Horas operacionais efetivas dos berços

O valor 8.760 h/ano representa o máximo teórico do calendário anual; não é o parâmetro de entrada para as equações de capacidade. O parâmetro H efetivo (H_ef) deve ser calculado individualmente para cada terminal, descontando todos os períodos de indisponibilidade operacional. A capacidade deve ser calculada a partir das horas efetivamente disponíveis para operação de carga e descarga, descontados todos os períodos de indisponibilidade dos berços. A fórmula geral é:

> H_ef = H_cal − H_cli − H_mnt − H_nav − H_out (Eq. 1c)

onde H_cal = 8.760 h/ano (horas do calendário); H_cli = horas perdidas por restrições climáticas (ventos fortes, ondulação severa, nevoeiro); H_mnt = horas de manutenção programada de equipamentos e paradas de inspeção dos berços; H_nav = horas de restrição de navegação (janelas de maré, operações noturnas proibidas, dragagem em curso); e H_out = outros períodos de indisponibilidade (paralisacões, força maior, eventos excepcionais).

Os valores de H_cli, H_mnt e H_nav devem ser obtidos diretamente dos terminais por meio do questionário padronizado (Quadro 9) e dos relatórios operacionais da autoridade portuária. A ANTAQ disponibiliza, para alguns portos, dados sobre paradas climáticas e de manutenção no Anuário Estatístico Aquaviário. Na ausência de dados, adotar H_ef = 8.000 h/ano para terminais sem restrição climática severa, documentando a premissa na memória de cálculo do Passo 11. Para terminais em regiões de condições meteorológicas adversas frequentes, como portos do Sul ou portos lagunares, H_ef pode ser inferior a 7.000 h/ano. A Eq. 1c substitui H_total em todas as aplicações das Eqs. 1a e 1b.

## 3.4. Metodologia de obtenção do fator de indisponibilidade climática

O componente H_cli da Eq. 1c exige tratamento específico, uma vez que a magnitude da indisponibilidade climática varia conforme o tipo de carga e o equipamento utilizado: operações Ro-Ro e de líquido a granel (com mangotes) são suspensas a velocidades de vento e alturas de onda inferiores às toleradas por shiploader de granel sólido. A metodologia de obtenção de H_cli compreende três etapas sequenciais.

\(a\) Coleta dos dados meteorológicos históricos: obter série horária de pelo menos 5 anos dos seguintes parâmetros: velocidade média do vento (m/s, média de 10 minutos), precipitação (mm/h), visibilidade horizontal (m) e, quando aplicável, altura significativa de ondas (Hs, m). As fontes primárias são: INMET (estações meteorológicas automáticas próximas ao porto, série disponível em banco.dados.inmet.gov.br); DHN/Centro de Hidrografia da Marinha (ondas e correntes); estações meteorológicas próprias da autoridade portuária, quando disponíveis.

\(b\) Aplicação dos limiares de suspensão por tipo de operação: para cada hora da série histórica, verificar se ao menos um parâmetro meteorológico ultrapassou o limiar de suspensão de operações para o perfil de carga analisado. H_cli é a contagem anual das horas em que pelo menos um limiar foi excedido. Os limiares de referência por tipo de operação são apresentados no Quadro 12. Quando o terminal já dispuser de registros internos de paradas climáticas auditados pela AP, esse dado substitui o cálculo por limiares, sendo obrigatório documentar o período de referência e o critério adotado.

\(c\) Análise de sensibilidade: calcular H_cli em três cenários de limiar: (i) limiar de referência conforme Quadro 12; (ii) limiar 20% mais restritivo (simula modernização de equipamentos com menor tolerância a ventos); (iii) limiar 20% menos restritivo (simula condições futuras de melhoria de previsão e janelas operacionais). Para cada cenário, recalcular H_ef e C_cais pela Eq. 1b e registrar a variação percentual em relação ao cenário-base. Variações superiores a 5% em C_cais indicam alta sensibilidade climática e devem ser reportadas no diagnóstico.

**Quadro 12:** Limiares de suspensão de operações por condição climática e tipo de carga

  --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  **Tipo de operação**                        **Parâmetro meteorológico**                               **Limiar de suspensão**                         **Fonte dos dados**                                                         **Análise de sensibilidade**
  ------------------------------------------- --------------------------------------------------------- ----------------------------------------------- --------------------------------------------------------------------------- ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  Contêiner (guindastes STS / portainer)      Velocidade média do vento (10 min)                        \> 14 m/s (50 km/h)                             INMET; estação anemométrica do porto; manual do fabricante do equipamento   Variar limiar para 12 m/s e 16 m/s; calcular diferença percentual em H_cli e impacto em C_cais; reportar resultado na memória de cálculo

  Granel sólido (grab, sugador, shiploader)   Velocidade do vento; precipitação intensa                 \> 12 m/s (vento); \> 15 mm/h (chuva intensa)   INMET; relatórios operacionais do terminal                                  Variar limiar de vento para 10 m/s e 14 m/s; avaliar impacto em H_cli; graneis agrícolas têm restrições adicionais de umidade relativa (\> 85%) para farelo

  Líquido a granel (dutos; mangotes)          Velocidade do vento; altura significativa de ondas (Hs)   \> 15 m/s (vento); Hs \> 0,8 m                  DHN / Centro de Hidrografia da Marinha; INMET; relatórios operacionais      Hs é o parâmetro crítico; variar entre 0,6 m e 1,0 m; operadores de terminais petrolíferos frequentemente dispõem de limiares contratuais com armadores

  Carga geral (guindaste móvel)               Velocidade do vento; visibilidade horizontal              \> 12 m/s (vento); \< 500 m (nevoeiro)          INMET; DHN / Serviço de Previsão Marítima                                   Nevoeiro é fator determinante em portos lagunares e de estuário; validar frequência histórica com REDEMET / INMET; variar limiar de visibilidade entre 300 m e 1.000 m

  Ro-Ro e automotivo (rampa de popa)          Velocidade do vento; Hs; corrente de maré                 \> 10 m/s (vento); Hs \> 0,5 m                  DHN; INMET; normas operacionais do armador                                  Operações Ro-Ro têm os limiares mais restritivos; correntes de maré superiores a 2,5 nós também suspendem a manobra em portos de baía; consultar Plano de Manobra do porto
  --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Fonte: INMET; DHN/Marinha; manuais de equipamentos; elaboração própria.

### **3.4.1. Fontes de dados climáticos e projeção de H_cli em cenários futuros**

O procedimento de cálculo de H_cli descrito na seção 3.4 requer dados meteorológicos horários cuja qualidade e representatividade condicionam a confiabilidade do resultado. Esta subseção especifica as fontes de dados obrigatórias, o período mínimo de cobertura e o tratamento a ser adotado para a projeção de H_cli nos cenários futuros.

A fonte primária de dados meteorológicos é o Instituto Nacional de Meteorologia (INMET), que mantém estações automáticas com registro horário de velocidade do vento, precipitação, umidade relativa, temperatura e pressão atmosférica. Para terminais costeiros, os dados de altura significativa de ondas e período de onda devem ser obtidos junto à Diretoria de Hidrografia e Navegação (DHN) da Marinha do Brasil ou, quando disponíveis, junto a sistemas de monitoramento próprios da autoridade portuária. Os dados de visibilidade, quando não registrados pela estação INMET mais próxima, podem ser complementados por registros aeronáuticos (METAR/REDEMET) do aeródromo mais próximo ao complexo portuário.

A série histórica deve cobrir, no mínimo, os últimos 20 anos de registros horários disponíveis na data de elaboração do estudo. Esse período permite capturar ciclos climáticos interanuais (El Niño/La Niña) e reduzir a influência de anos atípicos sobre a média de H_cli. Quando a estação mais próxima não dispuser de 20 anos de registros horários, o estudo deve utilizar a série mais longa disponível e registrar a limitação na memória de cálculo. A série de normais climatológicas vigente publicada pelo INMET deve ser consultada como referência de controle para validar a representatividade dos dados horários utilizados.

Para os cenários futuros (horizontes de 5, 10 e 25 anos), H_cli não deve ser mantido constante e igual à média histórica sem justificativa. O estudo deve verificar se há tendência estatística nas séries de precipitação, velocidade do vento e temperatura da estação de referência, utilizando teste de Mann-Kendall ou regressão linear sobre médias anuais. Quando a tendência for estatisticamente significativa (p \< 0,05), a projeção de H_cli nos cenários futuros deve incorporar essa tendência, extrapolando-a linearmente até o horizonte do estudo. Quando não houver tendência significativa, o valor histórico médio de H_cli pode ser mantido nos cenários futuros.

O relatório \"Impactos e Riscos da Mudança do Clima nos Portos Públicos Costeiros Brasileiros\", publicado pela ANTAQ, deve ser consultado para verificar se o complexo portuário analisado possui indicadores de vulnerabilidade climática específicos. Caso existam, esses indicadores devem ser cruzados com os resultados da análise de tendência e reportados como fator de risco na memória de cálculo, mesmo que não alterem diretamente o valor numérico de H_cli projetado.

## 3.5. Quantificação de H_mnt, H_nav e H_out: fontes de dados, procedimentos e diferenciação por tipo de carga

\[Nota técnica\] Recomendação: para terminais que operam granéis higroscópicos (açúcar, grãos, farelo), incluir orientação sobre quantificação de H_cli e H_out. Terminais que operam granéis higroscópicos registram paradas por chuva e umidade relativa elevada que impedem operação de embarque; sem essas categorias explícitas, o modelo pode subestimar o desconto sobre H_cal.

A Eq. 1c decompõe H_ef em cinco termos. O componente H_cli foi tratado na seção anterior (Quadro 12). Os três componentes restantes --- H_mnt, H_nav e H_out --- requerem procedimentos de obtenção distintos conforme o tipo de carga e a configuração do terminal. O Quadro 16 apresenta, para cada componente, a definição operacional, as fontes de dados primárias, a faixa típica de valores e a diferenciação por tipo de carga, incluindo restrições específicas aplicadas a cargas higroscopícas.

**Quadro 16:** Componentes de H_ef: definições, fontes de dados, faixas típicas e diferenciação por tipo de carga

  --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  **Componente**   **Definição**                                                                                                                                                                                               **Fonte de dados**                                                                                                                                                                                                          **Faixa típica (h/ano)**   **Diferenciação por tipo de carga e observações**
  ---------------- ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- -------------------------- --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  H_cal            Horas do calendário anual; base máxima de disponibilidade de um berço.                                                                                                                                      Cálculo direto: 365 × 24 = 8.760 h/ano.                                                                                                                                                                                     8.760                      Não varia por tipo de carga. Ano de 366 dias (bisexto): 8.784 h. Registrar o ano de referência na memória de cálculo.

  H_cli            Horas com operação suspensa por condições meteorológicas ou oceanográficas adversas; quantificado conforme Quadro 12.                                                                                       INMET (estações automáticas); DHN/Centro de Hidrografia da Marinha (ondas); registros operacionais da AP auditados, quando disponíveis.                                                                                     200--800                   Varia significativamente por perfil: Ro-Ro e gránel líquido têm limiares mais restritivos (ver Quadro 12). Em portos abrigados ou lagunares, H_cli pode ser inferior a 100 h/ano.

  H_mnt            Horas de indisponibilidade por manutenção programada e corretiva de equipamentos e infraestrutura portuária.                                                                                                Registro de ordens de serviço do terminal; manuais do fabricante de equipamentos; laudos de inspeção da autoridade portuária; certificados de classificação náutica.                                                        150--500                   Guindastes STS portainer: ciclos de manutenção preventiva totalizam 200--400 h/ano. Shiploader de granel sólido: 150--300 h/ano em operação intensiva. Braço de carregamento de líquidos (mangote/braço de carregamento): inclui manutenção de válvulas e testes de pressurização. Quando o terminal não dispuser de registros auditados, adotar 10% do H_cal disponível como estimativa conservadora.

  H_nav            Horas em que o berço está operacionalmente disponível, mas a entrada ou saída de navio é impossível por restrições náuticas: calado, visibilidade mínima, congestão no canal ou janela diúrna de manobra.   Tábuas de marés DHN; Plano de Manobra aprovado pela Capitania dos Portos; log do VTS (sistema de tráfego de embarcações); registros históricos de pilotagem da autoridade portuária.                                        0--800                     Determinante em portos de barra (estuarinos e lagunares): H_nav pode atingir 600--800 h/ano quando apenas duas janelas diárias de alta maré são viáveis. Em portos abrigados com canal de acesso irrestrito: H_nav ≈ 0. Restrições de visibilidade mínima em canais estreitos afetam todos os perfis de carga igualmente. Janela diúrna de manobra (sem navegação noturna) aplicação: registrar limitação na memória de cálculo.

  H_out            Demais indisponibilidades não enquadráveis nas categorias anteriores: restrições operacionais específicas por tipo de carga, paralisações trabalhistas, manutenção de dragagem, eventos extraordinários.    Registros operacionais auditados da autoridade portuária; relatórios mensais de operação do terminal; dados pluviométricos do INMET (série horária de precipitação); REDEMET para frequência de umidade relativa elevada.   100--400                   Graneis higroscópicos (fertilizantes, açúcar, sal, farelo de soja): operações suspensas com precipitação \> 5 mm/h ou umidade relativa \> 85%; contabilizar as horas em que ao menos um desses limiares foi excedido como H_out, com base na série horária do INMET. Graneis sólidos não higroscópicos (minério de ferro, carvão): operação possível durante chuvas; H_out por precipitação = 0 salvo determinação em contrário da AP. Carga geral sensível (celulose, papel): mesmos critérios de precipitação que graneis higroscópicos.
  --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Fonte: INMET; DHN/Marinha; REDEMET; registros operacionais da autoridade portuária; elaboração própria.

Produtividade real vs. produtividade nominal: o parâmetro P_i da Eq. 1a deve refletir a produtividade efetivamente observada nas operações do terminal, não a produtividade nominal ou de placa do equipamento. A produtividade efetiva é calculada a partir da prancha operacional registrada no Estatístico Aquaviário da ANTAQ (toneladas ou movimentos por hora de operação efetiva T_op), depurada por IQR para exclusão de outliers. O Quadro 2 fornece faixas de referência para validação dos valores obtidos; quando a prancha apurada divergir das faixas, a causa deve ser investigada e documentada na memória de cálculo.

## 3.6. Formulação por produtividade (Eq. 1a)

Quando se dispõe de registros detalhados de produtividade por perfil de carga e por sistema operacional, a formulação recomendada é:

> C_cais = Σᵢ (Pᵢ × H_disp × η_op × BOR_adm) (Eq. 1a)

Onde:

Pᵢ = produtividade operacional do perfil de carga i (t/h ou mov/h) --- prancha média do Estatístico Aquaviário ANTAQ ou faixa do Quadro 2;

H_disp = horas disponíveis no período (h/ano) = 8.760 − H_mnt − H_cli − H_nav − H_out;

η_op = eficiência operacional (adimensional) = razão entre horas produtivas e horas totais de operação, calculada sobre o histórico ANTAQ;

BOR_adm = taxa de ocupação de berço admissível (adimensional) --- Quadro 1, conforme tipo de terminal e número de berços.

Essa formulação relaciona diretamente a produtividade ao tempo disponível e à ocupação operacional, permitindo calibrar cada fator de forma independente. O somatório é realizado por perfil de carga, de modo que a capacidade total do cais corresponde à soma das capacidades parciais de cada grupo de carga operado naquele trecho.

## 3.7. Fatores de perda operacional e formulação expandida da capacidade de cais (Eq. 1a')

\[Nota técnica\] Recomendação: alertar sobre risco de dupla penalização quando os dados-fonte já incorporam perdas operacionais. Os tempos médios publicados pela ANTAQ incluem ineficiências reais (espera por maré, troca de turno, manobra de vagões); aplicar f_d e η_op sobre esses tempos médios desconta a mesma perda duas vezes. Sugestão: exigir declaração explícita de se os tempos-base refletem operação ideal (projeto) ou operação observada.

\[Nota técnica\] Recomendação: incluir fator de interferência entre corredores de exportação que compartilham o mesmo berço ou pátio. Em terminais multiuso, a alternância entre cargas distintas em um mesmo silo ou armazém exige limpeza de linha que pode alcançar várias horas; essa perda não é capturada por f_d nem por η_op, pois decorre do sequenciamento da carteira de navios e não da operação individual.

A Eq. 1a, na forma apresentada, incorpora os parâmetros P_i, H_ef, η_op e BOR_adm. Para garantir a aderência à operação real dos terminais, três fatores de perda operacional devem ser tornados explícitos no modelo: o fator de descontinuidade (f_d), o fator de eficiência operacional (η_op) e o fator de segurança (f_seg). A formulação expandida, denominada Eq. 1a', incorpora obrigatoriamente esses três fatores e o número de unidades de equipamento por berco:

> C_cais = \[Σᵢ (nᵢ × Pᵢ × (1 − f_d) × η_op)\] × H_ef × BOR_adm × f_seg (Eq. 1a')

Onde: nᵢ = número de unidades do equipamento do tipo i no berço (ex.: 2 guindastes STS no mesmo berço); Pᵢ = produtividade real do equipamento i (t/h ou mov/h), obtida do histórico ANTAQ depurado; f_d = fator de descontinuidade; η_op = fator de eficiência operacional; H_ef = horas operacionais efetivas (Eq. 1c); BOR_adm = taxa de ocupação admissível (Quadros 17 e 18); f_seg = fator de segurança. A Eq. 1a' é equivalente à Eq. 1a quando nᵢ = 1, f_d = 0 e f_seg = 1,00.

**Quadro 19:** Fatores de perda operacional: definições, faixas típicas e procedimentos de valoração

  ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  **Fator de perda operacional**    **Símbolo**   **Definição**                                                                                                                                                                                                                                                      **Faixa típica**   **Procedimento de valoração**                                                                                                                                                                                                                                                                                        **Posição na Eq. 1a\'**
  --------------------------------- ------------- ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ ------------------ -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- -----------------------------------------------------------------------------------------------------------------------------
  Fator de descontinuidade          f_d           Fração do H_ef consumida por operações intermediárias entre escalas: manobra de amarras, abertura/fechamento de escotilhas, posicionamento e desposicionamento de equipamentos, troca de turno entre escalas contíguas e colchete de segurança entre atracações.   0,05 -- 0,15       *Apurar como razão T_setup / Ta por escala, onde T_setup é o intervalo entre a conclusão de uma operação e o início efetivo da próxima. Na ausência de registros, adotar f_d = 0,10 como valor-padrão e registrar na memória de cálculo. Na Eq. 1b, o componente a (clearance) captura parcialmente este fator.*     P_i × (1 − f_d): reduz a produtividade efetiva de cada equipamento pelo tempo não produtivo dentro do H_ef.

  Fator de eficiência operacional   η_op          *Proporção do tempo de operação efetiva (T_op) em que o equipamento está gerando throughput, descontadas as paralições breves internas ao turno: reposicionamento de equipamento, aguardo de lote ou caminhoão, ajuste de calado, inspetoria.*                     0,55 -- 0,80       Calcular como razão entre tempo produtivo e T_op total do histórico ANTAQ depurado por IQR (Planilha 2). Faixas por equipamento: ver Quadro 10. Para terminais sem registro de T_op desagregado, estimar η_op por entrevista estruturada com operadores do terminal, validada contra prancha histórica.              P_i × η_op: compõe o par âmetro de produtividade efetiva junto com f_d.

  Fator de segurança                f_seg         Margem de reserva aplicada à capacidade calculada para absorver: (i) incertezas de medição da série histórica; (ii) variabilidade interanual não capturada pelo modelo; (iii) picos de demanda acima da média histórica dentro do horizonte de planejamento.       0,85 -- 0,95       Adotar f_seg = 0,90 como valor-padrão. Reduzir para 0,85 quando: a série histórica tiver menos de 3 anos; ou a variabilidade interanual dothroughput for superior a 15%. Ampliar para 0,95 apenas quando a série for ≥ 10 anos e o CV interanual for inferior a 5%. Registrar justificativa em memória de cálculo.   C_cais_adm = C_cais_calc × f_seg: aplicado à capacidade já calculada pelas Eqs. 1a\' ou 1b antes de comparar com a demanda.
  ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Fonte: elaboração própria; ANTAQ (2023); World Bank Port Reform Toolkit (2007).

## 3.8. Formulação por ciclo de atracação (Eq. 1b)

Quando os dados disponíveis são os tempos operacionais agregados por atracação e o lote médio, a formulação alternativa é:

> C_cais = (b × BOR_adm × H_ef × Lm) / (Ta + a) (Eq. 1b)

Onde:

b = número de berços operacionais (adimensional) --- cadastro da autoridade portuária;

BOR_adm = taxa de ocupação de berço admissível (adimensional) --- Quadro 1, conforme tipo de terminal e número de berços;

Lm = lote médio por atracação (t/atracação ou TEU/atracação) --- Estatístico Aquaviário ANTAQ, por terminal e grupo de carga;

Ta = tempo de permanência do navio no berço (h/atracação) = Inop.Pré + T_op + Inop.Pós --- Estatístico Aquaviário ANTAQ;

a = clearance entre atracacões (h) --- adotado entre 3,0 e 3,5h conforme registros ANTAQ.

As Eqs. 1a e 1b são matematicamente equivalentes; a escolha depende do formato dos dados disponíveis. A Eq. 1a é preferível quando os registros de produtividade permitem desagregar a análise por perfil de carga e sistema operacional. A Eq. 1b é adequada quando os dados disponíveis são os tempos operacionais agregados. O cálculo deve ser realizado separadamente por grupo de carga (granéis sólidos vegetais, granéis sólidos minerais, carga geral, granéis líquidos e contêineres) e por trecho de cais ou terminal.

## 3.9. Decomposição do tempo atracado

O tempo de permanência do navio no berço (Ta) na Eq. 1b deve ser calculado a partir da decomposição em três componentes:

> Ta = Inop.Pré + T_op + Inop.Pós

Onde:

Inop.Pré = tempo inoperante pré-operação (h) --- média depurada por IQR, Passo 1;

T_op = tempo de operação (h) = Lm / P (lote médio dividido pela produtividade média depurada);

Inop.Pós = tempo inoperante pós-operação (h) --- média depurada por IQR.

Todos os parâmetros são calculados por grupo de terminal, berço, tipo de carga, sentido e navegação. A decomposição permite identificar qual componente mais contribui para o tempo de permanência e, portanto, onde há potencial de ganho de produtividade sem investimento em infraestrutura.

## 3.10. Alocação da capacidade por mix de utilização do berço

Quando um mesmo berço opera múltiplos perfis de carga, a capacidade total do berço deve ser distribuída proporcionalmente ao tempo que cada perfil ocupa naquele berço. O procedimento é:

\(1\) Para cada combinação berço--perfil de carga, calcular o tempo total consumido no ano-base: T_total(j) = (Movimentação(j) / Lm(j)) × (Ta(j) + a), onde j identifica o perfil de carga.

\(2\) Calcular o tempo total no berço: T_berço = Σ_j T_total(j).

\(3\) Calcular a fração de ocupação de cada perfil: f(j) = T_total(j) / T_berço.

\(4\) Alocar a capacidade: C(j) = C_berço × f(j), onde C_berço é a capacidade total calculada pela Eq. 1b para aquele berço com BOR_adm do Quadro 1.

Esse procedimento garante que a soma das capacidades alocadas por perfil de carga seja igual à capacidade total do berço. A alocação por mix é a base para a análise de utilização: o BUR observado de cada perfil (Eq. 2b) é calculado como Movimentação(j) / C(j), indicando quais perfis de carga estão mais próximos do limite de capacidade em cada berço.

## 3.11. Indicadores de ocupação: BOR e BUR

\[Nota técnica\] Recomendação: definir procedimento para cálculo do clearance (folga sob quilha + folga lateral) a partir dos timestamps de atracação/desatracação da ANTAQ e dos dados de calado dos navios. O clearance afeta diretamente a acessibilidade do berço e, quando insuficiente, obriga operação com carga parcial ou espera por maré, reduzindo a capacidade real sem que isso apareça nas variáveis atuais do modelo.

Definições: a Taxa de Utilização dos Berços (TUB), também referida como Berth Occupancy Rate (BOR) na literatura internacional, é a fração do tempo total disponível em que o berço está fisicamente ocupado por uma embarcação. O Índice de Utilização dos Berços (BUR) mede a fração da capacidade de movimentação efetivamente realizada em relação à capacidade calculada. Ambos os indicadores são adimensionais e expressos em percentual. Os valores admissíveis por tipo de terminal são os do Quadro 1.

A Taxa de Ocupação do Berço (BOR, Berth Occupancy Rate), também denominada Taxa de Utilização dos Berços (TUB), mede a fração do tempo total disponível efetivamente ocupada por operações com navio no berço:

> BOR = (Σ Ta) / (b × 8.760) × 100 (%) (Eq. 2a)

O somatório de Ta abrange todas as atracacões no período, excluindo o clearance a do numerador (Convenção A da ANTAQ). Os limites operacionais recomendados são indicados no Quadro 1. Valores de BOR acima do limiar admissível sinalizam formação sustentada de fila de navios aguardando berço, com aumento desproporcional do tempo médio de espera no line-up. Quando o BOR supera 100%, o trecho opera acima do equilíbrio da teoria das filas (M/M/n), configurando gargalo de nível de serviço.

A Taxa de Utilização do Berço (BUR, Berth Utilization Ratio) complementa o BOR ao medir a relação entre a movimentação efetivamente realizada e a capacidade teórica calculada:

> BUR = Movimentação_realizada / C_cais × 100 (%) (Eq. 2b)

A distinção entre BOR e BUR é operacionalmente relevante. O BOR mede ocupação temporal: um berço pode estar fisicamente ocupado por um navio sem que a operação de carga esteja em curso (por paralisações, condições climáticas, atrasos de liberação). O BUR mede a utilização efetiva da capacidade de throughput. Um berço com BOR de 60% (ocupação temporal moderada) pode apresentar BUR de 90% (utilização da capacidade próxima do limite) caso a produtividade efetiva esteja abaixo da nominal. O diagnóstico de capacidade deve reportar ambos os indicadores, distinguindo entre a capacidade observada (o capacidade observadacapacidade observada registrado no ano-base) e a capacidade atingível (o capacidade atingívelcapacidade atingível máximo que o cais pode alcançar operando nos limites de BOR e produtividade de referência). A diferença entre ambas indica o potencial de ganho de capacidade por melhorias operacionais, sem necessidade de novos investimentos em infraestrutura.

**Quadro 1:** Taxas de ocupação de berço (BOR) admissíveis por tipo de terminal

  -----------------------------------------------------------------------------------------------
  **Tipo de terminal**         **N.º de berços**   **BOR recomendado**   **Regime operacional**
  ---------------------------- ------------------- --------------------- ------------------------
  Especializado, carga única   1                   50--65%               Contínuo (24/7)

  Especializado, carga única   2                   55--70%               Contínuo (24/7)

  Multipropósito               3                   60--75%               Contínuo (24/7)

  Multipropósito               4+                  65--80%               Contínuo (24/7)

  Contêineres (ded.)           2--3                60--70%               Contínuo (24/7)

  Graneis líquidos             1--2                50--65%               Contínuo ou turnos
  -----------------------------------------------------------------------------------------------

Fonte: UNCTAD (1985); PIANC (2014).

Os limites crescentes de BOR refletem o efeito de pooling de fila: à medida que o número de berços aumenta, a variabilidade relativa dos tempos de espera diminui, permitindo operar com maior taxa de ocupação sem degradação proporcional do nível de serviço (UNCTAD, 1985). Para terminais especializados com operação de um único tipo de carga e um berço, a variabilidade intrínseca é máxima e o índice conservador de 50--65% é o recomendado; para cais de multipropósito com quatro ou mais berços e diversidade de cargas, o limite de 65--80% é operacionalmente sustentável.

**Quadro 2:** Produtividade operacional de referência por tipo de carga e sistema

  ----------------------------------------------------------------------------------------------------
  **Tipo de carga**          **Sistema operacional**               **Faixa típica**   **Unidade**
  -------------------------- ------------------------------------- ------------------ ----------------
  Granéis sólidos vegetais   Mecanizado (shiploaders, esteiras)    800--2.000         t/h

  Granéis sólidos vegetais   Semimecanizado (moegas, grab)         200--500           t/h

  Granéis sólidos minerais   Mecanizado (esteiras, shiploaders)    1.000--3.000       t/h

  Granéis líquidos           Bombeamento (dutos)                   300--1.000         t/h

  Carga geral                Convencional (guindaste de bordo)     30--80             t/h

  Carga geral                Semimecanizado (guindaste de terra)   60--150            t/h

  Contêineres                Portêineres (STS crane)               20--35             moves/h

  Contêineres                Mobile Harbour Crane (MHC)            12--20             moves/h
  ----------------------------------------------------------------------------------------------------

Fonte: ANTAQ; benchmarks internacionais (UNCTAD, 1985; World Bank, 2007).

O Quadro 2 fornece faixas de produtividade típica por tipo de carga e configuração operacional. Esses valores servem como parâmetro de entrada para a Eq. 1a (Pᵢ) e como referência de validação: quando a prancha média registrada no Estatístico Aquaviário da ANTAQ divergir das faixas típicas, a causa deve ser investigada (equipamento obsoleto, regime de turnos reduzido, mix de cargas com diferentes graus de mecanização). A produtividade efetiva de cada terminal deve ser calibrada com dados históricos do próprio porto; as faixas do quadro não substituem a calibração local, mas orientam a verificação de consistência.

Fonte dos dados de entrada: todos os parâmetros das Eqs. 1a e 1b são obtidos do Estatístico Aquaviário da ANTAQ (lote médio, prancha operacional, tempos de permanência), complementados pelo cadastro de berços da autoridade portuária (número de berços, dimensões), pelos quadros de BOR (Quadro 1) e de produtividade (Quadro 2). Quando a autoridade portuária já disponibiliza o BOR calculado em seus sistemas gerenciais com base em série histórica auditada e consistente com os registros da ANTAQ, esse indicador pode ser adotado diretamente.

**Quadro 6:** Parâmetros das Eqs. 1a e 1b: definições, unidades, fontes e procedimentos de obtenção

  ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  **Parâmetro**   **Definição**                                                              **Unidade**    **Fonte primária**             **Procedimento de obtenção**
  --------------- -------------------------------------------------------------------------- -------------- ------------------------------ ----------------------------------------------------------------------------------------------------------------------
  b               Número de berços operacionais para o perfil de carga j                     ---            Cadastro de berços da AP       Levantamento direto; conferência com o campo "Berço" do Estatístico ANTAQ

  BOR_adm         Taxa de ocupação admissível                                                adimensional   Quadro 1 do roteiro            Seleção por tipo de terminal e n.º de berços; valores de referência consolidados no Quadro 1

  Lm              Lote médio por atracação (carga movimentada por escala)                    t ou TEU       Estatístico Aquaviário ANTAQ   Média por grupo após exclusão de replicatas e filtragem por IQR (Planilha 2)

  Ta              Tempo médio de permanência por atracação (berth time)                      h              Estatístico Aquaviário ANTAQ   Inop.Pré + T_op + Inop.Pós; depurado por IQR (Planilha 2); decomposto por período para identificação de sazonalidade

  a               Clearance: intervalo mínimo entre atracacões consecutivas no mesmo berço   h              Estatístico Aquaviário ANTAQ   Diferença entre chegadas consecutivas; padrão de referência: 3,0 h quando o dado não estiver disponível
  ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Fonte: elaboração própria.

## 3.12. Taxas de ocupação admissíveis: referências UNCTAD e PIANC por perfil de carga e configuração operacional

\[Nota técnica\] Recomendação: adaptar o conceito de BOR_adm para terminais que operam com berth windows (janelas de atracação pré-alocadas). Nesse regime, a fila livre (FIFO) pressuposta pelo modelo de Erlang-C não se aplica; a capacidade é limitada pelo número de slots disponíveis e pelo cumprimento do agendamento. Sugestão: incluir variante de BOR_adm baseada em taxa de utilização de slots.

O Quadro 1 apresenta os limites genéricos de BOR_adm. Para estudos de capacidade que fundamentam investimentos em infraestrutura portuária, esses limites devem ser substituídos pelos valores do Quadro 17, que diferencia o BOR_adm por perfil de carga e número de berços com base nas recomendações da UNCTAD (1985) e da PIANC. A racionale subjacente é o efeito de pooling de fila (teoria M/M/n de Erlang-C): para um dado nível de serviço-alvo (tempo médio de espera aceitável), o BOR_adm admissível aumenta com o número de berços porque a variabilidade relativa da demanda diminui. A tabela também diferencia o BOR_adm por perfil de carga, pois terminais de contêiner apresentam maior variabilidade de tempo de serviço que terminais de granel sólido, exigindo maiores margens de segurança operacional.

**Quadro 17:** BOR_adm de referência por perfil de carga e número de berços (UNCTAD e PIANC)

  ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  **Perfil de carga**   **N.º berços**   **BOR_adm --- UNCTAD (1985)**   **BOR_adm --- PIANC**   **Observações metodológicas**
  --------------------- ---------------- ------------------------------- ----------------------- -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  Granel sólido         1                ≤ 0,50                          ≤ 0,55                  Alta variabilidade de chegadas (navios Capesize e Handymax com intervalos irregulares) justifica limite conservador para berço único. Terminais com sazonalidade agrícola acentuada: aplicar limite inferior em período de pico de safra.

  Granel sólido         2--3             ≤ 0,65                          ≤ 0,70                  Efeito de pooling reduz variabilidade relativa da fila; UNCTAD (1985, p. 77) admite até 0,65 para 2 berços especializados. Quando H_cli for superior a 500 h/ano, recalcular BOR_adm via Erlang-C com H_ef reduzido.

  Granel líquido        1--2             ≤ 0,55                          ≤ 0,60                  Operação de dutos apresenta menor variabilidade no tempo de serviço, o que permitiria limite maior; contudo, o risco de incidentes ambientais em manobras de transbordo recomenda margem operacional. Terminais com operação mista (dutos + mangotes) devem adotar o limite mais conservador.

  Contêiner             1                ≤ 0,50                          ≤ 0,55                  Limite mais restritivo por razão da alta variabilidade do tempo de serviço por STS e da sensibilidade do custo de escala ao tempo de espera. BOR acima de 0,55 em berço único implica tempo médio de espera superior a 0,5 escala (M/M/1).

  Contêiner             2--3             ≤ 0,65                          ≤ 0,70                  PIANC (Report n.º 158, WG Ports) recomenda BOR_adm ≤ 0,65 para terminal dedicado de contêiner com 2 berços. Para ULCSs (navios Ultra Large Container), adotar limite inferior (0,60) em razão do impacto disproporcionalmente alto de atrasos sobre custos da escala.

  Contêiner             ≥ 4              ≤ 0,70                          ≤ 0,75                  Efeito de pooling mais pronunciado; aplicação de filas M/M/n com n ≥ 4. Adotar limite inferior quando houver berço dedicado a ULCS, pois a variância do serviço desse berço afeta a fila global.

  *Carga geral*         1                ≤ 0,45                          ≤ 0,50                  Maior heterogeneidade de cargas e navios implica alta variabilidade de tempo de serviço. Terminais com regime de turnos diúrnos (16 h/dia): H_ef já reduzido; BOR calculado sobre H_ef, não H_cal --- registrar convenção adotada.

  *Carga geral*         2+               ≤ 0,60                          ≤ 0,65                  Pooling reduz variabilidade relativa. Quando o mix incluir produtos higroscópicos (papel, algodão, farinha), adicionar H_out ao cálculo de H_ef antes de aplicar o limite de BOR_adm.

  Ro-Ro/Automotivo      1+               ≤ 0,55                          ≤ 0,60                  Operação de rampa de popa com alta sensibilidade a atrasos de navios e restrições climáticas mais restritivas (vento \> 10 m/s, Hs \> 0,5 m). H_cli mais elevado reduz H_ef e eleva o BOR aparente; BOR_adm calculado sobre H_ef corrigido. Adotar Erlang-C para configurações com 2+ berços.
  ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Fonte: UNCTAD (1985, p. 70--77); PIANC Report n.º 121 (2014); PIANC WG Ports; elaboração própria.

Para qualquer configuração não coberta pelo Quadro 17, BOR_adm deve ser calculado explicitamente pela fórmula de Erlang-C (M/M/n), informando: taxa de chegada de navios (λ, navios/h), tempo médio de serviço (1/μ, h/navio), número de berços (n) e nível de serviço-alvo (tempo de espera aceitável). O resultado do cálculo de BOR_adm deve ser registrado na memória de cálculo com os parâmetros utilizados. Adotar os valores do Quadro 17 sem recalibração local somente quando os dados de chegada de navios do terminal forem insuficientes para estimar λ e 1/μ com confiabilidade.

**3.13. Modelos de teoria das filas: distribuições de chegada e atendimento por perfil de terminal**

A determinação de BOR_adm não pode se restringir a tabelas de benchmarks. O ponto de partida metodológico é a teoria das filas (queueing theory), que relaciona a taxa de ocupação do berço (ρ = BOR) ao nível de serviço atingido --- medido pela probabilidade de espera de navio ou pelo tempo médio de espera em fila. A escolha do modelo (M/M/c, M/Ek/c ou M/D/c) depende das distribuições empíricas de chegadas e de tempo de serviço (Ta), que variam por perfil de terminal. O Quadro 18 apresenta o modelo recomendado, os procedimentos de estimação dos parâmetros λ e μ e a articulação com os benchmarks do Quadro 17 para cada perfil.

\[Nota técnica\] Recomendação: exigir teste de aderência (qui-quadrado ou Kolmogorov-Smirnov) antes de aplicar Erlang-C. O modelo assume chegadas Poisson e tempo de serviço exponencial ou determinístico; se a distribuição empírica não se ajustar a essas premissas (ex.: chegadas em comboio em terminais de granéis), os resultados de P(W \> 0) e do fator de espera ficam enviesados. Caso a aderência seja rejeitada, indicar simulação de eventos discretos como alternativa.

**Quadro 18:** Modelos de teoria das filas por perfil de terminal: distribuições, parâmetros e articulação com benchmarks UNCTAD/PIANC

  ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  **Perfil de terminal**                  **Modelo de fila recomendado e distribuições**                                                                                                                                                                                                                       **Estimação dos parâmetros λ e μ**                                                                                                                                                                                                                                                                  **Articulação com BOR_adm (UNCTAD/PIANC) e nível de serviço**
  --------------------------------------- -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  Multipropósito / carga geral            M/M/c (Markoviano): chegadas Poisson (λ estável); serviço exponencial (M); CV²(Ta) ≈ 1. Aplica-se quando o perfil de navio e a carga variam significativamente entre escalas, gerando alta variabilidade no tempo de serviço.                                        λ = frequência média de escalas (navios/dia), obtida do histórico ANTAQ com filtro por trecho de cais. μ = 1 / E\[Ta\], onde E\[Ta\] é o tempo médio de permanência por escala. ρ = λ / (c × μ) = BOR observado. Usar ρ como insumo para Erlang-C.                                                  *BOR_adm alvo: ver Quadro 17 (carga geral, 1 berço: ≤ 0,45; 2+: ≤ 0,60). Critério de nível de serviço: P(W \> 0) ≤ 20% (probabilidade de espera de navio). Se ρ calculado \> BOR_adm do Quadro 17: sinalizar saturação e quantificar déficit de capacidade.*

  Contêiner (múltiplas armadoras)         M/G/c ou M/Ek/c: chegadas Poisson; distribuição de serviço mais regular que carga geral. Quando CV²(Ta) \< 1 (operações STS com menor variabilidade), usar M/Ek/c (Erlang-k no serviço), onde k = 1 / CV²(Ta). Erlang-C é o caso particular k = 1.                   k = 1 / CV²(Ta): calcular do histórico de Ta por perfil de carga. Para k ≥ 2: menor probabilidade de espera que M/M/c para o mesmo ρ, permitindo BOR_adm levemente maior. Estimar λ por armadora e agregar. Verificar se intervalos de chegada seguem distribuição exponencial (teste K-S ou AD).   *BOR_adm: Quadro 17 (contêiner, 2--3 berços: ≤ 0,65 UNCTAD; ≤ 0,70 PIANC). Nível de serviço-alvo: P(W \> 0) ≤ 15% ou tempo médio de espera ≤ 0,5 × E\[Ta\]. Para ULCSs, adotar critério mais restritivo (≤ 10%) dado o custo desproporcional de atraso de navio de grande porte.*

  Granel sólido (sazonalidade agrícola)   M/Ek/c (k ≥ 2): chegadas Poisson com ajuste sazonal; serviço Erlang com menor variabilidade que M/M/c. Em período de safra: λ aumenta e a distribuição de chegadas pode se afastar de Poisson; avaliar ajuste por distribuição gamma ou log-normal para pico.        Dividir a série histórica em período de safra e entressafra. Estimar λ_safra e λ_entressafra separadamente. Calcular BOR_adm para cada período. A capacidade crítica é determinada pelo período de pico. Verificar CV²(Ta) para calibrar k.                                                         *BOR_adm: Quadro 17 (granel sólido, 1 berço: ≤ 0,50 UNCTAD; ≤ 0,55 PIANC). O critério UNCTAD serve como validação: se ρ_safra \> 0,50 para 1 berço, o diagnóstico deve identificar o período como gargalo sazonal.*

  Granel líquido (bombeamento)            M/D/c ou M/Ek/c com k alto (≥ 5): serviço quase-determinístico. A vazão de bombeamento é próxima de constante para uma mesma classe de produto, resultando em CV²(Ta) tipicamente \< 0,20. M/D/c representa o caso-limite de serviço determinístico.                 E\[Ta\] = Lm / (vazão média de bombeamento); CV²(Ta) estimado do histórico ANTAQ; k = 1 / CV²(Ta). Para M/D/c, μ = 1 / E\[Ta\] com variabilidade zero. A baixa variabilidade de serviço reduz o tempo médio de espera para o mesmo ρ.                                                               *Apesar da menor variabilidade, o Quadro 17 recomenda BOR_adm conservador (≤ 0,55--0,60) por razões de segurança operacional e ambiental. O analista pode justificar BOR_adm superior com cálculo explícito de P(W \> 0) via M/D/c e registro em memória de cálculo.*

  Ro-Ro / Automotivo                      M/M/c ou M/Ek/c: chegadas com menor aleatoriedade (escalas parcialmente programadas); avaliar se distribuição de chegadas se ajusta melhor a Erlang-k que a Poisson. Alta variabilidade de tempo de serviço (número de veículos e sequência de embarque variados).   Quando a escala do navio for programada com mais de 48 h de antecedência, λ pode ser estimado diretamente da agenda de navios (port log) em vez do método histórico ANTAQ. Isso reduz a incerteza de λ e permite BOR_adm levemente superior com o mesmo nível de serviço.                           *BOR_adm: Quadro 17 (≤ 0,55 UNCTAD; ≤ 0,60 PIANC). O cálculo de BOR deve ser feito sobre H_ef já corrigido pelo H_cli mais restritivo (vento \> 10 m/s, Hs \> 0,5 m); usar H_ef real e não H_cal no denominador do BOR.*
  ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Fonte: UNCTAD (1985); Groenveld (2005); Baird (2004); elaboração própria.

O procedimento operacional para aplicação da teoria das filas compreende três etapas. Primeiro, estimar λ e μ a partir do histórico depurado de escalas (Planilha 1) e verificar a aderência das distribuições empíricas aos modelos teóricos (teste Kolmogorov-Smirnov ou Anderson-Darling). Segundo, calcular BOR_adm como o valor máximo de ρ que satisfaz o nível de serviço-alvo (P(W \> 0) ≤ 20% para terminais multipropósito; ≤ 15% para contêineres). Terceiro, confrontar o BOR_adm calculado com o intervalo de referência do Quadro 17: se houver convergência, adotar o valor calculado; se houver divergência superior a 5 pontos percentuais, investigar a causa (sazonalidade, mistura de distribuições, outliers) e registrar o tratamento adotado na memória de cálculo. Os Granel líquido (bombeamento)

Os valores de referência do Quadro 17 são valores de validação, não substitutos do cálculo explícito.

## 3.14. Fatores de eficiência operacional: fundamentação teórica e valoração

Os fatores de eficiência que aparecem nas fórmulas deste roteiro (BOR_adm, η, f_s, η_s, η_d) têm fundamentação em referenciais técnicos consolidados. Sua correta valoração condiciona a qualidade do diagnóstico: valores subestimados superestimam a capacidade disponível; valores superestimados a subestimam. O Quadro 10 sistematiza cada fator, seu referencial teórico principal e os intervalos de referência recomendados.

**Quadro 10:** Fatores de eficiência operacional: definição, base teórica e intervalos de referência

  ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  **Fator**   **Definição**                                                                                                                   **Referencial teórico**                                              **Intervalo de referência**                                                        **Fonte de valoração local**
  ----------- ------------------------------------------------------------------------------------------------------------------------------- -------------------------------------------------------------------- ---------------------------------------------------------------------------------- --------------------------------------------------------------------------------------------------------------------------------------------
  BOR_adm     Taxa de ocupação admissível dos berços: fração de H_ef efetivamente utilizada em operações de carga                             UNCTAD (1985, cap. 4); PIANC (2014, Report 121); World Bank (2007)   0,40--0,65 conforme n.º de berços e tipo de terminal (Quadro 1)                    *Seleção no Quadro 1; ajuste para terminais com sistema de janelas de atracação (berth windows)*

  η           Eficiência de prancha: razão entre produtividade efetiva medida e capacidade nominal declarada do equipamento                   World Bank (2007); Drewry Port Benchmark Survey (edições anuais)     0,65--0,90 conforme tipo de equipamento e maturidade operacional do terminal       Cálculo direto no Estatístico ANTAQ: prancha média (Lm/T_op) dividida pela capacidade nominal; valores \< 0,65 requerem investigação

  f_s         Fator de ocupação do piso: razão entre área efetivamente ocupada pela carga e área útil do armazém ou pátio                     UNCTAD (1985); PIANC; prática setorial                               0,70--0,85 para pátios de contêineres; 0,80--0,90 para silos e armazéns cobertos   Dado operacional do arrendatário; validar com histórico de pico de ocupação registrado em sistema TOS ou relatórios mensais

  η_s         Eficiência do sistema de armazenagem: fracção da capacidade estática efetivamente aproveitável após descontáveis operacionais   UNCTAD (1985); literatura de planejamento de terminais portários     0,85--0,95 para a maioria dos terminais                                            *Estimativa do operador; calibrar por confronto entre CE calculada e throughput histórico: η_s calibrado = throughput_obs / (CE × DOA/DT)*

  η_d         Eficiência do ciclo dinâmico: fator de ajuste para perdas no ciclo de entrada e saída de cargas do sistema de armazenagem       UNCTAD (1985); prática setorial                                      0,90--0,95                                                                         Estimativa do operador; validar por confronto entre CD calculada e η_d histórico observado na série anual
  ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Fonte: UNCTAD (1985); PIANC (2014); World Bank (2007); elaboração própria.

O BOR_adm é o fator com maior impacto sobre o resultado da Eq. 1b. Sua valoracão por tipo de terminal e número de berços deriva da teoria de filas (modelo Erlang-C para chegadas de Poisson) e é adotada internacionalmente em planos mestres portuários desde a publicação do manual da UNCTAD (1985). A lógica subjacente é que berços com alta taxa de ocupação geram filas de espera longas, deteriorando o nível de serviço; o BOR_adm é o ponto de equilíbrio entre utilização e aceitação da fila. Portos com sistema de janelas de atracação (berth windows) podem operar com BOR_adm ligeiramente superior ao Quadro 1, pois o agendamento reduz a variância das chegadas. A eficiência de prancha (η) deve ser calculada diretamente no Estatístico ANTAQ como a razão entre a prancha média observada e a capacidade nominal declarada pelo operador; valores inferiores a 0,65 indicam ineficiência operacional estrutural e requerem investigacão e calibracão cuidadosa antes de adotar como parâmetro de capacidade.

## 3.15. Diagnóstico de capacidade do cais

O diagnóstico de capacidade do cais é elaborado ao final do Passo 2, depois de calculados C_cais (Eq. 1a ou 1b), BOR observado, BOR admissível e BUR. A sequência é: (1) definição e coleta de dados, (2) cálculo das equações, (3) apuração dos indicadores de ocupação, e (4) diagnóstico. O diagnóstico deve reportar: se BOR obs. \> BOR adm., o cais já opera acima do limite de serviço no ano de referência; se BUR \> 90%, a folga de produtividade é marginal. O diagnóstico deve ser registrado no Quadro 5 (quadro-síntese).

## 3.16. Aplicação das fórmulas e parâmetros por perfil de carga

\[Nota técnica\] Recomendação: harmonizar as faixas de produtividade do Quadro 15 (aplicação das fórmulas) com as do Quadro 2 (parâmetros operacionais). Para carga geral conteinerizada, o Quadro 2 admite 20-35 mov/h enquanto o Quadro 15 pode usar faixas distintas. Divergências entre quadros geram ambiguidade na escolha do valor de entrada.

O Quadro 15 organiza, por perfil de carga, a equação recomendada, os parâmetros críticos com suas unidades de medida, a faixa de produtividade de referência e as observações metodológicas específicas. A tabela constitui referência rápida para o analista ao iniciar o cálculo de cada trecho de cais, direcionando a escolha entre Eq. 1a e Eq. 1b e os valores-guia para validação dos parâmetros levantados em campo.

**Quadro 15:** Aplicação das fórmulas e parâmetros por perfil de carga

  ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  **Perfil de carga**                          **Equação aplicável**       **Parâmetros críticos (símbolo e unidade)**                                              **Produtividade típica**                                       **Observações metodológicas**
  -------------------------------------------- --------------------------- ---------------------------------------------------------------------------------------- -------------------------------------------------------------- ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  Contêiner (guindaste STS/portainer)          Eq. 1a (preferencial)       P_i: 20--35 mov/h por guindaste; η_op: 0,60--0,75; BOR_adm: ≤ 0,70; H_ef (h/ano)         20--35 mov/h por guindaste                                     Aplicar fator TEU (1,40--1,65 TEU/caixa); número de guindastes por berço eleva C_cais proporcionalmente; BOR_adm obtido via Erlang-C.

  Granel sólido (shiploader/grab/pneumático)   Eq. 1a ou 1b                P_i: 500--4.000 t/h (Eq. 1a); Lm (t/escala) e Ta (h/escala) (Eq. 1b); η_op: 0,65--0,80   500--4.000 t/h                                                 Eq. 1b preferível quando série histórica ANTAQ está disponível e depurada. Graneis agrícolas podem ter H_cli adicional por umidade relativa (\> 85% para farelo).

  Granel líquido (dutos/mangotes)              Eq. 1b                      Lm (t/escala); Ta (h/escala); a: tempo de manobra (h)                                    Determinada pela vazão das bombas                              H_cli inclui Hs \> 0,8 m e vento \> 15 m/s. Contratos com armadores podem fixar limiares mais restritivos; registrar critério adotado na memória de cálculo.

  Carga geral (guindaste móvel)                Eq. 1a ou 1b conforme mix   P_i: 100--500 t/h; η_op: 0,55--0,70; Lm (t/escala) quando histórico disponível           100--500 t/h                                                   Alta variabilidade por tipo de embalagem. Quando o mix for heterogêneo, segmentar por subperfil (carga paletizada, bobinas, graneis embalados) ou usar Eq. 1b com Lm histórico agregado.

  Ro-Ro/Automotivo (rampa de popa)             Eq. 1b                      Lm (CEU/escala ou un/escala); Ta (h/escala); a: tempo de manobra (h)                     Determinada pela capacidade da rampa e sequência de embarque   Fator CEU: 1 (automóvel) a 3 (caminhão). H_cli mais restritivo (vento \> 10 m/s, Hs \> 0,5 m). Registrar sequência de embarque como condicionante de Ta.
  ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Fonte: elaboração própria; ANTAQ (2023); UNCTAD (1985); World Bank (2007).

# 4. Passo 3: Ajuste para operações especiais: cruzeiros

Este passo aplica-se exclusivamente quando o porto opera navios de cruzeiro nos mesmos berços de carga. As horas disponíveis do trecho devem ser reduzidas pelo período de ocupação anual por cruzeiros antes de aplicar as Eqs. 1a ou 1b:

> H_aj = H_total − H_cruzeiros (Eq. 3)

onde H_cruzeiros é estimado a partir de três variáveis: (a) o número anual de escalas de cruzeiro; (b) o comprimento de atracação (Length Overall, LOA) de cada navio, que determina quantos berços adjacentes ficam bloqueados simultaneamente; e (c) a duração média de permanência por escala.

Fontes: o número de escalas e os LOA das embarcacões são obtidos dos registros da ANTAQ e da Associação Brasileira de Terminais de Cruzeiros Marítimos (Brasil Cruise), que publica relatórios anuais por temporada. Navios de grande porte (LOA acima de 300 m) podem bloquear dois ou mais berços adjacentes, multiplicando as horas indisponíveis. A temporada de cruzeiros no Brasil vai de novembro a abril. Quando os berços de cruzeiro são fisicamente separados dos berços de carga, a Eq. 3 não deve ser aplicada.

# 5. Passo 4: Cálculo da capacidade de armazenagem estática

Capacidade de armazenagem é a quantidade máxima de carga que o sistema de instalações de guarda transitória do terminal pode reter simultaneamente, expressa em toneladas (t) para granéis sólidos, carga geral e granéis líquidos, exceto quando o produto seja cotado em volume, caso em que se usa m³, e em TEU para contêineres. A distinção entre capacidade estática e dinâmica é necessária porque a mesma instalação pode reter uma quantidade de carga (capacidade estática, em t ou TEU no instante t) mas movimentar um volume maior ao longo do ano, conforme a velocidade de rotação do estoque (capacidade dinâmica, em t/ano ou TEU/ano).

## 5.1. Procedimento de mapeamento e quantificação das instalações

Antes de aplicar as equações, o analista deve mapear e quantificar individualmente cada instalação de armazenagem do terminal. O procedimento compreende quatro etapas: (1) levantamento junto à Autoridade Portuária dos contratos de arrendamento, do Plano de Desenvolvimento e Zoneamento (PDZ) e dos relatórios anuais de utilização; (2) classificação por tipologia (silo, armazém fechado, armazém aberto, tanque, pátio descoberto, pátio de contêineres) e por perfil de carga atendido (granel sólido vegetal, granel sólido mineral, granel líquido, carga geral, contêineres); (3) registro da capacidade nominal declarada pelo operador ou pela AP, com indicação da data-base e da fonte; e (4) cálculo ou validação da capacidade efetiva pela Eq. 4, confrontando o resultado com a capacidade nominal declarada. Discrepancias superiores a 10% devem ser investigadas e documentadas na memória de cálculo. Todos os dados levantados devem ser registrados em planilha-base, referenciada na Planilha 3 do Passo 11.

A capacidade de armazenagem estática corresponde ao volume máximo de carga que pode ser mantido simultaneamente nas instalações do porto. O cálculo deve ser realizado por instalação e por tipo de carga (granéis sólidos, granéis líquidos, carga geral, contêineres), distinguindo armazenagem primária e retroárea.

## 5.2. Diferenciação dos métodos de cálculo por perfil de carga

A Eq. 4 se aplica a todos os perfis de carga, mas os parâmetros A_útil, ρ, f_s e η_s assumem significados e fontes distintos conforme o tipo de instalação. O Quadro 20 sistematiza a formulação específica por perfil, os parâmetros críticos de calibração e a unidade de resultado. Para contêineres, a formulação baseia-se no número de ground slots (N_GS) e nos fatores de pátio detalhados no Quadro 21.

**Quadro 20:** Métodos de cálculo da capacidade estática por perfil de carga

  ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  **Perfil de carga**   **Formulação específica**                                                        **Parâmetros-chave**                                                                                                                                                     **Unidade**   **Observação metodológica**
  --------------------- -------------------------------------------------------------------------------- ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ ------------- --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  Granel sólido         CE = V_silo × ρ_prod × η_s (silo) ou CE = A_útil × ρ_pátio × f_s × η_s (pátio)   V_silo em m³ interno; ρ_prod: soja 0,72--0,76 t/m³; milho 0,70--0,74; farelo 0,58--0,62; fertilizante 0,85--1,10 t/m³; η_s: 0,85--0,95 (silo), 0,70--0,82 (pátio)        t             Silos: f_s não se aplica, pois o volume interno já é tridimensional. Pátios descobertos: f_s representa a altura de empilhamento (3--8 m, conforme o ângulo de repouso do produto). Segregar por produto para evitar contaminação cruzada entre lotes.

  Granel líquido        CE = V_tq × ρ_p × η_tq                                                           V_tq em m³ útil por tanque; ρ_p: óleo vegetal ≈ 0,85 t/m³; petróleo cru 0,82--0,88 t/m³; combustíveis 0,73--0,84 t/m³; GLP ≈ 0,73 t/m³ (ANTAQ, 2021); η_tq: 0,90--0,95   t             CE por tanque, segregada por produto. Tanques destinados a produtos incompatíveis não somam capacidade. Capacidade nominal (m³) publicada pela ANTAQ pode ser adotada diretamente, desde que auditada.

  Contêiner             CE = N_GS × f_s × f_util × (1 − f_seg)                                           N_GS: número de ground slots; f_s: RTG 4--6, reach stacker 3--5, SC 2--3; f_util: 0,75--0,85; f_seg: 0,10--0,20. Ver Quadro 21.                                          TEU           TGS = N_GS / A_bruta (TEU/m²) é o indicador-síntese da densidade de pátio. Converter para t pelo fator de carga médio (14--22 t/TEU, conforme tara e carga por TEU).

  Carga geral           CE = A_útil × ρ × f_s × η_s                                                      ρ: 0,4--1,2 t/m² conforme embalagem; f_s: 1--3 camadas; η_s: 0,60--0,80                                                                                                  t             Segmentar por tipo de embalagem (paletes, big bags, bobinas) e por requisito especial (frigorificado, IMO). Corredores de empilhadeiras reduzem η_s em relação a instalações de granéis.

  Ro-Ro e automotivo    CE = A_útil / A_vaga × η_s                                                       A_vaga: 16--22 m² por veículo de passeio; 30--45 m² para caminhões e máquinas; η_s: 0,55--0,70                                                                           unid.         Converter para t pelo peso médio por categoria de veículo. Pátio Ro-Ro opera com f_s = 1 (monocamada). A_vaga inclui corredor de circulação e área de manobra.
  ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Fonte: ANTAQ (2020b; 2021); UNCTAD (1985); World Bank (2007).

## 5.3. Parâmetros operacionais de pátio para contêineres: TGS, altura de empilhamento e fatores de utilização

Pátios de contêineres exigem tratamento específico por combinar a densidade de solo (ground slots), a capacidade de empilhamento e as restrições de segregação operacional. O parâmetro TGS (densidade de ground slots, em TEU/m²) sintetiza a relação entre o número de posições no solo e a área bruta do pátio, e constitui o ponto de partida para o cálculo de CE em TEU. O Quadro 21 relaciona os parâmetros de pátio com as faixas típicas por tipo de equipamento de movimentação.

**Quadro 21:** Parâmetros operacionais de pátio de contêineres: TGS, altura de empilhamento e fatores de utilização e segregação

  ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  **Parâmetro**               **Símbolo**   **Faixa típica**                                                             **Fator de influência**                                                                                                                                                   **Procedimento de estimativa**
  --------------------------- ------------- ---------------------------------------------------------------------------- ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  Densidade de ground slots   TGS           0,04--0,07 TEU/m²                                                            Equipamento: RTG: 0,05--0,07; reach stacker: 0,04--0,05; straddle carrier: 0,03--0,05                                                                                     Dividir o número total de ground slots (N_GS) pela área bruta do pátio. N_GS é o número de posições de contêiner no solo, independente da altura de empilhamento.

  Altura de empilhamento      f_s           RTG: 4--6; reach stacker: 3--5; straddle carrier: 3--4; empilhadeira: 2--3   Tipo de equipamento; resistência estrutural do piso; proporção de contêineres reefer (limita o empilhamento máximo por necessidade de acesso à tomada de energia)         Adotar o valor típico por tipo de equipamento ou a informação operacional do terminal. Para pátios com blocos de tipos distintos, calcular média ponderada por área de bloco.

  Fator de utilização         f_util        0,75--0,85                                                                   Eficiência do TOS; nível de automação; composição do fluxo entre importação e exportação                                                                                  Razão entre o número médio de TEU ocupados e a capacidade nominal do pátio (N_GS × f_s). Calibrar com histórico do TOS. Adotar 0,80 na ausência de dados operacionais.

  Fator de segregação         f_seg         0,10--0,20                                                                   Número de armadoras; proporção de reefer (segregação obrigatória por tomada de energia); contêineres OOG e IMO; sentido do fluxo (importação, exportação, transhipment)   Razão entre slots indisponíveis por segregação e total de slots. Terminais com reefer acima de 15% do TEU movimentado tendem ao limite superior. Verificar capacidade de tomadas de energia (plugs reefer) no levantamento de campo.

  Área equivalente por TEU    A_TEU         14--22 m²/TEU (pátio bruto)                                                  Combinação de TGS, f_s, f_util e f_seg                                                                                                                                    *Calculado a posteriori: A_bruta / CE_TEU. Valor entre 15 e 18 m²/TEU indica pátio bem aproveitado; acima de 22 m²/TEU, subutilização ou layout ineficiente. Serve como indicador de consistência do cálculo.*
  ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Fonte: UNCTAD (1985); World Bank (2007); Terminal Benchmarking (IHS Markit).

## 5.4. Formulação da capacidade estática (Eq. 4)

A capacidade estática de cada instalação é calculada pela expressão:

> CE = A_util × ρ × f_s × η_s (Eq. 4)

onde A_util é a área útil da instalação de armazenagem (m²), descontadas áreas de circulação, corredores e estruturas fixas, obtida do cadastro da autoridade portuária, dos contratos de arrendamento ou dos Planos de Desenvolvimento e Zoneamento (PDZ); ρ é a densidade de estocagem (t/m² para pátios e armazéns ou t/m³ para silos e tanques), calibrada conforme o tipo de carga a partir dos valores de referência do Quadro 3; f_s é o fator de empilhamento (adimensional), que expressa o número efetivo de camadas de estocagem (1,0 para silos e tanques, 2--5 para contêineres conforme equipamento de movimentação); e η_s é a eficiência estrutural da instalação (adimensional, 0 a 1), que desconta espaços mortos, áreas de manobra de equipamentos e reduções por incompatibilidade de cargas. Os valores de referência constam do Quadro 3.

Para tanques e silos, a A_util é substituída pelo volume útil interno (m³) e ρ passa a ser a densidade específica do produto (t/m³). Para granéis líquidos, a densidade varia conforme o produto: 0,85 t/m³ para óleos vegetais e 0,73 t/m³ para GLP (ANTAQ, 2021). Para pátios de contêineres, a expressão pode ser adaptada com ρ em TEU/m² e f_s como número de camadas (stacking height), resultando em CE em TEU.

Quando a autoridade portuária já disponibiliza a capacidade estática nominal homologada por instalação, esse valor pode ser adotado diretamente, desde que validado com os parâmetros do Quadro 3. A Eq. 4 é aplicada para recalcular CE nos casos em que a capacidade nominal não está disponível, está desatualizada ou precisa ser recalibrada para simulação de cenários.

**Quadro 3:** Parâmetros de referência para cálculo de capacidade estática por tipo de carga

  -------------------------------------------------------------------------------------------------------------------------------
  **Tipo de carga / instalação**       **ρ (t/m² ou t/m³)**   **f_s (empilhamento)**   **η_s (eficiência)**   **Fonte**
  ------------------------------------ ---------------------- ------------------------ ---------------------- -------------------
  Granéis sólidos vegetais (silo)      0,70--0,80 t/m³        1,0                      0,85--0,95             ANTAQ (2020b)

  Granéis sólidos vegetais (armazém)   1,5--2,5 t/m²          1,0--1,2                 0,80--0,90             ANTAQ (2020b)

  Granéis sólidos minerais (pátio)     3,0--5,0 t/m²          1,0--1,5                 0,75--0,90             ANTAQ; UNCTAD

  Granéis líquidos (tanque)            0,73--0,85 t/m³        1,0                      0,90--0,98             ANTAQ (2021)

  Carga geral (armazém)                1,5--2,0 t/m²          1,0--2,0                 0,65--0,80             UNCTAD (1985)

  Contêineres (pátio)                  1,2--1,8 TEU/m²        2--5 (altura)            0,65--0,70             ANTAQ; World Bank
  -------------------------------------------------------------------------------------------------------------------------------

Fonte: ANTAQ (2020b; 2021); UNCTAD (1985); World Bank (2007).

Os valores do Quadro 3 orientam a calibração inicial dos parâmetros da Eq. 4. A η_s de contêineres (0,65--0,70) reflete a parcela de área ocupada por corredores de RTG e espaços de manobra; em terminais com reach stackers, a η_s tende ao limite inferior da faixa. A calibração local é obrigatória: os parâmetros do quadro servem como referência de consistência, não como valores definitivos.

Fontes dos dados de entrada: área útil e volume interno são obtidos dos contratos de arrendamento, do PDZ ou diretamente junto ao operador. A ANTAQ publica a Proposição de Valores Referenciais Remuneratórios para Áreas Arrendáveis (ANTAQ, 2020b), que inclui parâmetros de densidade e eficiência por tipologia de instalação.

Retroárea: em portos com áreas retroportuárias operacionalmente interligadas, calcular CE separadamente para cada instalação retroportuária, com seus próprios parâmetros de ρ, f_s e η_s. Os contratos de passagem são regulados pela ANTAQ (Resolução n.º 2.240/2011). A CE total do sistema de armazenagem é a soma das CE de todas as instalações (área primária e retroárea), segregada por perfil de carga.

\[Nota técnica\] Para terminais de granéis agrícolas, os parâmetros DT_ef e f_s desta seção devem ser calculados em dois regimes (safra e entressafra), conforme procedimento descrito na Seção 10.3.1. O DT_ef de safra corresponde ao percentil 75 da distribuição observada nos meses de pico, e o f_s de safra ao percentil 90.

## 5.5. Capacidade da retroárea e áreas de apoio à armazenagem

Terminais que operam sob contrato de passagem (Resolução ANTAQ n.º 2.240/2011) não detêm titularidade sobre as instalações retroportuárias, mas fazem uso operacional de armazéns ou pátios de terceiros para armazenagem temporária de carga. Para esses terminais, a análise de capacidade do sistema de armazenagem deve incluir a estimativa da CE das instalações retroportuárias integradas ao fluxo de carga, com base nos mesmos parâmetros da Eq. 4 (A_útil, ρ, f_s, η_s), obtidos junto ao operador da retroárea ou por levantamento de campo. A não inclusão da retroárea subestima a capacidade total do sistema e pode produzir diagnósticos equivocados sobre o elo restritivo.

De forma complementar, quando o sistema logístico do terminal inclui áreas de apoio à armazenagem localizadas na retroárea do porto organizado, como Estações Aduaneiras do Interior (EADI), Zonas de Atividade Logística (ZAL), portos secos ou terminais de triagem ferroviária, a capacidade dessas instalações deve ser estimada de forma segregada e registrada na análise. Essas áreas funcionam como extensões do sistema de armazenagem portuária e seu dimensionamento afeta diretamente o DT médio do terminal, com impacto sobre a capacidade dinâmica calculada pela Eq. 5.

**Quadro 7:** Parâmetros das Eqs. 4 e 5: definições, unidades, fontes e procedimentos de obtenção

  -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  **Parâmetro**   **Definição**                                                            **Unidade**             **Fonte primária**                                      **Procedimento de obtenção**
  --------------- ------------------------------------------------------------------------ ----------------------- ------------------------------------------------------- ------------------------------------------------------------------------------------------------------------------------------------------
  A_util          Área útil de armazenagem efetivamente disponível para operação           m²                      PDZ, contratos de arrendamento, levantamento de campo   Descontar corredores de segurança, estruturas fixas e zonas de circulação de equipamentos; adotar planta atualizada do armazém ou pátio

  ρ               Densidade de estocagem (peso por unidade de área)                        t/m² ou TEU/m²          Operador portuário / AP                                 Dado operacional do arrendatário; validar por amostragem de cargas típicas; verificar se inclui alturas de empilhamento

  f_s             Fator de ocupação do piso (razão entre área ocupada e área útil total)   adimensional \[0--1\]   Operador portuário / AP                                 Estimado com base em dados históricos de ocupação máxima; referência: 0,70--0,80 para pátios de contêineres

  η_s             Eficiência operacional do sistema de armazenagem                         adimensional \[0--1\]   Operador portuário / AP                                 *Percentual de capacidade efetivamente aproveitável após manutenções, indisponibilidades e restrições de layout; referência: 0,85--0,95*

  CE              Capacidade estática de armazenagem resultante da Eq. 4                   t ou TEU                Calculado (Eq. 4)                                       Intermediário de cálculo; segregado por perfil de carga e por instalação (área primária e retrórea)

  DOA             Dias de ocupação média por rotação de estoque                            dias                    Operador portuário / AP                                 Tempo médio de permanência da carga no armazém ou pátio; obtido de registros operacionais do arrendatário; validar por perfil de carga

  DT              Dias totais do período de análise                                        dias                    Definição do estudo                                     365 dias para análise anual; 91 ou 92 dias para análise trimestral; ajustar conforme horizonte de avaliação

  η_d             Eficiência operacional do ciclo dinâmico de movimentação                 adimensional \[0--1\]   Operador portuário / AP                                 Fator de ajuste para perdas no ciclo de entrada e saída de cargas; referência: 0,90--0,95; calibrar com dados históricos do arrendatário
  -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Fonte: elaboração própria.

# 6. Passo 5: Estimativa da capacidade dinâmica de movimentação

A capacidade dinâmica (CD) expressa a movimentação anual do sistema de armazenagem, relacionando a capacidade estática com o número de rotações do estoque e a eficiência operacional:

> CD = CE × (DOA / DT) × η_d (Eq. 5)

onde CE é a capacidade estática calculada no Passo 4 (Eq. 4); DOA é o número de Dias Operacionais por Ano (365 para operação contínua, ajustado para portos com interrupções sazonais); DT é o tempo de permanência médio da carga na instalação, em dias (DT, do inglês dwell time); a razão DOA/DT é o número de giros anuais; e η_d é a eficiência operacional dinâmica (adimensional, 0 a 1), que captura perdas de capacidade por ineficiências de movimentação interna, tempos de carga e descarga nos armazéns, limpeza entre lotes e perda de sincronismo entre chegada de carga e disponibilidade de berço. Valores típicos: 0,80--0,95 para granéis com operação mecanizada e 0,65--0,85 para carga geral com movimentação convencional (UNCTAD, 1985; World Bank, 2007).

**Fontes e calibração do dwell** time: o DT deve ser coletado por grupo de carga e por zona (primária e retroárea) junto à autoridade portuária. Para contêineres, dados complementares da Receita Federal (plataforma Fala.BR). Como referência, a ANTAQ (2020b) publica valores de giros por faixa de eficiência: armazéns de menor eficiência operam com aproximadamente 12 giros/ano (DT de 30 dias); armazéns de alta eficiência, 30--35 giros/ano. Para granéis vegetais, DT na área primária tipicamente é de 13 dias, elevando-se para 28 dias nas áreas retroportuárias.

O DT é de calibração local obrigatória. Em commodities com sazonalidade acentuada, calcular CD separadamente para o período de pico e para o restante do ano. Quando a retroárea faz parte do sistema, a CD total é a soma da CD da área primária com a CD da retroárea, cada uma com seus próprios parâmetros de CE, DT e η_d. A η_d deve ser calibrada com dados operacionais do terminal; na ausência desses dados, adotar os valores de referência da UNCTAD (1985) e justificar a escolha.

\[Nota técnica\] Recomendação: revisar a referência à metodologia UNCTAD para dwell time. O benchmark de 3-5 dias para contêineres e 20 dias para granéis sólidos data da década de 1970 e não reflete a operação atual de terminais com agendamento eletrônico e automação de gates. Sugestão: incluir benchmarks atualizados ou exigir coleta empírica de DT por terminal.

## 6.1. Dwell time por zona de armazenagem: valores de referência para calibração

O dwell time não é homogêneo entre área primária e retroárea: cargas na retroárea apresentam DT sistematicamente superior ao da área primária, pois incorporam tempos de transferência, fila de acesso e eventualidades logísticas entre o porto e o armazém ou pátio retroportuário. O Quadro 22 apresenta valores de referência por perfil de carga e por zona, com indicação das fontes de dados e das variações sazonais que devem ser consideradas no cálculo.

**Quadro 22:** Dwell time por zona de armazenagem e perfil de carga: valores de referência para calibração

  -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  **Perfil de carga**      **DT área primária (dias)**   **DT retroárea (dias)**   **Variação sazonal**                                                                                  **Fontes e procedimento**
  ------------------------ ----------------------------- ------------------------- ----------------------------------------------------------------------------------------------------- ----------------------------------------------------------------------------------------------------------------------------------------------------------------
  Granel sólido agrícola   5--15                         20--40                    DT primária reduz para 5--8 dias no pico de safra; eleva-se para 15--20 dias na entressafra           TOS da autoridade portuária; questionário ao operador; faturamento de armazenagem (ANTAQ, 2020b). DT de retroárea inclui tempo de transporte e fila de acesso.

  Granel líquido           10--20                        25--45                    Menor variação sazonal; DT por produto: petróleo cru menor que combustíveis derivados                 Ordens de entrada e saída de tanque; registros da autoridade portuária; operador.

  Contêiner (importação)   5--12                         15--30                    Pico no 4º trimestre (festas de fim de ano)                                                           Receita Federal (Plataforma Fala.BR); TOS do terminal; ANTAQ (2020b). DT de exportação é sistematicamente menor que DT de importação no mesmo terminal.

  Contêiner (exportação)   3--8                          10--20                    Pico durante a safra agrícola (fevereiro a abril)                                                     Mesmas fontes acima. O DT de exportação é influenciado pelo agendamento de navios (port call window).

  Carga geral              10--25                        30--60                    Alta variância por tipo de produto; projetos industriais podem ter DT acima de 60 dias na retroárea   Questionário ao operador; registros do sistema de controle do terminal. Alta variância exige cálculo de CE com DT médio ponderado por tipo de carga.
  -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Fonte: ANTAQ (2020b); Receita Federal (Fala.BR); UNCTAD (1985).

A CD deve ser calculada para o cenário atual, com o DT observado no período de referência, e para os cenários futuros, com DT projetado. O DT projetado pode ser estimado com base em: (i) benchmarks de terminais similares com maior eficiência logística; (ii) metas contratuais dos arrendamentos e projetos de modernização do TOS; (iii) hipóteses do modelo de demanda para cada cenário de crescimento. Quando a projeção indica redução do DT por ganhos de eficiência, a CD aumenta sem ampliação da CE, o que representa capacidade latente do sistema de armazenagem. A memória de cálculo deve registrar o DT adotado para cada cenário e a justificativa correspondente.

## 6.2. Uso dos resultados e vinculação ao planejamento

Os resultados dos Passos 4 e 5 alimentam quatro frentes analíticas. A primeira é o diagnóstico da capacidade instalada atual: a comparação entre CE e CD no ano de referência indica se o sistema de armazenagem opera com folga ou próximo da saturação, e qual instalação ou perfil de carga representa o fator limitante. A segunda é a identificação de necessidades de expansão: quando CD projetada é inferior à demanda projetada para algum horizonte e perfil de carga, o resultado indica a magnitude do déficit de armazenagem e o período em que deve ocorrer. A terceira é o insumo para o Passo 10 (integração demanda-capacidade): C_arm = CD e entra na Eq. 13 para determinar o elo restritivo do sistema. A quarta é o subsídio para o Programa de Investimentos do Terminal (PIT) e para os documentos de planejamento do porto (Plano Mestre, PDZ): os resultados quantificam a capacidade incremental de armazenagem necessária por perfil de carga, definindo o escopo de eventuais projetos de ampliação.

# 7. Passo 6: Verificação da restrição do canal de acesso aquaviário

A compatibilidade física entre a frota projetada e o canal é verificada pela equação de calado máximo operacional:

> Cmax = Prof_NR − E_squat − E_ondas − E_sed − UKC (Eq. 7)

onde Prof_NR é a profundidade nominal do canal referenciada ao Nível de Redução (NR) da DHN; E_squat é o afundamento dinâmico; E_ondas é a contribuição da altura significativa de ondas; E_sed é a espessura de sedimento residual entre dragagens; e UKC é a folga abaixo da quilha (≥ 0,5 m em águas abrigadas, ≥ 1,0 m em canais expostos, conforme PIANC Report n.º 121/2014).

Fontes: batimetrias recentes (máximo 24 meses), referenciadas ao NR-DHN, fornecidas pela autoridade portuária ou concessionária do canal (ANTAQ, 2024). Perfil de frota: Estatístico Aquaviário da ANTAQ (classe de DWT e tipo de navio por atracação). Condições meteorológicas e marítimas: registros da Marinha (DHN) e INMET. Critérios operacionais: Portaria de Tráfego Marítimo da autoridade portuária. Em canais com restrição de maré, cruzar tábuas de maré com requisitos de calado para calcular horas anuais efetivas de operação.

\[Nota Técnica\] Os parâmetros de capacidade do canal de acesso aquaviário (número máximo de movimentações diárias, janelas de maré operacionais, restrições de calado por tipo de embarcação e condições de manobrabilidade nas bacias de evolução) são produzidos pelo Caderno de Acessos do macrocaderno de Infraestrutura e Operações Portuárias. O roteiro de capacidades recebe esses parâmetros como dado de entrada para a verificação da Eq. 7 e para a composição de C_sistema na Eq. 13. Quando o Caderno de Acessos identificar restrições operacionais no canal (gargalos geométricos, limitações de praticagem ou indisponibilidade de VTMIS), essas restrições devem ser traduzidas em redução do número efetivo de movimentações diárias utilizado no cálculo de verificação do canal.

# 8. Passo 7: Análise da capacidade de hinterlândia

A capacidade de hinterlândia compreende a soma das capacidades dos acessos rodoviário e ferroviário ao porto:

> C_hint = C_rod + C_fer (Eq. 8)

O cálculo de cada componente é detalhado nas subseções seguintes. O Quadro 4 apresenta os parâmetros operacionais de referência para calibração dos modelos de acesso.

\[Nota Técnica\] Os valores de capacidade dos acessos rodoviário, ferroviário e dutoviário utilizados nesta seção são produzidos pelo Caderno de Acessos do macrocaderno de Infraestrutura e Operações Portuárias. O Caderno de Acessos fornece, como resultado de suas análises: (a) para o acesso rodoviário, o nível de serviço (LOS) das rodovias da hinterlândia, a capacidade das portarias (taxa de utilização e fluxo máximo admissível) e a capacidade dos pátios de triagem; (b) para o acesso ferroviário, a capacidade instalada em pares diários de trens (PDT), a capacidade efetiva do terminal ferroportuário e o índice de utilização crítico (IUC); (c) para o acesso dutoviário, a capacidade hidráulica e o volume operacional. Esses valores alimentam as Eqs. 8 a 12 do presente roteiro. Quando o Caderno de Acessos incluir resultados de simulação de tráfego (microsimulação de portarias, simulação de interação entorno-portarias), esses resultados devem ser utilizados preferencialmente aos valores analíticos das Eqs. 8 a 12, registrando a substituição na memória de cálculo.

## 8.1. Acesso rodoviário

A capacidade rodoviária é determinada pelo mínimo entre três componentes: a capacidade do gate de acesso ao porto (G), a capacidade das docas de carga e descarga (DU) e a capacidade do pátio de triagem:

> C_rod = min (G, DU, Pátio) (Eq. 9)

A capacidade do gate é calculada por:

> G = N_lane × P_g × η_p × U × L_F × H_eff × σ (Eq. 10)

onde N_lane é o número de faixas operacionais do gate (cadastro da autoridade portuária); P_g é a produtividade do gate (veículos/hora por faixa), conforme Quadro 4; η_p é a eficiência operacional do processamento (adimensional), que desconta interrupções, filas de documentação e trocas de turno; U é a carga útil média por veículo (t/veículo), estimada a partir de contagens classificatórias nas vias de acesso (DNIT) ou registros de pesagem da balança portuária; L_F é o fator de carga (adimensional), razão entre a carga efetiva e a capacidade nominal do veículo; H_eff é o número de horas efetivas de operação do gate por ano (h/ano), descontadas restrições municipais de circulação de veículos pesados e períodos de manutenção; e σ é o fator de sazonalidade (adimensional), que ajusta a capacidade média anual ao pico de safra (tipicamente 0,70--0,85 em portos de commodities agrícolas).

A capacidade das docas de carga e descarga (DU) segue lógica análoga:

> DU = N_DU × P_DU × η_p × H_eff × σ (Eq. 11)

onde N_DU é o número de docas ou pontos de carga/descarga operacionais; e P_DU é a produtividade por doca (veículos/hora por DU), conforme Quadro 4. Os demais parâmetros seguem a mesma definição da Eq. 10. Para converter a capacidade em veículos/ano para t/ano, multiplicar pelo produto U × L_F.

A capacidade do pátio de triagem (TPA) funciona como buffer entre o gate e o cais. Sua capacidade anual é estimada pela capacidade estática do pátio (em veículos) multiplicada pelo número de giros diários (ciclos de entrada, espera e saída) e pelo número de dias operacionais. Quando o TPA opera com agendamento eletrônico (OTM), a taxa de giro tende a ser maior que em sistemas de fila livre.

**Quadro 4:** Parâmetros operacionais de referência para acesso terrestre

  -------------------------------------------------------------------------------------------------------------------
  **Componente**                  **Parâmetro**          **Faixa típica**   **Unidade**        **Fonte**
  ------------------------------- ---------------------- ------------------ ------------------ ----------------------
  Gate rodoviário (granéis)       P_g (produtividade)    40--80             veíc/h por faixa   ANTAQ; DNIT

  Gate rodoviário (contêineres)   P_g (produtividade)    25--50             veíc/h por faixa   ANTAQ; World Bank

  Doca de carga/descarga (DU)     P_DU (produtividade)   8--20              veíc/h por DU      Operador; ANTAQ

  Balança rodoviária              Tempo de pesagem       2--5               min/veículo        DNIT; operador

  Pátio de triagem (TPA)          Capacidade estática    50--300            veículos           Autoridade portuária

  Composição ferroviária          TU_trem (carga útil)   2.500--8.000       t/trem             PEF; ANTT
  -------------------------------------------------------------------------------------------------------------------

Fonte: ANTAQ; DNIT; ANTT (PEF); World Bank (2007).

Dados e fontes: N_lane e N_DU são obtidos do cadastro da autoridade portuária. P_g e P_DU são calibrados a partir do Quadro 4 e validados com dados operacionais do terminal (registros de passagem de balança, horários de entrada e saída). Contagens classificatórias nas vias de acesso (DNIT) fornecem o perfil veicular e a carga útil média. Restrições municipais de circulação de veículos pesados são obtidas da legislação municipal e incorporadas em H_eff. Quando houver congestionamento relevante nas vias de acesso externo, aprofundar com simulação de tráfego (PTV Vissim ou similar) e com a metodologia HCM (TRB, 2016) para determinação do nível de serviço (LOS).

## 8.2. Fatores de reversibilidade operacional e análise de chegada de veículos

As faixas do gate podem operar em modo reversível, redirecionando a capacidade entre fluxos de entrada e saída conforme a demanda. O número efetivo de faixas no pico de chegada é N_in = N_lane − N_out_min, onde N_out_min é o mínimo de faixas mantidas para saída. O fator de reversibilidade (f_rev = N_rev / N_lane, onde N_rev é o número de faixas reversíveis) permite modelar configurações assimétricas: terminais com fluxo predominantemente de importação ou exportação se beneficiam de layouts com maior proporção de faixas reversíveis, reduzindo o tempo de espera no pico de um único sentido sem ampliar a infraestrutura física.

A análise do padrão de chegada de caminhões e composições ferroviárias deve incorporar dados de simulação das vias de acesso direto ao terminal. O objetivo é identificar restrições operacionais que impactem a capacidade dos gates e os fluxos de recepção e expedição. Os parâmetros a avaliar são: (i) padrão de chegada de caminhões (distribuição horária e sazonal, com identificação dos picos de demanda no gate); (ii) condições para descarga direta (possibilidade de o veículo ser descarregado sem passagem por área de armazenagem intermediária, o que reduz o tempo de permanência e aumenta o giro); (iii) capacidade de permanência de veículos no interior do porto (número máximo de caminhões ou composições em espera ou em manobra dentro do perímetro, sem comprometer a fluidez do pátio interno); e (iv) fluidez nos eixos de acesso externo (relação V/C nas vias limítrofes, nível de serviço HCM e presença de filas de espera externas ao porto).

Simulação de tráfego: quando o congestionamento nas vias externas ou no interior do gate for identificado como fator limitante, aprofundar a análise com simulação micros-cópica de tráfego (PTV Vissim, AIMSUN ou similar), que modela explicitamente a interação entre chegadas de caminhões, filas no gate, processamento nas faixas e saída do terminal. Os parâmetros de entrada da simulação são: taxa de chegada de caminhões por hora (obtida das contagens classificatórias DNIT ou de registros de balança), tempo médio de processamento por faixa (1/P_g), e número e configuração das faixas (incluindo faixas reversíveis). A simulação permite estimar o comprimento médio da fila externa, o tempo médio de espera e a probabilidade de saturação do gate nos períodos de pico.

## 8.3. Acesso ferroviário

A capacidade ferroviária é calculada por:

> C_fer = N_trens × TU_trem × D_op (Eq. 12)

onde N_trens é o número máximo de composições que podem operar por dia no corredor ferroviário que serve o porto, determinado pelas restrições de capacidade de linha (número de cruzamentos, sistema de sinalização, janelas de manutenção); TU_trem é a tonelagem útil média por composição (t/trem), conforme Quadro 4; e D_op é o número de dias operacionais por ano (tipicamente 340--350 para ferrovias de carga, descontando manutenção programada da via).

Fontes: N_trens e TU_trem são obtidos dos Programas de Exploração Ferroviária (PEF) da concessionária, das Notas de Benchmarking da ANTT e dos planos da EPL. Na ausência de dados detalhados, adotar a abordagem de enquadramento: confrontar a capacidade declarada ou projetada para o corredor (PEF, projetos de ampliação) com a demanda no horizonte do plano. Registrar explicitamente a precisão limitada dessa abordagem. A capacidade do pátio ferroviário interno do porto (recepção, manobra e distribuição) deve ser verificada separadamente, pois pode constituir gargalo local mesmo quando a malha externa possui folga.

## 8.4. Capacidade de recepção e expedição por trem: carga por vagão e produtividade do sistema ferroviário

A capacidade ferroviária no pátio interno do porto depende não apenas da via externa (Eq. 12), mas também da produtividade dos sistemas de recepção da composição. A carga útil por composição (TU_trem) é o produto da carga útil por vagão (TU_vag, t/vagão) pelo número de vagões por composição (N_vag): TU_trem = TU_vag × N_vag. O TU_vag depende do tipo de vagão (hopper fechado GHF: 70--80 t/vagão; hopper aberto GHA: 70--80 t; prancha GN: 60--80 t conforme produto) e da eficiência de carregamento (fração da capacidade nominal efetivamente utilizada: 0,90--0,98). A produtividade do sistema ferroviário no porto também inclui: (i) o tempo de recepção por composição (T_recep, h/trem), que engloba manobra de entrada, posicionamento sobre o tombador ou moega, operação de descarga e saída do pátio; e (ii) a capacidade do pátio ferroviário interno (N_vias × comprimento_via), que determina quantas composições podem ser recebidas simultaneamente.

A fórmula expandida de capacidade ferroviária, incorporando o sistema de recepção no pátio interno, é:

> C_fer = min(C_fer_via, Q_rec_ferro, C_pátio_ferro) (Eq. 12a)

onde C_fer_via = N_trens × TU_trem × D_op é a capacidade determinada pela via externa (Eq. 12); Q_rec_ferro é a capacidade dos equipamentos de recepção no pátio (tombadores, moegas, correias), calculada pelo Quadro 23; e C_pátio_ferro é a capacidade de trânsito do pátio ferroviário interno (t/ano), estimada pela capacidade estática do pátio em composições simultâneas multiplicada pelo número de ciclos por dia e pelos dias operacionais.

## 8.5. Equipamentos de recepção e expedição de carga: tombadores, moegas, correias e estações de bombeamento

Os equipamentos de recepção e expedição constituem a interface entre o sistema de transporte terrestre e o sistema de armazenagem do porto. Para granéis sólidos, os tombadores de vagões e as moegas com sistemas de correias determinam o ritmo máximo de descarga da composição; para granéis líquidos, as estações de bombeamento e os dutos de recepção fixam a vazão máxima de transferência. A capacidade desses equipamentos pode ser o elo mais restritivo da hinterlândia, mesmo quando a via externa e o gate dispõem de folga. O Quadro 23 apresenta as fórmulas e os parâmetros de estimativa por tipo de equipamento.

**Quadro 23:** Capacidade dos equipamentos de recepção e expedição de carga por tipo

  -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  **Equipamento**                          **Tipo de carga**                                            **Fórmula de capacidade**                       **Parâmetros-chave**                                                                                                                     **Faixa típica e fontes**
  ---------------------------------------- ------------------------------------------------------------ ----------------------------------------------- ---------------------------------------------------------------------------------------------------------------------------------------- ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  Tombador de vagões                       Granel sólido (soja, milho, farelo, fertilizante, minério)   Q_tomb = P_tomb × n_tomb × H_ef_tomb × η_tomb   P_tomb: produtividade por tombador (t/h); n_tomb: número de tombadores; H_ef_tomb: horas efetivas/ano; η_tomb: eficiência (0,65--0,80)   P_tomb: 1.000--2.500 t/h para tombadores de vagão-hopper modernos. H_ef_tomb = H_cal menos interrupções de manutenção e limpeza de fosso. Fonte: relatórios operacionais de VLI, VALE; manuais do fabricante.

  Moega e sistema de correias              Granel sólido; carga geral ensacada                          Q_moega = Σ(P_corr_i × η_corr_i)                P_corr_i: capacidade nominal da correia i (t/h); η_corr_i: eficiência da correia (0,70--0,85); somatório sobre correias em paralelo      P_corr: 500--2.000 t/h conforme largura (600--1.800 mm). Verificar coerência entre capacidade da moega e da correia de transferência para silo ou armazém. Fonte: CEMA (Conveyor Equipment Manufacturers Assoc.); manuais do fabricante.

  Estação de bombeamento                   Granel líquido (derivados, óleos vegetais)                   Q_bomb = n_bomb × Q_unit × η_bomb × ρ_p         n_bomb: bombas operacionais; Q_unit: vazão unitária (m³/h); η_bomb: eficiência (0,75--0,92); ρ_p: densidade do produto (t/m³)            Q_unit: óleos vegetais 200--600 m³/h; derivados de petróleo 500--1.200 m³/h. Quedas de pressão em dutos longos limitam a vazão efetiva; verificar diâmetro e extensão dos dutos no levantamento de campo. Fonte: API 2610; ANTAQ (2021).

  Rampa Ro-Ro (embarçque e desembarçque)   Veículos (automotivos, máquinas, carga rolante)              Q_ramp = N_ramp × P_ramp × H_ef × η_ramp        N_ramp: rampas operacionais; P_ramp: veículos/h por rampa; η_ramp: 0,70--0,85                                                            P_ramp: 20--40 veículos/h (passeio); 10--20 veículos/h (veículos pesados). Limitante freqüente: acesso ao pátio de estocagem. Converter veículos/h para t/h pelo peso médio por categoria.
  -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Fonte: VALE; VLI; API 2610; CEMA; ANTAQ (2021); manuais de fabricantes.

\[Nota técnica\] Para terminais de granéis agrícolas, os volumes diários de chegada rodoviária e ferroviária utilizados nesta seção devem ser segmentados em regime de safra e entressafra, conforme procedimento descrito na Seção 10.3.1. A capacidade de hinterlândia de safra (C_hint_safra) corresponde ao cálculo realizado com os volumes médios diários dos meses de pico.

## 8.6. Definição da capacidade de hinterlândia como menor valor entre os subsistemas

\[Nota técnica\] Recomendação: incluir variável de interferência rodoferroviária no modelo de capacidade de hinterlândia. Em terminais com acesso rodoferroviário compartilhado, cruzamentos em nível entre a ferrovia e as vias rodoviárias causam bloqueios que reduzem a capacidade de recepção independentemente da capacidade nominal da linha férrea ou do pátio.

A capacidade efetiva de cada modal é determinada pelo menor valor entre seus componentes operacionais internos. Para o acesso rodoviário, a Eq. 9 define C_rod = min(G, DU, Q_rec_road, Pátio), onde Q_rec_road é a capacidade dos equipamentos de recepção e expedição rodoviária (tombadores, moegas, correias para caminhões). Para o acesso ferroviário, a Eq. 12a define C_fer = min(C_fer_via, Q_rec_ferro, C_pátio_ferro). A capacidade total de hinterlândia é a soma dos modais: C_hint = C_rod + C_fer. A restrição sistêmica se aplica em dois níveis: dentro de cada modal (mínimo interno dos componentes, Eqs. 9 e 12a) e entre subsistemas do sistema portuário (mínimo externo, Eq. 13: C_sistema = min(C_cais, C_arm, C_hint)).

Para portos que operam com um único modal terrestre, C_hint é igual à capacidade desse modal. Portos exclusivamente rodoviários: C_hint = C_rod. Portos com corredor ferroviário exclusivo de granel: C_hint = C_fer. A decomposição de C_hint por modal deve ser registrada no quadro-síntese (Quadro 5) para permitir identificar se o gargalo está no modal rodoviário, ferroviário ou em algum equipamento específico de recepção e expedição.

# 9. Passo 9: Integração sistêmica da capacidade

Os passos anteriores geram estimativas de capacidade para cada subsistema. A integração sistêmica identifica o elo restritivo aplicando, para cada perfil de carga j e cada horizonte de planejamento t:

> C_sistema(j, t) = min ( C_cais(j,t), C_arm(j,t), C_hint(j,t) ) (Eq. 13)

onde C_cais(j,t) é a capacidade de cais para o perfil de carga j no horizonte t (Eqs. 1a/1b, ajustada pela Eq. 3 quando aplicável); C_arm(j,t) é a capacidade dinâmica de armazenagem para o perfil j no horizonte t (Eq. 5); e C_hint(j,t) é a capacidade de hinterlândia para o perfil j no horizonte t (Eq. 8). A restrição do canal de acesso (Eq. 7) atua como filtro: se o calado máximo operacional não comporta a frota projetada, o throughput efetivo é limitado à frota compatível.

A Eq. 13 deve ser aplicada separadamente por perfil de carga (granéis sólidos vegetais, granéis sólidos minerais, carga geral, granéis líquidos, contêineres) e para cada horizonte de planejamento (ano-base, 2030, 2040 e 2050). A capacidade total do porto em cada horizonte é o somatório das C_sistema(j,t) de todos os perfis. A consistência entre parâmetros e cenários é condição de validação: os mesmos cenários de investimento e as mesmas premissas operacionais devem ser usados em todos os subsistemas para cada horizonte.

A cadeia de transmissão do gargalo percorre, na direção do fluxo de carga: acesso aquaviário, berço e cais, equipamentos de pátio, armazenagem primária, retroárea, portarias e vias internas, e eixos de hinterlândia rodoviário e ferroviário. Ampliar a capacidade de cais sem equalizar a armazenagem apenas antecipa a saturação desta; construir novas portarias sem ampliar a capacidade viária de hinterlândia desloca o congestionamento para o acesso externo; dragagens sem ajuste da frota-alvo não elevam a movimentação efetiva.

\[Nota Técnica\] A aplicação da Eq. 13 pressupõe que os valores de C_hint e da verificação do canal de acesso já incorporem os resultados do Caderno de Acessos do macrocaderno de Infraestrutura e Operações Portuárias. Caso o Caderno de Acessos não esteja concluído no momento da elaboração do roteiro de capacidades, a integração sistêmica deve ser realizada em duas etapas: (i) uma versão preliminar utilizando estimativas analíticas das Eqs. 7 a 12 para C_hint e canal, com registro explícito da condição provisória; e (ii) uma versão consolidada após a entrega do Caderno de Acessos, substituindo as estimativas analíticas pelos valores calibrados por simulação e levantamento de campo. A versão final do quadro de consolidação sistêmica (Quadro 5) deve indicar a origem de cada valor de capacidade (analítico ou Caderno de Acessos).

O diagnóstico deve ser compilado em quadro-síntese que confronte, para o mesmo horizonte de demanda e sob os mesmos cenários de investimento, as seguintes métricas por perfil de carga: C_cais (t/ano), BOR observado e BOR admissível (Eq. 2a, Quadro 1), BUR (Eq. 2b), C_arm = CD (t/ano), C_hint (t/ano) decomposta em C_rod e C_fer, C_sistema (Eq. 13) e identificação do elo restritivo. Para os acessos rodoviários, reportar o Nível de Serviço HCM (LOS A-F) nas vias externas e a fila média nas portarias. Para ferrovias, reportar o índice de utilização (composições efetivas / N_trens). O A Eq. 13 deve ser aplicada separadamente por perfil de carga (granéis sólidos vegetais, granéis sólidos minerais, carga geral, granéis líquidos, contêineres) e para cada horizonte de planejamento (ano-base, 2030, 2040 e 2050). A capacidade total do porto em cada horizonte é o somatório das C_sistema(j,t) de todos os perfis. A consistência entre parâmetros e cenários é condição de validação: os mesmos cenários de investimento e as mesmas premissas operacionais devem ser usados em todos os subsistemas para cada horizonte.

A cadeia de transmissão do gargalo percorre, na direção do fluxo de carga: acesso aquaviário, berço e cais, equipamentos de pátio, armazenagem primária, retroárea, portarias e vias internas, e eixos de hinterlândia rodoviário e ferroviário. Ampliar a capacidade de cais sem equalizar a armazenagem apenas antecipa a saturação desta; construir novas portarias sem ampliar a capacidade viária de hinterlândia desloca o congestionamento para o acesso externo; dragagens sem ajuste da frota-alvo não elevam a movimentação efetiva.

A Eq. 13 deve ser aplicada separadamente por perfil de carga (granéis sólidos vegetais, granéis sólidos minerais, carga geral, granéis líquidos, contêineres) e para cada horizonte de planejamento (ano-base, 2030, 2040 e 2050). A capacidade total do porto em cada horizonte é o somatório das C_sistema(j,t) de todos os perfis. A consistência entre parâmetros e cenários é condição de validação: os mesmos cenários de investimento e as mesmas premissas operacionais devem ser usados em todos os subsistemas para cada horizonte.

A cadeia de transmissão do gargalo percorre, na direção do fluxo de carga: acesso aquaviário, berço e cais, equipamentos de pátio, armazenagem primária, retroárea, portarias e vias internas, e eixos de hinterlândia rodoviário e ferroviário. Ampliar a capacidade de cais sem equalizar a armazenagem apenas antecipa a saturação desta; construir novas portarias sem ampliar a capacidade viária de hinterlândia desloca o congestionamento para o acesso externo; dragagens sem ajuste da frota-alvo não elevam a movimentação efetiva.

de projeto é o somatório de C_sistema(j,t) para todos os perfis no horizonte considerado.

A análise sistêmica integrada, incluindo o papel do cais como elemento estruturante e a interdependência dos subsistemas de armazenagem e hinterlândia, está exposta na seção \"Estrutura do capítulo de capacidade\". Os procedimentos de integração sistêmica são aplicados neste passo mediante a Eq. 13 (C_sistema(j,t) = min(C_cais, C_arm, C_hint)) e o preenchimento do Quadro 5.

## 9.1. Identificação obrigatória do elo limitante por cenário

A identificação do gargalo operacional é obrigatória em cada cenário analisado. Para cada combinação de perfil de carga j e horizonte t, o elo limitante é o subsistema cujo valor de capacidade coincide com C_sistema(j,t) = min(C_cais, C_arm, C_hint) na Eq. 13. O elo deve ser explicitamente registrado na coluna correspondente do Quadro 5 e no texto de diagnóstico, com a indicação do valor numérico que determina a restrição. O Quadro 24 sistematiza os critérios de identificação por subsistema, os indicadores de diagnóstico associados e as ações de equalização correspondentes.

**Quadro 24:** Critérios de identificação do elo limitante, indicadores de diagnóstico e ações de equalização por subsistema

  --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  **Subsistema**                        **Condição de gargalo**                                                                                                                                                         **Indicadores de diagnóstico**                                                                                                                                                                    **Ação de equalizacão recomendada**
  ------------------------------------- ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  Cais                                  C_cais ≤ C_arm e C_cais ≤ C_hint para o mesmo perfil de carga e horizonte                                                                                                       BOR calculado ≥ BOR_adm (Quadro 17); produtividade efetiva dos equipamentos abaixo da referência (Quadro 2); H_ef insuficiente por elevação de H_cli, H_mnt ou H_nav                              Ampliar número de berços ou equipamentos; reduzir H_mnt por manutenção preditiva; mitigar H_nav por melhoria de calado ou pilotagem; avaliar BOR_adm com modelo Erlang-C calibrado.

  Armazenagem                           C_arm \< C_cais e C_arm \< C_hint para o mesmo perfil e horizonte                                                                                                               Dwell time efetivo (DT_ef) acima do valor de equilíbrio: DT_eq = CE × DOA / C_cais; giro real \< giro de referência ANTAQ (2020b); taxa de utilização do sistema de armazenagem próxima a 100%    Ampliar CE (novas áreas ou instalações, Eq. 4); reduzir DT por modernização do TOS e agendamento de retirada; se giro máximo viável já for atingido, tratar como restrição operacional e calcular CD com DT_ef (incluindo formação de lote, limpeza e manutenção).

  Armazenagem (restrição operacional)   Giro real inferior ao giro nominal por condicionantes operacionais: formação de lote, limpeza de estruturas, manutenção de silos/moegas, segregação de produtos incompatíveis   DT_ef = DT_permanencia + T_lote + T_limpeza + T_manutencao; CD_real = CE × (DOA / DT_ef) × η_d; a diferença CD_nominal − CD_real quantifica a capacidade consumida por operações não-produtivas   Levantar os intervalos operacionais (T_lote, T_limpeza, T_manut) por instalação e tipo de carga; registrar em memória de cálculo; recalcular CD com DT_ef; incluir esses intervalos como parâmetros de cenário futuro se houver projetos de melhoria operacional.

  Hinterlândia rodoviária               C_rod \< C_fer e C_hint \< C_cais e C_hint \< C_arm                                                                                                                             LOS E/F nas vias externas ao porto (V/C \> 0,85); fila média no gate acima do nível de serviço-alvo; N_lane × P_g insuficiente para o pico de chegada de caminhões                                Ampliar N_lane; implantar OTM com agendamento eletrônico; negociar janelas de circulação com o município; ampliar Q_rec_road (moegas e tombadores para caminhões); avaliar descarga direta para reduzir tempo de permanência no portão.

  Hinterlândia ferroviária              C_fer \< C_rod e C_hint \< C_cais e C_hint \< C_arm                                                                                                                             Índice de utilização (composições efetivas / N_trens_max) \> 0,85; Q_rec_ferro é o componente mínimo da Eq. 12a; gargalo no pátio ferroviário interno (N_vias × comprimento_via insuficiente)     Ampliar capacidade de via externa (cruzamentos, sinalização); aumentar TU_trem (vagões hopper de maior capacidade); instalar tombadores adicionais ou ampliar moegas; ampliar pátio ferroviário interno.
  --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Fonte: elaboração própria com base em UNCTAD (1985); World Bank (2007); ANTAQ (2020b).

Quando o gargalo se desloca entre cenários, o relatório deve: (i) indicar o ano de transferência do elo restritivo; (ii) quantificar o déficit no novo subsistema limitante; e (iii) avaliar se os projetos do PIT dimensionados para o novo gargalo são suficientes para restabelecer a folga operacional. Ampliar a capacidade de cais além do ponto de transferência do gargalo, sem equalizar os demais subsistemas, gera capacidade ociosa e não eleva o throughput efetivo do terminal.

## 9.2. Quadro-modelo de consolidação sistêmica

O quadro a seguir constitui o template padrão de consolidação sistêmica. Cada linha corresponde a um perfil de carga em um horizonte de planejamento. Os campos marcados \[calc.\] devem ser preenchidos com os valores calculados nos Passos 2, 4--5 e 7. O campo \[Q1\] na coluna BOR adm. deve ser substituído pelo limite correspondente ao tipo de terminal e número de berços, conforme Quadro 1. O elo restritivo é o subsistema cujo valor coincide com C_sistema --- isto é, o mínimo da Eq. 13. Para contêineres, as colunas de capacidade devem ser preenchidas em TEU/ano em vez de t/ano.

**Quadro 5:** Template de consolidação sistêmica de capacidade portuária

  ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  **Perfil de carga**         **Horizonte**   **C_cais (t/ano)**   **BOR obs. (%)**   **BOR adm. (%)**   **BUR (%)**   **C_arm (t/ano)**   **C_hint (t/ano)**   **C_sistema (t/ano)**   **Elo restritivo**
  --------------------------- --------------- -------------------- ------------------ ------------------ ------------- ------------------- -------------------- ----------------------- --------------------
  **Granel Sólido Vegetal**   Ano-base        \[calc.\]            \[calc.\]          \[Q1\]             \[calc.\]     \[calc.\]           \[calc.\]            \[calc.\]               \[a definir\]

                              2030            \[calc.\]            --                 \[Q1\]             \[calc.\]     \[calc.\]           \[calc.\]            \[calc.\]               \[a definir\]

                              2040            \[calc.\]            --                 \[Q1\]             \[calc.\]     \[calc.\]           \[calc.\]            \[calc.\]               \[a definir\]

                              2050            \[calc.\]            --                 \[Q1\]             \[calc.\]     \[calc.\]           \[calc.\]            \[calc.\]               \[a definir\]

  **Granel Sólido Mineral**   Ano-base        \[calc.\]            \[calc.\]          \[Q1\]             \[calc.\]     \[calc.\]           \[calc.\]            \[calc.\]               \[a definir\]

                              2030            \[calc.\]            --                 \[Q1\]             \[calc.\]     \[calc.\]           \[calc.\]            \[calc.\]               \[a definir\]

                              2040            \[calc.\]            --                 \[Q1\]             \[calc.\]     \[calc.\]           \[calc.\]            \[calc.\]               \[a definir\]

                              2050            \[calc.\]            --                 \[Q1\]             \[calc.\]     \[calc.\]           \[calc.\]            \[calc.\]               \[a definir\]

  **Granel Líquido**          Ano-base        \[calc.\]            \[calc.\]          \[Q1\]             \[calc.\]     \[calc.\]           \[calc.\]            \[calc.\]               \[a definir\]

                              2030--2050      \[calc.\]            --                 \[Q1\]             \[calc.\]     \[calc.\]           \[calc.\]            \[calc.\]               \[a definir\]

  **Carga Geral**             Ano-base        \[calc.\]            \[calc.\]          \[Q1\]             \[calc.\]     \[calc.\]           \[calc.\]            \[calc.\]               \[a definir\]

                              2030--2050      \[calc.\]            --                 \[Q1\]             \[calc.\]     \[calc.\]           \[calc.\]            \[calc.\]               \[a definir\]

  **Contêineres**             Ano-base        \[calc. TEU\]        \[calc.\]          \[Q1\]             \[calc.\]     \[calc. TEU\]       \[calc. TEU\]        \[calc. TEU\]           \[a definir\]

                              2030            \[calc. TEU\]        --                 \[Q1\]             \[calc.\]     \[calc. TEU\]       \[calc. TEU\]        \[calc. TEU\]           \[a definir\]

                              2040            \[calc. TEU\]        --                 \[Q1\]             \[calc.\]     \[calc. TEU\]       \[calc. TEU\]        \[calc. TEU\]           \[a definir\]

                              2050            \[calc. TEU\]        --                 \[Q1\]             \[calc.\]     \[calc. TEU\]       \[calc. TEU\]        \[calc. TEU\]           \[a definir\]
  ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Fonte: elaboração com base nas Eqs. 1a/1b, 2a/2b, 5, 8 e 13.

\[Q1\] = limite do Quadro 1 conforme tipo de terminal e número de berços; \[--\] = BOR futuro não observado (estimado por simulação ou cenário); \[calc.\] = valor a ser preenchido pelo analista após cálculos dos passos correspondentes; \[calc. TEU\] = valor em TEU/ano, aplicado exclusivamente ao perfil de carga conteinerizada.

# 10. Passo 10: Projeção de capacidade futura e projetos do PIT

Cada projeto do PIT deve ser traduzido em incremento de capacidade: novos berços ampliam C_cais (Eqs. 1a/1b); novos silos ou armazéns ampliam CE (Eq. 4) e, consequentemente, CD (Eq. 5); dragagem altera Cmax (Eq. 7); novos gates ou docas ampliam C_rod (Eqs. 9--11); e ampliações ferroviárias acrescentam capacidade a C_fer (Eq. 12). Cada incremento deve ser recalculado na Eq. 13 para verificar se o elo restritivo se transfere para outro subsistema.

Fontes: Plano Mestre do porto (EPL), editais de licitação e concessão (ANTAQ), PEF da ANTT e estudos de viabilidade da autoridade portuária. O PDZ define a vocação de cada área e as condições de reordenação espacial.

A projeção consiste em somar os incrementos dos projetos às capacidades atuais, com respectivas datas de entrada em operação. O resultado é uma curva de capacidade ao longo do tempo, confrontada com a projeção de demanda para identificar o ano de saturação. Após cada rodada de investimento simulada, verificar se o gargalo se transfere para outro elo ou se o throughput global é efetivamente elevado.

Captura de carga: estimar a parcela da demanda potencial da área de influência atraída pelo porto, considerando concorrência e elasticidade de fluxos. Fontes: estatístico ANTAQ (market share histórico, composição de frota), Plano Nacional de Logística Portuária (PNLP, projeções de demanda por commodity) e entrevistas estruturadas com embarcadores.

## 10.1. Diferenciação entre cenário atual e cenários futuros

Para fins deste roteiro, definem-se dois cenários formais de capacidade. O Cenário Atual corresponde à capacidade calculada com os parâmetros operacionais e a estrutura física observados no ano-base da análise: berços existentes, equipamentos em operação, áreas de armazenagem licenciadas, acessos rodoviários e ferroviários na configuração vigente. O Cenário Atual serve como referência de validação: C_sistema calculado deve ser confrontado com a movimentação histórica observada no mesmo período; desvios superiores a 10% exigem revisão dos parâmetros. O Cenário Futuro corresponde à capacidade projetada para os horizontes 2030, 2040 e 2050, incorporando três categorias de alteração dos parâmetros detalhadas a seguir.

A análise de capacidade distingue dois níveis de representação temporal. O primeiro é a capacidade atual, calculada com os parâmetros operacionais do ano-base (Lm, Ta, BOR_adm, ρ, f_s, η_s, N_trens etc.) e a estrutura física existente. Esse valor é o ponto de partida e a referência de validação: deve ser confrontado com a movimentação histórica observada para confirmar que o modelo reproduz o comportamento real do terminal. O segundo nível é a capacidade projetada, que incorpora três categorias de alteração dos parâmetros ao longo do horizonte de planejamento.

\(a\) Ganhos de eficiência operacional: redução de Ta por janelas de atracação, reserva on-line e processos Just-in-Time; aumento da prancha por otimização de turnos e gestão de equipes. Esses ganhos elevam C_cais sem ampliação física e devem ser documentados com base em benchmarks ou metas contratuais do arrendatário.

\(b\) Modernização de equipamentos: substituição de guindastes portáis por ship-to-shore de maior capacidade; automação de pátios de contêineres; instalação de stackers em armazéns de granel sólido. Cada substituição implica recalibrar o parâmetro afetado (prancha, ρ ou f_s) e recalcular C_cais ou C_arm para o horizonte em que a modernização entra em operação.

\(c\) Investimentos em infraestrutura: novos berços (incrementa b na Eq. 1b), novas áreas de armazenagem (incrementa A_util na Eq. 4), dragagem (altera Cmax na Eq. 7), novos gates e pátios de triagem (altera DU e Pátio nas Eqs. 10--11), duplicação ferroviária (incrementa N_trens na Eq. 12). Cada incremento tem data de entrada em operação definida pelo PIT e deve ser recalculado via Eq. 13 para verificar se o gargalo se transfere.

Para cada horizonte e cenário, os parâmetros operacionais devem ser documentados em tabela de premissas, registrando o valor do ano-base e o valor adotado para cada horizonte (2030, 2040, 2050), com a justificativa da alteração. A tabela de premissas integra a memória de cálculo do Passo 11. A comparação entre capacidade atual e capacidade projetada é representada no gráfico especificado a seguir.

## 10.1.1. Incorporação de projetos de eficiência operacional nos cenários futuros

A Seção 10.1 define três categorias de intervenção que podem compor cenários futuros: ganhos de eficiência operacional, modernização de equipamentos e investimentos em infraestrutura física. As duas últimas alteram parâmetros de entrada cuja variação é diretamente quantificável (número de berços, área de armazenagem, capacidade nominal do equipamento). A primeira categoria, que inclui projetos de digitalização, VTMIS, agendamento eletrônico de portarias e automação de processos, exige procedimento específico porque o ganho depende da configuração operacional do terminal e não pode ser prescrito por faixa genérica.

O procedimento para incorporar projetos de eficiência operacional em cenários futuros tem três etapas.

Etapa 1, mapeamento do efeito sobre parâmetros. Cada projeto deve ser associado ao parâmetro específico da equação de capacidade que ele altera. Um sistema VTMIS com coordenação de manobras atua sobre H_nav (Eq. 1c) e sobre o tempo inoperante pré-operação (Inop.Pré, na decomposição do tempo atracado da Seção 3.9), porque melhora a coordenação entre prático, rebocador e berço, mas não altera a restrição física de maré ou calado. Um sistema de agendamento eletrônico de caminhões atua sobre a capacidade de portaria (parâmetros G e DU na Eq. 9) e sobre o tempo inoperante pós-operação (Inop.Pós), porque distribui o fluxo de veículos ao longo do dia e reduz o tempo de espera para liberação de carga. Automação de gates atua sobre o tempo de processamento por veículo (t_v) na Eq. 10. O analista deve registrar, para cada projeto, o parâmetro afetado e a equação correspondente.

Etapa 2, estimativa da variação do parâmetro. O valor da variação (redução de H_nav em horas, redução de Inop.Pré em horas, aumento de G em veículos/dia) deve ser obtido de uma entre três fontes, registrada na memória de cálculo: estudo de viabilidade específico do projeto, com modelagem do ganho para a configuração do terminal em análise; benchmark documentado de terminal com configuração comparável (geometria de canal, número de berços, volume de movimentação) onde a mesma tecnologia já opera em regime estável, com indicação da fonte, do período de referência e das condições de comparabilidade; ou simulação de eventos discretos calibrada com dados operacionais do terminal. O roteiro não prescreve faixas numéricas de ganho porque o efeito de cada tecnologia varia conforme a configuração do terminal, o nível de automação pré-existente e o grau de maturidade da implementação.

Etapa 3, recálculo e análise de sensibilidade. Com o parâmetro ajustado, recalcular C_cais, C_arm, CD ou C_hint conforme a equação afetada, e propagar o resultado para C_sistema = min(C_cais, C_arm, C_hint). Para cada projeto de eficiência, a análise deve incluir pelo menos dois cenários de implementação: um cenário conservador (ganho mínimo estimado) e um cenário otimista (ganho máximo estimado). A diferença entre os dois cenários no ano de saturação (A_sat) indica a sensibilidade da capacidade ao sucesso da implementação e permite dimensionar o risco associado a depender de ganhos de eficiência para postergar investimentos em infraestrutura física.

A tabela de premissas exigida na Seção 10.1 deve conter, para cada projeto de eficiência operacional, o nome do projeto, o horizonte de implementação, o parâmetro afetado, o valor no ano-base, o valor estimado após implementação (cenário conservador e otimista), e a fonte da estimativa.

## 10.2. Gráfico-modelo de evolução capacidade versus demanda

\[Nota técnica\] Recomendação: incluir variável de reordenamento espacial no gráfico-modelo de evolução da capacidade. Expansões de capacidade frequentemente exigem transição de layout (mudança de uso de berço, conversão de pátio, realocação de silos), e o período de transição pode causar redução temporária de capacidade. O modelo atual projeta crescimento monotônico, sem capturar esse efeito.

O confronto entre capacidade e demanda ao longo do horizonte de planejamento deve ser representado graficamente para cada perfil de carga relevante. O gráfico-modelo tem a seguinte especificação:

Eixo horizontal: anos de planejamento (ano-base, 2030, 2040 e 2050). A escala deve ser linear e os pontos coincidirem com os horizontes da Eq. 13.

Eixo vertical: **throughput anual em t/ano (ou TEU/ano para contêineres), com escala iniciada em zero e limite superior 20% acima do maior valor projetado.**

Séries obrigatórias: (a) Demanda projetada --- uma curva para cada cenário (baixo, referência e alto), obtidas do estudo de demanda; (b) Capacidade instalada atual --- linha horizontal do ano-base até a data de entrada do primeiro projeto do PIT; (c) Capacidade com projetos do PIT --- curva escalonada que incorpora cada incremento de capacidade na data prevista de operação do projeto.

Identificação do ano de saturação: marcar o ponto de interseção entre a curva de demanda do cenário de referência e a curva de capacidade instalada. Quando a demanda do cenário alto superar a capacidade antes de 2030, o ponto deve ser destacado e mencionado no texto do diagnóstico. O ano de saturação é definido como o primeiro ano em que a demanda projetada ultrapassa C_sistema calculada pela Eq. 13 sem considerar novos projetos.

Desagregação por subsistema: quando o elo restritivo for diferente do cais, incluir curva adicional representando a capacidade do subsistema limitante (C_arm ou C_hint) para evidenciar o ponto de transferência do gargalo após os investimentos previstos.

O gráfico deve ser produzido por perfil de carga e acompanhado de tabela-resumo com os valores numéricos das curvas, permitindo auditoria dos dados. O eixo de demanda usa as mesmas unidades do eixo de capacidade (t/ano ou TEU/ano). Qualquer conversão de unidades deve ser documentada na memória de cálculo.

Fonte: elaboração própria (valores ilustrativos).

**Figura 1:** Gráfico-modelo de evolução capacidade versus demanda.

*\[Gráfico ilustrativo de evolução capacidade versus demanda - ver documento original\]*

## 10.3. Confronto sistemático entre demanda projetada e capacidade estimada

O confronto entre demanda projetada e capacidade estimada constitui o procedimento central de integração entre os blocos analíticos do roteiro. Para cada perfil de carga relevante e para cada horizonte de planejamento (ano-base, 2030, 2040 e 2050), devem ser registrados lado a lado: (a) a demanda projetada obtida no estudo de demanda, nos três cenários definidos (baixo, referência e alto); e (b) a capacidade do sistema calculada pela Eq. 13, sem considerar novos investimentos. O resultado é uma matriz ano-por-carga que permite identificar em quais combinações perfil-horizonte a capacidade instalada será insuficiente para atender a demanda projetada.

O confronto deve ser organizado em tabela estruturada segundo o template do Quadro 25. Para cada linha, a taxa de ocupação u_t é calculada como u_t = D_t / C_sistema_t, onde D_t é a demanda do cenário de referência no horizonte t e C_sistema_t é a capacidade calculada pela Eq. 13. A classificação do resultado segue quatro faixas: Normal (u_t \< 0,80), Alerta (0,80 ≤ u_t \< 0,90), Crítico (0,90 ≤ u_t \< 1,00) e Saturação (u_t ≥ 1,00). Linhas classificadas como Alerta, Crítico ou Saturação exigem o tratamento descrito na seção seguinte.

## 10.3.1. Confronto sazonal para terminais de granéis agrícolas

Terminais que operam granéis agrícolas apresentam variação intra-anual de demanda que pode exceder a capacidade mensal do sistema mesmo quando a capacidade média anual é suficiente. A safra de soja concentra o escoamento entre março e junho, a segunda safra de milho entre julho e setembro, e a cana-de-açúcar entre abril e novembro. O confronto entre demanda e capacidade calculado apenas com parâmetros médios anuais não detecta a saturação que ocorre nesses períodos.

O procedimento de confronto sazonal segmenta a análise em dois regimes: meses de safra e meses de entressafra. A definição dos meses de safra deve ser feita a partir da série histórica de movimentação do terminal, identificando o intervalo contínuo que concentra pelo menos 60% da movimentação anual do perfil de carga j. Os meses restantes compõem a entressafra.

Para cada regime, os parâmetros de entrada dos Passos 2, 4 e 7 devem ser recalculados com os valores observados no período correspondente. No Passo 2 (capacidade de cais), o tempo atracado médio (Ta), o lote médio (Lm) e o BOR observado devem ser extraídos dos registros operacionais dos meses de safra, e não da média anual. No Passo 4 (capacidade de armazenagem), o dwell time efetivo (DT_ef) deve corresponder ao percentil 75 da distribuição observada nos meses de safra, porque a média subestima o tempo de permanência nos períodos de maior pressão sobre a retroárea. O fator de ocupação do piso (f_s) deve ser valorado com o percentil 90 dos meses de safra, refletindo a condição operacional de estresse. No Passo 7 (capacidade de hinterlândia), os volumes diários de chegada rodoviária e ferroviária devem corresponder à média dos meses de safra.

Com os parâmetros de safra, recalcular C_cais, C_arm, CD e C_hint para o período de pico. A capacidade em regime de safra (C_safra) é o menor valor entre esses subsistemas, calculado com os parâmetros do período de pico. A capacidade em regime de entressafra (C_entressafra) é calculada de forma análoga, com os parâmetros do período complementar.

O confronto sazonal compara a demanda mensal projetada (obtida pela distribuição da demanda anual segundo o perfil histórico de sazonalidade) com a C_safra mensal. O ano de saturação sazonal (A_sat_safra) é o primeiro ano em que a demanda projetada para os meses de safra excede a C_safra acumulada no mesmo intervalo. Esse ano pode anteceder o A_sat calculado com parâmetros médios anuais (Seção 10.4), e a diferença entre os dois indica o horizonte em que o terminal opera com gargalo sazonal sem gargalo estrutural permanente.

O Quadro 25 (confronto sistemático) deve incluir, para terminais de granéis agrícolas, uma linha adicional com a C_safra e o A_sat_safra. A memória de cálculo deve registrar os meses definidos como safra, os parâmetros recalculados para cada regime e a fonte dos dados utilizados na segmentação temporal.

**Quadro 25:** Template do confronto sistemático entre demanda projetada e capacidade estimada, com indicação de gatilhos de investimento

  -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  **Perfil de carga**     **Horizonte**   **D_t (t/ano ou TEU/ano)**   **C_sistema (t/ano ou TEU/ano)**   **u_t = D_t / C_sistema (%)**   **Indicação de gatilho**
  ----------------------- --------------- ---------------------------- ---------------------------------- ------------------------------- -------------------------------------------------------
  \[Perfil de carga j\]   2030            \[Estudo de demanda\]        \[Eq. 13\]                         \[Calcular\]                    Normal / Alerta (≥ 80%) / Crítico (≥ 90%) / Saturação

  \[Perfil de carga j\]   2040            \[Estudo de demanda\]        \[Eq. 13\]                         \[Calcular\]                    Normal / Alerta (≥ 80%) / Crítico (≥ 90%) / Saturação

  \[Perfil de carga j\]   2050            \[Estudo de demanda\]        \[Eq. 13\]                         \[Calcular\]                    Normal / Alerta (≥ 80%) / Crítico (≥ 90%) / Saturação
  -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

## 10.4. Ano de saturação: definição e identificação

O Ano de Saturação (A_sat) é definido como o primeiro ano em que a demanda projetada no cenário de referência ultrapassa a capacidade do sistema sem considerar novos investimentos: A_sat = min { t : D_t \> C_sistema_t }. Quando o confronto sistemático indica que D_t supera C_sistema_t dentro do horizonte de planejamento, A_sat deve ser registrado no relatório de diagnóstico e no gráfico-modelo do Passo 10. Se A_sat ocorre antes de 2030 para o cenário alto, a ocorrência deve ser destacada com anotação explícita no diagnóstico.

A identificação de A_sat deve ser realizada em duas etapas. A primeira toma a capacidade instalada atual como referência fixa (sem projetos), determinando o horizonte em que a demanda já supera a infraestrutura existente. A segunda incorpora os incrementos de capacidade previstos no PIT, com suas respectivas datas de entrada em operação, e verifica se e quando a saturação persiste mesmo após os investimentos planejados. Em ambos os casos, o subsistema que determina C_sistema pela Eq. 13 deve ser identificado para que o diagnóstico registre o elo restritivo associado ao ano de saturação.

## 10.5. Gatilhos de investimento e ações estruturantes

A metodologia adota dois níveis de gatilho de investimento, definidos em termos da taxa de ocupação u_t calculada pelo confronto sistemático. O primeiro nível, denominado Alerta, é ativado quando u_t atinge 80% da capacidade do sistema (u_t ≥ 0,80). Nesse patamar, o roteiro recomenda o início do planejamento de projetos de expansão: levantamento de estudos de viabilidade, consulta ao PDZ quanto à disponibilidade de áreas, e verificação de condicionantes licitárias e de licenciamento. O segundo nível, denominado Crítico, é ativado quando u_t atinge 90% da capacidade (u_t ≥ 0,90). Nesse patamar, a necessidade de expansão de capacidade deve ser tratada como urgente, com indicação de ações estruturantes para o planejamento do setor portuário.

Nos anos em que se verificar saturação operacional (u_t ≥ 1,00), a metodologia exige a indicação explícita da necessidade de realização de investimentos, com o objetivo de subsidiar a proposição de ações estruturantes e intervenções orientadas à manutenção dos níveis de serviço das operações e à adequada absorção da demanda projetada. A indicação deve especificar: (a) o subsistema limitante (cais, armazenagem ou hinterlândia), identificado pela Eq. 13; (b) o tipo de intervenção necessária, segundo os critérios do Quadro 24; e (c) o prazo mínimo de antecedência para maturação e implantação do projeto, considerando os ciclos de planejamento do PIT e do Plano Mestre.

### **10.5.1. Mapeamento de áreas disponíveis na poligonal como dado de entrada para cenários de expansão**

A definição de ações estruturantes nos anos de saturação (seção 10.5) depende da existência de espaço físico para expansão dentro da poligonal do porto organizado. Essa informação é produzida pelo macrocaderno de Governança, no tópico de exploração do espaço portuário, que identifica as áreas arrendadas, disponíveis, ociosas e exploradas indiretamente, bem como a situação contratual de cada uma.

O roteiro de capacidades deve incorporar esse levantamento como dado de entrada para os cenários de expansão. O procedimento consiste em: (a) obter do macrocaderno de Governança a relação de áreas disponíveis ou com contrato vencido ou em processo de relicitação dentro da poligonal; (b) classificar cada área por vocação de uso (armazenagem coberta, pátio de contêineres, tancagem, retroárea, terminal ferroviário), com base na localização, dimensões e infraestrutura existente; (c) estimar a capacidade adicional que cada área poderia gerar, aplicando os parâmetros de armazenagem da seção 5 (Eq. 4) ou de pátio da seção 5.3; e (d) verificar se a capacidade adicional estimada é suficiente para atender o déficit identificado pelo confronto demanda versus capacidade (seção 10.3).

Quando não houver áreas disponíveis dentro da poligonal em quantidade suficiente para suprir o déficit projetado, o estudo deve registrar essa restrição e indicar que a expansão de capacidade dependerá de: (a) intensificação do uso das áreas existentes (aumento de empilhamento, redução de dwell time, automação); (b) revisão do Plano de Desenvolvimento e Zoneamento (PDZ) para reclassificação de áreas; ou (c) alternativas externas à poligonal (retroportos, terminais intermodais, áreas de apoio logístico). Essa análise condiciona diretamente a viabilidade das ações listadas na seção 10.5 e deve constar do quadro de consolidação sistêmica (Quadro 5) como restrição espacial.

## 10.6. Capacidade como condicionante da captura de carga: relação com a competição portuária

A análise de demanda está fundamentada no conceito de competição portuária: os portos disputam fluxos logísticos com outros terminais e modos de transporte na mesma área de influência. Nesse contexto, a capacidade instalada não é apenas uma restrição física ao processamento de carga, mas um fator determinante da posição competitiva do porto. Um terminal que opera próximo à saturação perde flexibilidade competitiva: não consegue absorver desvios de carga provenientes de portos concorrentes, não é capaz de ampliar seu market share com novos embarcadores e passa a operar com níveis de serviço degradados que tendem a deslocar cargas sensíveis a prazo e confiabilidade para outros complexos portuários.

A metodologia deve estabelecer uma relação explícita entre capacidade instalada e tendência de limitação na captura de cargas. Para cada perfil de carga e horizonte de planejamento, a taxa de ocupação u_t calculada no confronto sistemático (Quadro 25) deve ser interpretada também como indicador de compressão da capacidade competitiva do porto: quando u_t se aproxima do limiar crítico (90%), o terminal perde margem para capturar carga adicional da área de influência, independentemente da demanda potencial existente. Esse efeito deve ser documentado no diagnóstico e integrado à justificativa dos investimentos propostos.

## 10.7. Perda potencial de carga em cenários de saturação

Quando a demanda projetada supera a capacidade instalada (u_t ≥ 1,00), o terminal não tem condições físicas de processar o volume excedente. O resultado direto é a perda efetiva de carga: embarcadores e operadores logísticos redirecionam seus fluxos para portos concorrentes com capacidade disponível. Uma vez estabelecidas essas rotas alternativas, a recuperação do market share perdido demanda tempo e investimento superiores ao necessário para a prevenção da saturação.

A metodologia exige a quantificação do volume de carga em risco em cada ano de saturação identificado. O volume potencial de perda por perfil de carga j e horizonte t é definido como: V_perda_jt = max(0, D_jt − C_sistema_jt), onde D_jt é a demanda projetada no cenário de referência e C_sistema_jt é a capacidade calculada pela Eq. 13 sem novos projetos. A agregação de V_perda por horizonte, convertida para toneladas equivalentes, fornece a base econômica para a priorização dos investimentos e para a mensuração do custo de não ampliar a capacidade. Esse valor deve ser registrado na memória de cálculo e apresentado no relatório de diagnóstico.

## 10.8. Expansão de capacidade e potencial de captura de fluxos logísticos

A expansão de capacidade produz dois efeitos sobre a captura de carga. O primeiro é defensivo: elimina a perda de movimentação nos anos de saturação, preservando o market share existente. O segundo é ofensivo: ao ampliar a capacidade antes que concorrentes saturem, o porto passa a disputar fluxos logísticos que ainda não estão alocados a nenhum terminal ou que estão sendo captados por portos com menor vantagem locacional. A magnitude desse efeito ofensivo depende da elasticidade competitiva dos fluxos na área de influência, estimada no estudo de demanda com base em modelos gravitacionais, de custo generalizado de transporte ou de preferência declarada de embarcadores.

Para subsidiar essa análise, a metodologia deve articular os resultados do confronto sistemático (Quadro 25) com as projeções de demanda potencial da área de influência. Especificamente, deve-se: (a) identificar o volume de demanda potencial não capturado pelo porto no ano-base (carga gerada na área de influência que escoa por outros terminais); (b) estimar a parcela adicional capútrável em cada horizonte de planejamento, condicionada à disponibilidade de capacidade; e (c) comparar, por cenário, o volume de captura potencial com e sem os investimentos previstos no PIT. Essa comparação traduz os projetos de expansão de infraestrutura em ganhos mensuráveis de movimentação, fortalecendo a justificativa de cada intervenção proposta.

# 11. Passo 11: Instrumentos operacionais e memória de cálculo

Os cálculos dos Passos 1 a 10 devem ser documentados em memória de cálculo estruturada, composta por planilhas eletrônicas (formato .xlsx) reprodutíveis a partir das bases de dados primários. A memória de cálculo tem dupla função: registrar os procedimentos de forma auditada e produzir automaticamente os indicadores que alimentam o Quadro 5 e o gráfico-modelo do Passo 10. A estrutura de referência compreende: (a) base bruta de atracações, (b) indicadores operacionais calculados por grupo e (c) tabela de capacidades por berço e perfil de carga.

## 11.1. Base de dados primária

Fonte: estatístico Aquaviário da ANTAQ, disponibilizado em formato tabular com registro individual por atracação. A base padrão de insumos é composta por dois arquivos:

**(a) Base de cargas não conteinerizadas** --- contém registros de granéis sólidos vegetais, granéis sólidos minerais, granéis líquidos e carga geral, com movimentação em toneladas (t). Para o ano-base de 2024, a base da ANTAQ reúne 121.071 atracacões em 39 complexos portuários, organizadas em 20 colunas: Ano, Complexo Portuário, Nome da Instalação, Nome do Terminal, Tipo de Terminal, Berço, Navegação da Atracacão, Número de Atracacão, IMO da Embarcação, Número de Capitania, Data da Chegada, Data da Atracacão, Data do Início da Operação, Data do Término da Operação, Data da Desatracação, Perfil da Carga, Nomenclatura Simplificada, Tipo de Operação de Carga, Sentido e Total de Movimentação Portuária (t). Os cinco campos de timestamp permitem calcular os tempos operacionais definidos no Passo 1.

**(b) Base de cargas conteinerizadas** --- exclusivamente carga conteinerizada, com movimentação em TEU (Twenty-foot Equivalent Unit). Para 2024, a base reúne 31.543 atracacões em 19 complexos portuários. A estrutura de colunas é idêntica à da base não conteinerizada, com a última coluna substituindo toneladas por TEU. Esta base demanda tratamento adicional de replicatas antes do cálculo de indicadores.

## 11.2. Estrutura da memória de cálculo

A memória de cálculo é organizada em três planilhas sequenciais, geradas a partir de código Python reprodutível:

Planilha 1: Base depurada: resultado do tratamento de replicatas e do cálculo dos tempos operacionais (Passo 1). Cada linha corresponde a uma atracação consolidada. Colunas adicionais calculadas: Inop.Pré (h), T_op (h), Inop.Pós (h), Line-up (h) e Produtividade (t/h ou TEU/h). Registros com T_op nulo ou negativo são descartados e documentados em log.

Planilha 2: Indicadores operacionais: resultado da depuração estatística por IQR e do cálculo dos indicadores agregados (Passo 1, Passo 2). Uma linha por grupo (terminal, berço, perfil de carga, sentido, navegação). Colunas: Q1 e Q3 para cada variável depurada, limites L_inf e L_sup, número de observações totais e número de observações retidas, média depurada de Inop.Pré, média depurada de Produtividade, média depurada de Inop.Pós, lote médio (Lm) e T_op recalculado (Lm / Produtividade média depurada).

Planilha 3: Capacidades calculadas: resultado do cálculo de capacidade pela Eq. 1b, da alocação por mix e do cálculo do BOR e BUR (Passo 2). Uma linha por grupo. Colunas: Ta (Inop.Pré + T_op + Inop.Pós), clearance fixo (a = 3,0 h), tempo por navio (Ta + a), BOR_adm (selecionado automaticamente por perfil de carga × número de berços, conforme mapa do Quadro 17 do roteiro; fallback de 0,80 para perfis não mapeados), BOR_adm fonte (rastreabilidade: \"Quadro 17 (UNCTAD)\" ou \"Fallback 0,80\"), capacidade bruta pela Eq. 1b, T_total(j) por perfil de carga, fração f(j), capacidade alocada C(j), BOR observado (Eq. 2a) e BUR observado (Eq. 2b). Os valores da Planilha 3 alimentam diretamente o Quadro 5.

## 11.3. Códigos de cálculo

Os cálculos das três planilhas devem ser implementados em código Python reprodutível, estruturado em três funções principais:

**tratamento_base(**): lê a base bruta da ANTAQ, aplica o tratamento de replicatas, calcula os cinco tempos operacionais e descarta registros inválidos. Retorna a Planilha 1.

**tabela_indicadores_operacionais(**): recebe a Planilha 1, agrupa os registros por (terminal, berço, perfil de carga, sentido, navegação), aplica a depuração por IQR às três variáveis e calcula os indicadores agrupados. Retorna a Planilha 2.

tabela_capacidades_calc(): recebe a Planilha 2 e o parâmetro externo clearance (padrão de 3,0 h), calcula a capacidade bruta pela Eq. 1b, realiza a alocação por mix e calcula BOR e BUR. O BOR_adm é determinado automaticamente para cada grupo pela função get_bor_adm(), que consulta o mapa BOR_ADM_MAPA (perfil de carga × número de berços) alinhado ao Quadro 17 do roteiro, com fallback de 0,80 para perfis não mapeados; o valor aplicado e a fonte são registrados na Planilha 3 para rastreabilidade. Retorna a Planilha 3. Para a base conteinerizada, a função utiliza get_bor_adm_cont() com mapa BOR_ADM_CONT_MAPA diferenciado por número de berços (0,50 para 1 berço, 0,65 para 2--3 berços, 0,70 para 4+ berços, conforme Quadro 17), e inclui etapa prévia de tratamento de replicatas por IMO e timestamps.

Instruções de execução: os códigos devem ser executados separadamente para a base de cargas não conteinerizadas e para a base conteinerizada. Os arquivos de saída (Planilhas 2 e 3) são insumos diretos para o preenchimento do Quadro 5 e para a construção do gráfico-modelo do Passo 10. O registro de todas as etapas de depuração (quantidades descartadas, limites IQR por grupo) deve ser exportado para log estruturado como parte integrante da memória de cálculo.

## 11.4. Referências

ANTAQ -- AGÊNCIA NACIONAL DE TRANSPORTES AQUAVIÁRIOS. Estatístico aquaviário. Brasília: ANTAQ, 2024.

ANTAQ. Proposição de valores referenciais remuneratórios para áreas arrendáveis. Brasília: ANTAQ, 2020b.

ANTAQ. Resolução n.º 2.240, de 4 de outubro de 2011. Brasília: ANTAQ, 2011.

BRASIL. Empresa de Planejamento e Logística (EPL). Plano Nacional de Logística Portuária. Brasília: EPL, 2022.

GOLDRATT, E. M.; COX, J. A meta: um processo de melhoria contínua. São Paulo: Nobel, 2002.

PIANC. Harbour approach channels: design guidelines. Report n.º 121. Bruxelas: PIANC, 2014.

TRB -- TRANSPORTATION RESEARCH BOARD. *Highway Capacity Manual*. 6. ed. Washington D.C.: TRB, 2016.

UNCTAD. Port development: a handbook for planners in developing countries. 2. ed. Genève: UNCTAD, 1985.

WORLD BANK. Port reform toolkit. 2. ed. Washington D.C.: World Bank, 2007.

# 12. Glossário de termos técnicos e siglas

O glossário reúne os principais termos técnicos e siglas empregados neste roteiro, com suas definições operacionais e referência às equações ou seções em que são utilizados.

Correspondência com a nomenclatura do PNL: as nomenclaturas de grupos de carga utilizadas neste roteiro seguem a classificação operacional do Estatístico Aquaviário da ANTAQ. A correspondência com os grupos do Plano Nacional de Logística (PNL/PNLP) é a seguinte: granel sólido vegetal → Commodities Agrícolas (PNL); granel sólido mineral → Commodities Minerais (PNL); granel líquido → Combustíveis e Derivados (PNL); carga geral → Manufaturados e Semimanufaturados (PNL); contêineres → Carga Conteinerizada (PNL). Estudos que utilizem projeções de demanda do PNL devem adotar a nomenclatura do Plano ou registrar explicitamente a correspondência na memória de cálculo.

**Quadro 11:** Glossário de termos técnicos e siglas

  -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  **Termo / Sigla**                             **Definição**
  --------------------------------------------- ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  *a (clearance)*                               Intervalo mínimo entre atracacões consecutivas no mesmo berço, medido em horas. Padrão de referência: 3,0 h na ausência de dado específico do terminal.

  ANTAQ                                         Agência Nacional de Transportes Aquários. Órgão regulador do setor portuário brasileiro, responsável pelo Estatístico Aquaviário.

  AP                                            Autoridade portuária. Entidade responsável pela administração do porto organizado.

  BOR (Berth Occupancy Rate)                    Taxa de ocupação do berço: fração das horas efetivas em que o berço esteve ocupado por uma embarcação em operação de carga. Indicador de nível de utilização e de pressão sobre a capacidade.

  BOR_adm                                       Taxa de ocupação admissível: valor máximo de BOR compativel com nível de serviço aceitável, derivado de modelos de teoria das filas. Determina a capacidade teórica máxima via Eq. 1b.

  BUR (Berth Utilization Rate)                  Taxa de utilização do berço em relação à capacidade teórica calculada: BUR = movimentação observada / C_cais. Indica a margem de folga operacional.

  C_arm                                         Capacidade de armazenagem do terminal, igual à capacidade dinâmica de movimentação (CD) calculada pela Eq. 5. Expressa em t/ano ou TEU/ano.

  C_cais                                        *Capacidade teórica do cais: throughput máximo que os berços podem processar no período de análise, calculado pelas Eqs. 1a ou 1b. Expressa em t/ano ou TEU/ano.*

  C_hint                                        Capacidade de hinterlândia: volume máximo de carga que o sistema de acesso terrestre (rodovias + ferrovias) pode absorver ou distribuir no período. C_hint = C_rod + C_fer (Eq. 8).

  C_sistema                                     Capacidade sistêmica: throughput máximo efetivo do porto, determinado pelo elo mais restritivo. C_sistema(j,t) = min(C_cais, C_arm, C_hint) para o perfil de carga j no horizonte t (Eq. 13).

  CE                                            Capacidade estática de armazenagem: volume de carga que o sistema de armazenagem comporta simultaneamente, calculado pela Eq. 4. Expressa em t ou TEU.

  CD                                            Capacidade dinâmica de movimentação: throughput anual do sistema de armazenagem, obtido relacionando CE com o giro de estoque (Eq. 5). Expressa em t/ano ou TEU/ano.

  CEU (Car Equivalent Unit)                     Unidade padrão de veículo para operações Ro-Ro. Converte categorias heterogêneas de veículos em unidade equivalente ao automóvel convencional: 1 automóvel = 1 CEU; 1 ônibus = 3 CEU; 1 caminhão pesado = 4 CEU.

  DOA                                           Dias de ocupação média por rotação de estoque: tempo médio de permanência da carga no sistema de armazenagem (armazém ou pátio), expresso em dias.

  DT                                            Dias totais do período de análise: 365 dias para análise anual; 91 ou 92 dias para análise trimestral.

  H_cal                                         Horas do calendário: 8.760 h/ano para anos não bisiestos.

  H_ef                                          Horas operacionais efetivas: horas do calendário descontados todos os períodos de indisponibilidade do berço (H_ef = H_cal − H_cli − H_mnt − H_nav − H_out). Parâmetro base das Eqs. 1a e 1b (Eq. 1c).

  IQR (Interquartile Range)                     Amplitude interquartílica: diferença entre o terceiro quartil (Q3) e o primeiro quartil (Q1) de uma distribuição. Usada neste roteiro como critério de filtragem de outliers nos indicadores operacionais do Estatístico ANTAQ.

  Lm                                            Lote médio por atracação: carga movimentada por escala, em toneladas ou TEU. Calculado como média do grupo após exclusão de replicatas e filtragem por IQR (Planilha 2).

  LOA (Length Overall)                          Comprimento total da embarcação, de proa a popa, em metros. Determina a ocupação de berços adjacentes em operações de cruzeiro (Passo 3).

  LOS (Level of Service)                        Nível de serviço de uma via rodoviária, classificado de A (fluxo livre) a F (colapso de tráfego), conforme o *Highway Capacity Manual* (TRB, 2016). Usado na análise de hinterlândia rodoviária (Passo 7).

  PDZ (Plano de Desenvolvimento e Zoneamento)   Instrumento de planejamento do porto organizado que define o uso do solo e os projetos de expansão da área portuária. Fonte de dados de área de armazenagem, leiaute e investimentos previstos.

  PIT (Programa de Investimentos do Terminal)   Conjunto de projetos de expansão ou modernização previstos para o terminal, com cronograma e capacidade incremental. Base para a projeção de capacidade futura no Passo 10.

  PNLP                                          Plano Nacional de Logística Portuária. Documento de planejamento do setor portuário brasileiro que reúne projeções de demanda por commodity e por porto.

  Ta (berth time)                               Tempo médio de permanência da embarcação no berço, em horas: Ta = Inop.Pré + T_op + Inop.Pós. Calculado a partir dos timestamps do Estatístico ANTAQ e depurado por IQR (Planilha 2).

  TEU (Twenty-foot Equivalent Unit)             Unidade padrão de contêiner de 20 pés. Fator de conversão: 1,40--1,65 TEU por caixa, calibrado com o Estatístico ANTAQ (Quadro 8).

  ToC (Theory of Constraints)                   Teoria das Restrições: abordagem de gestão sistêmica que identifica o elo mais restritivo de um processo como determinante do desempenho global. Base conceitual da Eq. 13 (C_sistema = mínimo dos subsistemas).

  T_op                                          Tempo de operação efetiva: período entre o início e o término da operação de carga ou descarga, em horas. Calculado como Data do Término da Operação menos Data do Início da Operação (Estatístico ANTAQ).

  V/C (Volume/Capacidade)                       Razão entre o volume de tráfego e a capacidade da via rodoviária. Indicador de saturação da infraestrutura de acesso. Usado na análise de hinterlândia (Passo 7); V/C \> 0,85 caracteriza proxímidade ao nível de serviço E/F.
  -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Fonte: elaboração própria.
