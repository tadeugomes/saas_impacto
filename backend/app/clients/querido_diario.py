"""
Cliente para a API do Querido Diário (OKBR).

API: https://queridodiario.ok.org.br/api/
Autenticação: Nenhuma (API aberta).

Busca menções ao porto em diários oficiais municipais e classifica
por tema e sentimento usando análise léxica (sem ML externo).
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
from collections import Counter, defaultdict
from typing import Any, Dict, List, Optional

from app.clients.base import BasePublicApiClient, PublicApiError
from app.config import get_settings

logger = logging.getLogger(__name__)

# Classificação temática por palavras-chave
TEMAS_COMPLIANCE = {
    "Infraestrutura e Obras": [
        "obra", "licitação", "dragagem", "berço", "ampliação",
        "inauguração", "construção", "investimento", "concessão",
        "modernização", "pavimentação", "terminal",
    ],
    "Meio Ambiente": [
        "ambiental", "licença", "embargo", "multa ambiental",
        "ibama", "descarte", "poluição", "remediação",
        "licenciamento", "eia", "rima", "impacto ambiental",
    ],
    "Regulação e Fiscalização": [
        "antaq", "resolução", "portaria", "fiscalização",
        "regulação", "normativo", "instrução normativa",
        "autoridade portuária", "alfândega", "receita federal",
    ],
    "Trabalhista": [
        "ogmo", "sindicato", "trabalhador portuário", "avulso",
        "escalação", "greve", "acordo coletivo", "dissídio",
        "segurança do trabalho", "nr-29",
    ],
    "Tributário e Fiscal": [
        "icms", "tributo", "fiscal", "isenção", "incentivo",
        "zona franca", "regime especial", "drawback",
        "tax", "alíquota",
    ],
}

# Polaridade léxica
PALAVRAS_POSITIVAS = {
    "investimento", "inauguração", "ampliação", "aprovação", "concessão",
    "modernização", "crescimento", "expansão", "melhoria", "autorização",
    "recordes", "recorde", "aumento", "benefício", "parceria",
}
PALAVRAS_NEGATIVAS = {
    "multa", "embargo", "sanção", "irregularidade", "suspensão",
    "interdição", "infração", "penalidade", "proibição", "cancelamento",
    "rescisão", "inadimplência", "autuação", "notificação", "descumprimento",
    "poluição", "acidente", "greve", "paralisação", "denúncia",
}


def _classify_theme(text: str) -> str:
    """Classifica um texto em um tema."""
    text_lower = text.lower()
    scores: Dict[str, int] = {}
    for tema, keywords in TEMAS_COMPLIANCE.items():
        scores[tema] = sum(1 for kw in keywords if kw in text_lower)
    best = max(scores, key=scores.get) if any(scores.values()) else "Outros"
    return best if scores.get(best, 0) > 0 else "Outros"


def _sentiment_score(text: str) -> float:
    """Calcula score de sentimento (-1 a +1) por análise léxica."""
    words = set(re.findall(r'\b\w+\b', text.lower()))
    pos = len(words & PALAVRAS_POSITIVAS)
    neg = len(words & PALAVRAS_NEGATIVAS)
    total = pos + neg
    if total == 0:
        return 0.0
    return round((pos - neg) / total, 2)


def _sentiment_label(score: float) -> str:
    if score > 0.2:
        return "positivo"
    elif score < -0.2:
        return "negativo"
    return "neutro"


class QueridoDiarioClient(BasePublicApiClient):
    """Cliente assíncrono para a API do Querido Diário."""

    def __init__(self):
        settings = get_settings()
        super().__init__(
            base_url=settings.querido_diario_api_base_url,
            api_name="querido_diario",
            timeout=settings.public_api_timeout_seconds,
        )
        self._cache_ttl = settings.cache_ttl_compliance

    def _make_cache_key(self, endpoint: str, params: dict) -> str:
        payload = json.dumps({"ep": endpoint, **params}, sort_keys=True)
        digest = hashlib.sha1(payload.encode()).hexdigest()
        return f"api:querido_diario:{endpoint}:{digest}"

    async def buscar_mencoes_portuarias(
        self,
        cod_municipio_ibge: str,
        termos_extra: Optional[List[str]] = None,
        meses: int = 12,
    ) -> List[Dict[str, Any]]:
        """
        Busca menções portuárias em diários oficiais do município.

        Args:
            cod_municipio_ibge: Código IBGE 7 dígitos
            termos_extra: Termos adicionais (ex: nome do porto)
            meses: Período de busca em meses (default: 12)
        """
        from datetime import date, timedelta
        hoje = date.today()
        inicio = (hoje - timedelta(days=meses * 30)).isoformat()

        termos = ["porto", "portuário", "terminal portuário"]
        if termos_extra:
            termos.extend(termos_extra)
        query = " OR ".join(f'"{t}"' for t in termos)

        cache_key = self._make_cache_key(
            "mencoes", {"mun": cod_municipio_ibge, "q": query[:50], "m": meses}
        )

        async def _fetch():
            params = {
                "territory_id": cod_municipio_ibge,
                "querystring": query,
                "since": inicio,
                "until": hoje.isoformat(),
                "size": 100,
                "sort_by": "descending_date",
            }
            try:
                data = await self.get("/gazettes", params=params)
                if isinstance(data, dict):
                    return data.get("gazettes", data.get("data", []))
                return data if isinstance(data, list) else []
            except PublicApiError as e:
                logger.warning("querido_diario_error: %s", e)
                return []

        return await self.get_cached(cache_key, _fetch, ttl=self._cache_ttl)

    async def analisar_mencoes_com_temas(
        self,
        cod_municipio_ibge: str,
        nome_instalacao: Optional[str] = None,
        meses: int = 12,
    ) -> Dict[str, Any]:
        """
        IND-10.04: Análise de menções com sentimento e temas.

        Retorna total de menções, score de sentimento geral,
        e detalhamento por tema com justificativa.
        """
        from datetime import datetime, timezone

        termos_extra = [nome_instalacao] if nome_instalacao else None
        mencoes = await self.buscar_mencoes_portuarias(
            cod_municipio_ibge, termos_extra, meses
        )

        if not mencoes:
            return {
                "cod_municipio": cod_municipio_ibge,
                "id_instalacao": nome_instalacao,
                "periodo_meses": meses,
                "total_mencoes": 0,
                "sentimento_geral": "sem_dados",
                "score_sentimento": None,
                "temas": [],
            }

        # Classifica cada menção por tema e sentimento
        by_theme: Dict[str, List[Dict]] = defaultdict(list)
        scores_all = []

        for m in mencoes:
            excerpt = str(m.get("excerpt", m.get("excerto", "")))
            tema = _classify_theme(excerpt)
            score = _sentiment_score(excerpt)
            scores_all.append((score, len(excerpt)))
            by_theme[tema].append({
                "excerpt": excerpt[:200],
                "score": score,
                "date": m.get("date", m.get("data", "")),
            })

        # Score geral ponderado por tamanho do excerto
        total_weight = sum(w for _, w in scores_all) or 1
        score_geral = round(sum(s * w for s, w in scores_all) / total_weight, 2)

        # Monta detalhamento por tema
        temas = []
        for tema, items in sorted(by_theme.items(), key=lambda x: -len(x[1])):
            tema_scores = [i["score"] for i in items]
            tema_score = round(sum(tema_scores) / len(tema_scores), 2) if tema_scores else 0.0
            sentiment = _sentiment_label(tema_score)

            # Justificativa automática
            n_pos = sum(1 for s in tema_scores if s > 0.2)
            n_neg = sum(1 for s in tema_scores if s < -0.2)
            n_neu = len(tema_scores) - n_pos - n_neg
            if n_neg > n_pos:
                justificativa = f"Predominância de menções negativas ({n_neg} de {len(items)})"
            elif n_pos > n_neg:
                justificativa = f"Predominância de menções positivas ({n_pos} de {len(items)})"
            else:
                justificativa = f"Distribuição equilibrada ({n_pos} positivas, {n_neg} negativas, {n_neu} neutras)"

            temas.append({
                "tema": tema,
                "mencoes": len(items),
                "sentimento": sentiment,
                "score": tema_score,
                "exemplos": [i["excerpt"] for i in items[:3]],
                "justificativa": justificativa,
            })

        return {
            "cod_municipio": cod_municipio_ibge,
            "id_instalacao": nome_instalacao,
            "periodo_meses": meses,
            "total_mencoes": len(mencoes),
            "sentimento_geral": _sentiment_label(score_geral),
            "score_sentimento": score_geral,
            "temas": temas,
            "composicao": {
                "formula": "Score = média ponderada dos scores por tema (peso = nº menções)",
                "nota_metodologica": (
                    "Classificação temática por palavras-chave. Sentimento por polaridade "
                    "léxica (positivo: investimento, inauguração, ampliação; negativo: multa, "
                    "embargo, irregularidade, sanção). Determinístico e auditável."
                ),
                "fonte": "Querido Diário — OK Brasil (diários oficiais de 5.000+ municípios)",
                "periodo_busca": f"últimos {meses} meses",
                "termos_busca": ", ".join(
                    ["porto", "portuário", "terminal portuário"]
                    + ([nome_instalacao] if nome_instalacao else [])
                ),
                "ultima_atualizacao": datetime.now(timezone.utc).isoformat(),
            },
        }


# Singleton
_querido_diario_client: Optional[QueridoDiarioClient] = None


def get_querido_diario_client() -> QueridoDiarioClient:
    global _querido_diario_client
    if _querido_diario_client is None:
        _querido_diario_client = QueridoDiarioClient()
    return _querido_diario_client
