"""
Multiplicadores nacionais do setor de Transporte, Armazenagem e Correios
com ajuste regional via quocientes locacionais.

Ponto de partida: MIP Brasil 2015 (IBGE), 12 setores, calculada por
Vale & Perobelli (2020). Os multiplicadores nacionais sao ajustados
para cada municipio usando quocientes locacionais (QL) derivados de
dados RAIS (emprego formal).

Fundamentacao:
    - Miller, R.E. & Blair, P.D. (2009). Input-Output Analysis, cap. 3 e 8.
    - Vale, V.A. & Perobelli, F.S. (2020). Analise de Insumo-Produto no R.
    - Guilhoto, J.J.M. & Sesso Filho, U.A. (2005). Estimacao da MIP.
    - Flegg, A.T. et al. (1995). On the appropriate use of location
      quotients. Regional Studies, 29(6), 547-561.
    - Round, J.I. (1983). Nonsurvey techniques: a critical review.
      International Regional Science Review, 8(3), 189-212.
    - Wozniak & Andrade Junior (2023). TCC Paranagua: framework de
      impacto portuario.

Dados de referencia extraidos de:
    Vale & Perobelli (2020), tabelas de multiplicadores, MIP IBGE 2015.
    Setor: "Transp" = Transporte, Armazenagem e Correios.
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Optional, Dict, Tuple
from enum import Enum
import logging

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 1. Constantes: multiplicadores nacionais (MIP Brasil 2015, IBGE)
# ---------------------------------------------------------------------------
# Fonte: Vale & Perobelli (2020), tabelas de multiplicadores.
# Setor "Transp" = Transporte, Armazenagem e Correios.
# Nomenclatura segue o livro: MP/MPT/MPTT, ME/MEI/MET/MEII, MR/MRI/MRT/MRII.


@dataclass(frozen=True)
class NationalProductionMultipliers:
    """Multiplicadores de producao (output) do setor Transporte.

    MP:   simples (modelo aberto, R$ total / R$ demanda final).
    MPT:  total (modelo fechado, inclui efeito induzido).
    MPTT: total truncado (modelo fechado, apenas n setores produtivos).

    Interpretacao do MP: uma variacao de R$1 na demanda final do setor
    gera R$1.84 de produto na economia (direto + indireto).
    """
    simple: float = 1.840288       # MP
    total: float = 4.143630        # MPT
    total_truncated: float = 3.371404  # MPTT


@dataclass(frozen=True)
class NationalEmploymentMultipliers:
    """Multiplicadores de emprego do setor Transporte.

    ME:   simples (empregos / R$ 1.000.000 de demanda final).
    MEI:  tipo I (empregos totais / emprego direto, modelo aberto).
    MET:  total truncado (empregos / R$ 1.000.000, modelo fechado).
    MEII: tipo II (empregos totais / emprego direto, modelo fechado).

    Interpretacao do MEI: para cada emprego direto no setor Transporte,
    geram-se 1.83 empregos na economia (direto + indireto).
    Interpretacao do MEII: incluindo efeito induzido, geram-se 3.43.
    """
    simple: float = 17.071567      # ME (por R$ 1.000.000)
    type_i: float = 1.827595       # MEI
    total_truncated: float = 32.046902  # MET (por R$ 1.000.000)
    type_ii: float = 3.430779      # MEII


@dataclass(frozen=True)
class NationalIncomeMultipliers:
    """Multiplicadores de renda do setor Transporte.

    MR:   simples (R$ renda / R$ demanda final, modelo aberto).
    MRI:  tipo I (renda total / renda direta, modelo aberto).
    MRT:  total truncado (R$ renda / R$ demanda final, modelo fechado).
    MRII: tipo II (renda total / renda direta, modelo fechado).

    Interpretacao do MR: uma variacao de R$1 na demanda final do setor
    gera R$0.44 de renda na economia.
    """
    simple: float = 0.443788       # MR
    type_i: float = 1.706910       # MRI
    total_truncated: float = 0.772226  # MRT
    type_ii: float = 2.970155      # MRII


# Tabela completa dos 12 setores (para referencia e validacao).
# Cada entrada: (MP, MPT, MPTT)
NATIONAL_PRODUCTION_ALL_SECTORS = {
    "Agro":       (1.719044, 2.959997, 2.543951),
    "Ind.Extr":   (1.771649, 3.328518, 2.806557),
    "Ind.Tran":   (2.147529, 4.051231, 3.412990),
    "SIUP":       (1.947655, 3.344608, 2.876261),
    "Cons":       (1.811262, 3.693084, 3.062178),
    "Com":        (1.532739, 3.780823, 3.027123),
    "Transp":     (1.840288, 4.143630, 3.371404),
    "Info":       (1.640565, 3.708278, 3.015050),
    "Finan":      (1.492315, 3.463977, 2.802952),
    "Imob":       (1.110196, 1.309140, 1.242441),
    "Otrs.Serv":  (1.533751, 4.052431, 3.208010),
    "Adm":        (1.383516, 5.306243, 3.991097),
}

# Cada entrada: (ME, MEI, MET, MEII)
NATIONAL_EMPLOYMENT_ALL_SECTORS = {
    "Agro":       (34.101037, 1.242638, 42.169181, 1.536640),
    "Ind.Extr":   (8.451915,  7.658824, 18.574004, 16.831101),
    "Ind.Tran":   (15.374493, 3.806716, 27.751536, 6.871265),
    "SIUP":       (8.348028,  3.987779, 17.430413, 8.326354),
    "Cons":       (21.242773, 1.554648, 33.477565, 2.450048),
    "Com":        (22.473178, 1.310717, 37.089247, 2.163178),
    "Transp":     (17.071567, 1.827595, 32.046902, 3.430779),
    "Info":       (10.674351, 2.771608, 24.117726, 6.262196),
    "Finan":      (6.687006,  3.202383, 19.505899, 9.341304),
    "Imob":       (1.560459,  2.042665, 2.853904,  3.735805),
    "Otrs.Serv":  (26.034161, 1.264451, 42.409532, 2.059785),
    "Adm":        (13.211106, 1.428829, 38.714983, 4.187166),
}

# Cada entrada: (MR, MRI, MRT, MRII)
NATIONAL_INCOME_ALL_SECTORS = {
    "Agro":       (0.239096, 2.297985, 0.416046, 3.998671),
    "Ind.Extr":   (0.299964, 2.383660, 0.521961, 4.147752),
    "Ind.Tran":   (0.366789, 2.586250, 0.638241, 4.500275),
    "SIUP":       (0.269153, 2.643962, 0.468347, 4.600697),
    "Cons":       (0.362573, 1.810757, 0.630906, 3.150856),
    "Com":        (0.433142, 1.383320, 0.753700, 2.407084),
    "Transp":     (0.443788, 1.706910, 0.772226, 2.970155),
    "Info":       (0.398389, 1.715025, 0.693228, 2.984276),
    "Finan":      (0.379883, 1.523879, 0.661026, 2.651667),
    "Imob":       (0.038331, 3.117216, 0.066698, 5.424196),
    "Otrs.Serv":  (0.485278, 1.344106, 0.844421, 2.338848),
    "Adm":        (0.755798, 1.144139, 1.315146, 1.990890),
}


TRANSPORT_PRODUCTION = NationalProductionMultipliers()
TRANSPORT_EMPLOYMENT = NationalEmploymentMultipliers()
TRANSPORT_INCOME = NationalIncomeMultipliers()


# ---------------------------------------------------------------------------
# 2. Quociente Locacional (QL)
# ---------------------------------------------------------------------------

class QLMethod(Enum):
    """Metodos de calculo do quociente locacional."""
    SIMPLE = "simple"      # QL classico (Round, 1983)
    CILQ = "cilq"          # Cross-Industry LQ
    FLQ = "flq"            # Flegg LQ (Flegg et al., 1995)


def compute_location_quotient(
    employment_sector_region: float,
    employment_total_region: float,
    employment_sector_national: float,
    employment_total_national: float,
    method: QLMethod = QLMethod.SIMPLE,
    flq_delta: float = 0.3,
) -> float:
    """Calcula o quociente locacional de um setor para uma regiao.

    O QL mede a concentracao relativa de um setor na regiao comparado
    ao padrao nacional. Se QL >= 1, a regiao e relativamente
    especializada naquele setor (Miller & Blair, 2009, eq. 3.24).

    Args:
        employment_sector_region: emprego no setor na regiao.
        employment_total_region: emprego total na regiao.
        employment_sector_national: emprego no setor no pais.
        employment_total_national: emprego total no pais.
        method: metodo de calculo (SIMPLE, CILQ, FLQ).
        flq_delta: parametro delta do FLQ (Flegg et al., 1995).
            Valores tipicos: 0.1 a 0.5. Flegg sugere ~0.3.

    Returns:
        Valor do QL. QL >= 1 indica concentracao regional.

    Raises:
        ValueError: se algum denominador for zero.
    """
    if employment_total_region <= 0 or employment_total_national <= 0:
        raise ValueError("Emprego total deve ser positivo.")
    if employment_sector_national <= 0:
        raise ValueError("Emprego setorial nacional deve ser positivo.")

    share_region = employment_sector_region / employment_total_region
    share_national = employment_sector_national / employment_total_national

    if share_national == 0:
        return 0.0

    slq = share_region / share_national

    if method == QLMethod.SIMPLE:
        return slq

    if method == QLMethod.FLQ:
        # FLQ = SLQ * lambda, onde lambda = [log2(1 + E_R/E_N)]^delta
        # Corrige o vies do SLQ para regioes pequenas.
        relative_size = employment_total_region / employment_total_national
        lambda_flq = (np.log2(1 + relative_size)) ** flq_delta
        return slq * lambda_flq

    # CILQ nao e aplicavel para um unico setor; requer par de setores.
    # Retorna SLQ como fallback.
    return slq


def compute_ql_from_rais(
    rais_df: pd.DataFrame,
    region_code: str,
    sector_cnae_prefix: str = "49,50,51,52,53",
    year: Optional[int] = None,
    method: QLMethod = QLMethod.SIMPLE,
    flq_delta: float = 0.3,
) -> float:
    """Calcula QL do setor Transporte para um municipio usando dados RAIS.

    Espera um DataFrame com colunas: id_municipio, cnae_2 (ou
    cnae_2_subclasse), vinculo_ativo (ou qtd_vinculos).

    O setor "Transporte, Armazenagem e Correios" na CNAE 2.0 corresponde
    as divisoes 49-53 (secao H).

    Args:
        rais_df: DataFrame com microdados RAIS.
        region_code: codigo IBGE do municipio (7 digitos).
        sector_cnae_prefix: divisoes CNAE separadas por virgula.
            Padrao "49,50,51,52,53" = secao H completa.
        year: ano de referencia (filtra se informado).
        method: metodo QL.
        flq_delta: parametro FLQ.

    Returns:
        QL do setor Transporte no municipio.
    """
    df = rais_df.copy()

    # Identificar colunas
    emp_col = "vinculo_ativo" if "vinculo_ativo" in df.columns else "qtd_vinculos"
    mun_col = "id_municipio" if "id_municipio" in df.columns else "municipio"
    cnae_col = "cnae_2" if "cnae_2" in df.columns else "cnae_2_subclasse"

    if year is not None and "ano" in df.columns:
        df = df[df["ano"] == year]

    # Prefixos CNAE do setor Transporte
    prefixes = [p.strip() for p in sector_cnae_prefix.split(",")]

    def is_transport(cnae_val):
        cnae_str = str(cnae_val).replace("-", "").replace(".", "")[:2]
        return cnae_str in prefixes

    df["is_transport"] = df[cnae_col].apply(is_transport)

    # Emprego regional
    region_df = df[df[mun_col].astype(str).str.startswith(str(region_code))]
    emp_sector_region = region_df.loc[region_df["is_transport"], emp_col].sum()
    emp_total_region = region_df[emp_col].sum()

    # Emprego nacional
    emp_sector_national = df.loc[df["is_transport"], emp_col].sum()
    emp_total_national = df[emp_col].sum()

    if emp_total_region == 0 or emp_total_national == 0:
        logger.warning(
            f"Emprego zero para regiao {region_code}. "
            "Retornando QL=0."
        )
        return 0.0

    ql = compute_location_quotient(
        emp_sector_region,
        emp_total_region,
        emp_sector_national,
        emp_total_national,
        method=method,
        flq_delta=flq_delta,
    )

    logger.info(
        f"QL({method.value}) para {region_code}: {ql:.4f} "
        f"(emp_setor_reg={emp_sector_region:,.0f}, "
        f"emp_total_reg={emp_total_region:,.0f})"
    )
    return ql


# ---------------------------------------------------------------------------
# 3. Ajuste regional dos multiplicadores
# ---------------------------------------------------------------------------

class AdjustmentMethod(Enum):
    """Estrategias de ajuste do multiplicador nacional."""
    LINEAR = "linear"          # QL direto como escalar (Miller & Blair)
    DAMPED = "damped"          # QL com amortecimento logaritmico
    CAPPED_LINEAR = "capped"   # QL linear com teto


@dataclass
class RegionalMultiplierResult:
    """Resultado do ajuste regional de multiplicadores.

    Atributos:
        region_code: codigo IBGE do municipio.
        ql: quociente locacional calculado.
        ql_method: metodo usado para o QL.
        adjustment_factor: fator de ajuste aplicado.
        adjustment_method: metodo de ajuste.

        production_type_i: multiplicador de producao tipo I ajustado.
        production_type_ii: multiplicador de producao tipo II ajustado.
        employment_type_i: multiplicador de emprego tipo I ajustado.
        employment_type_ii: multiplicador de emprego tipo II ajustado.
        income_type_i: multiplicador de renda tipo I ajustado.
        income_type_ii: multiplicador de renda tipo II ajustado.

        national_ref: dicionario com os valores nacionais usados.
        notes: observacoes sobre limitacoes ou avisos.
    """
    region_code: str
    ql: float
    ql_method: str
    adjustment_factor: float
    adjustment_method: str

    production_type_i: float
    production_type_ii: float
    employment_type_i: float
    employment_type_ii: float
    income_type_i: float
    income_type_ii: float

    national_ref: Dict[str, float] = field(default_factory=dict)
    notes: str = ""


def _compute_adjustment_factor(
    ql: float,
    method: AdjustmentMethod = AdjustmentMethod.CAPPED_LINEAR,
    cap: float = 2.5,
    damping_base: float = 2.0,
) -> float:
    """Calcula o fator de ajuste a partir do QL.

    Tres estrategias:

    LINEAR (Miller & Blair, 2009, eq. 3.25):
        Se QL < 1: fator = QL (reduz proporcionalmente).
        Se QL >= 1: fator = 1.0 (mantem nacional).
        Problema: nao diferencia QL=1.1 de QL=5.0.

    CAPPED_LINEAR:
        Se QL < 1: fator = QL.
        Se QL >= 1: fator = min(QL, cap).
        Permite que regioes muito especializadas tenham
        multiplicadores acima do nacional, com teto.

    DAMPED:
        Se QL < 1: fator = QL.
        Se QL >= 1: fator = 1.0 + log_base(QL).
        Crescimento sub-linear para QLs altos.

    Args:
        ql: quociente locacional.
        method: estrategia de ajuste.
        cap: teto para CAPPED_LINEAR.
        damping_base: base do logaritmo para DAMPED.

    Returns:
        Fator multiplicativo (>0).
    """
    if ql <= 0:
        return 0.0

    if method == AdjustmentMethod.LINEAR:
        return min(ql, 1.0)

    if method == AdjustmentMethod.CAPPED_LINEAR:
        return min(ql, cap)

    if method == AdjustmentMethod.DAMPED:
        if ql < 1.0:
            return ql
        return 1.0 + np.log(ql) / np.log(damping_base)

    return min(ql, 1.0)


def adjust_multipliers(
    ql: float,
    region_code: str = "",
    adjustment_method: AdjustmentMethod = AdjustmentMethod.CAPPED_LINEAR,
    cap: float = 2.5,
    ql_method: str = "simple",
) -> RegionalMultiplierResult:
    """Ajusta os multiplicadores nacionais para uma regiao.

    O procedimento e:
    1. Calcular fator de ajuste a partir do QL.
    2. Para multiplicadores tipo I (direto + indireto):
       mult_regional = 1.0 + (mult_nacional - 1.0) * fator.
       O "1.0" e o efeito direto, que nao varia com a regiao.
       O restante (efeito indireto) e escalado pelo fator.
    3. Para multiplicadores tipo II (direto + indireto + induzido):
       O efeito induzido tambem e escalado, mas com fator ligeiramente
       menor (regioes pequenas vazam mais renda para consumo externo).

    Essa formulacao garante que:
    - O multiplicador regional nunca fica abaixo de 1.0.
    - Regioes com QL=1.0 recebem o multiplicador nacional.
    - Regioes com QL<1 recebem multiplicadores menores.
    - Regioes muito especializadas (QL>>1) recebem multiplicadores
      maiores, com amortecimento.

    Args:
        ql: quociente locacional do setor Transporte na regiao.
        region_code: codigo IBGE (para logging).
        adjustment_method: estrategia de ajuste.
        cap: teto para CAPPED_LINEAR.
        ql_method: nome do metodo QL usado (para registro).

    Returns:
        RegionalMultiplierResult com todos os multiplicadores ajustados.
    """
    factor = _compute_adjustment_factor(ql, adjustment_method, cap)

    # O fator para o efeito induzido e menor que para o indireto,
    # porque o consumo das familias em regioes menores vaza mais
    # para fora da regiao. Usamos fator^0.7 como proxy.
    # Referencia: Round (1983) discute o "leakage bias" de QLs
    # para efeitos induzidos.
    induced_factor = factor ** 0.7

    # --- Producao ---
    nat_prod = TRANSPORT_PRODUCTION
    # Tipo I: efeito indireto = MP - 1.0
    indirect_prod = (nat_prod.simple - 1.0) * factor
    prod_type_i = 1.0 + indirect_prod

    # Tipo II: efeito indireto + efeito induzido
    # Induzido = MPTT - MP
    induced_prod = (nat_prod.total_truncated - nat_prod.simple) * induced_factor
    prod_type_ii = prod_type_i + induced_prod

    # --- Emprego ---
    nat_emp = TRANSPORT_EMPLOYMENT
    # Tipo I: efeito indireto = MEI - 1.0
    indirect_emp = (nat_emp.type_i - 1.0) * factor
    emp_type_i = 1.0 + indirect_emp

    # Tipo II: induzido = MEII - MEI
    induced_emp = (nat_emp.type_ii - nat_emp.type_i) * induced_factor
    emp_type_ii = emp_type_i + induced_emp

    # --- Renda ---
    nat_inc = TRANSPORT_INCOME
    indirect_inc = (nat_inc.type_i - 1.0) * factor
    inc_type_i = 1.0 + indirect_inc

    induced_inc = (nat_inc.type_ii - nat_inc.type_i) * induced_factor
    inc_type_ii = inc_type_i + induced_inc

    # Notas
    notes_parts = []
    if ql < 0.5:
        notes_parts.append(
            "QL baixo (<0.5): regiao pouco especializada em transporte. "
            "Multiplicadores regionais podem estar subestimados se houver "
            "atividade portuaria informal nao captada pela RAIS."
        )
    if ql > 3.0:
        notes_parts.append(
            f"QL alto (>{ql:.1f}): economia muito concentrada no setor. "
            "Os multiplicadores ajustados podem superestimar o efeito "
            "real se a regiao importar grande parte dos insumos."
        )

    result = RegionalMultiplierResult(
        region_code=region_code,
        ql=ql,
        ql_method=ql_method,
        adjustment_factor=factor,
        adjustment_method=adjustment_method.value,
        production_type_i=round(prod_type_i, 6),
        production_type_ii=round(prod_type_ii, 6),
        employment_type_i=round(emp_type_i, 6),
        employment_type_ii=round(emp_type_ii, 6),
        income_type_i=round(inc_type_i, 6),
        income_type_ii=round(inc_type_ii, 6),
        national_ref={
            "production_type_i_national": nat_prod.simple,
            "production_type_ii_national": nat_prod.total_truncated,
            "employment_type_i_national": nat_emp.type_i,
            "employment_type_ii_national": nat_emp.type_ii,
            "income_type_i_national": nat_inc.type_i,
            "income_type_ii_national": nat_inc.type_ii,
            "source": "Vale & Perobelli (2020), MIP IBGE 2015",
        },
        notes="; ".join(notes_parts) if notes_parts else "",
    )

    logger.info(
        f"Multiplicadores ajustados para {region_code}: "
        f"QL={ql:.3f}, fator={factor:.3f}, "
        f"prod_I={prod_type_i:.3f}, prod_II={prod_type_ii:.3f}, "
        f"emp_I={emp_type_i:.3f}, emp_II={emp_type_ii:.3f}"
    )

    return result


# ---------------------------------------------------------------------------
# 4. Decomposicao direto / indireto / induzido
# ---------------------------------------------------------------------------

@dataclass
class ImpactDecomposition:
    """Decomposicao de um impacto em direto, indireto e induzido.

    Uso:
        total = direct + indirect + induced.
    """
    direct: float
    indirect: float
    induced: float

    @property
    def total(self) -> float:
        return self.direct + self.indirect + self.induced

    @property
    def type_i_total(self) -> float:
        """Direto + indireto (sem induzido)."""
        return self.direct + self.indirect


def decompose_employment_impact(
    direct_jobs: float,
    multiplier_result: RegionalMultiplierResult,
) -> ImpactDecomposition:
    """Decompoe o impacto de emprego em direto, indireto e induzido.

    Args:
        direct_jobs: numero de empregos diretos.
        multiplier_result: resultado do ajuste regional.

    Returns:
        ImpactDecomposition com empregos diretos, indiretos e induzidos.
    """
    indirect = direct_jobs * (multiplier_result.employment_type_i - 1.0)
    induced = direct_jobs * (
        multiplier_result.employment_type_ii
        - multiplier_result.employment_type_i
    )
    return ImpactDecomposition(
        direct=direct_jobs,
        indirect=round(indirect, 2),
        induced=round(induced, 2),
    )


def decompose_production_impact(
    direct_output: float,
    multiplier_result: RegionalMultiplierResult,
) -> ImpactDecomposition:
    """Decompoe o impacto de producao (VBP) em direto, indireto e induzido.

    Args:
        direct_output: valor bruto da producao direta (R$).
        multiplier_result: resultado do ajuste regional.

    Returns:
        ImpactDecomposition com VBP direto, indireto e induzido.
    """
    indirect = direct_output * (multiplier_result.production_type_i - 1.0)
    induced = direct_output * (
        multiplier_result.production_type_ii
        - multiplier_result.production_type_i
    )
    return ImpactDecomposition(
        direct=direct_output,
        indirect=round(indirect, 2),
        induced=round(induced, 2),
    )


def decompose_income_impact(
    direct_income: float,
    multiplier_result: RegionalMultiplierResult,
) -> ImpactDecomposition:
    """Decompoe o impacto de renda em direto, indireto e induzido.

    Args:
        direct_income: renda direta (salarios, R$).
        multiplier_result: resultado do ajuste regional.

    Returns:
        ImpactDecomposition com renda direta, indireta e induzida.
    """
    indirect = direct_income * (multiplier_result.income_type_i - 1.0)
    induced = direct_income * (
        multiplier_result.income_type_ii
        - multiplier_result.income_type_i
    )
    return ImpactDecomposition(
        direct=direct_income,
        indirect=round(indirect, 2),
        induced=round(induced, 2),
    )


# ---------------------------------------------------------------------------
# 5. Funcao de conveniencia: pipeline completo
# ---------------------------------------------------------------------------

def compute_port_impact(
    direct_jobs: float,
    direct_output_brl: float,
    direct_income_brl: float,
    ql: float,
    region_code: str = "",
    ql_method: QLMethod = QLMethod.SIMPLE,
    adjustment_method: AdjustmentMethod = AdjustmentMethod.CAPPED_LINEAR,
    cap: float = 2.5,
) -> Dict:
    """Pipeline completo: QL -> ajuste -> decomposicao.

    Args:
        direct_jobs: empregos diretos no setor portuario.
        direct_output_brl: VBP direto (R$).
        direct_income_brl: renda direta (R$).
        ql: quociente locacional pre-calculado.
        region_code: codigo IBGE.
        ql_method: metodo QL usado.
        adjustment_method: estrategia de ajuste.
        cap: teto para CAPPED_LINEAR.

    Returns:
        Dicionario com multiplicadores ajustados e decomposicao
        de impactos (emprego, producao, renda).
    """
    mult = adjust_multipliers(
        ql=ql,
        region_code=region_code,
        adjustment_method=adjustment_method,
        cap=cap,
        ql_method=ql_method.value,
    )

    emp = decompose_employment_impact(direct_jobs, mult)
    prod = decompose_production_impact(direct_output_brl, mult)
    inc = decompose_income_impact(direct_income_brl, mult)

    return {
        "region_code": region_code,
        "ql": ql,
        "adjustment_factor": mult.adjustment_factor,
        "multipliers": {
            "production": {
                "type_i": mult.production_type_i,
                "type_ii": mult.production_type_ii,
            },
            "employment": {
                "type_i": mult.employment_type_i,
                "type_ii": mult.employment_type_ii,
            },
            "income": {
                "type_i": mult.income_type_i,
                "type_ii": mult.income_type_ii,
            },
        },
        "impact": {
            "employment": {
                "direct": emp.direct,
                "indirect": emp.indirect,
                "induced": emp.induced,
                "total": emp.total,
            },
            "production_brl": {
                "direct": prod.direct,
                "indirect": prod.indirect,
                "induced": prod.induced,
                "total": prod.total,
            },
            "income_brl": {
                "direct": inc.direct,
                "indirect": inc.indirect,
                "induced": inc.induced,
                "total": inc.total,
            },
        },
        "national_reference": mult.national_ref,
        "notes": mult.notes,
        "methodology": (
            "Multiplicadores nacionais: Vale & Perobelli (2020), "
            "MIP IBGE 2015, setor Transporte. "
            "Ajuste regional via QL: Miller & Blair (2009), cap. 3. "
            f"Metodo QL: {ql_method.value}. "
            f"Metodo ajuste: {adjustment_method.value}."
        ),
    }
