"""Testes de utilitários de resolução de município para consultas por instalação."""

from app.services.generic_indicator_service import (
    GenericIndicatorService,
)



def test_resolve_installation_name_tolerates_punctuation_and_prefixes():
    """Nomes com variações devem continuar resolvendo para o município mapeado."""
    assert GenericIndicatorService._resolve_municipio_from_instalacao("Santos (SP)") == "3548500"
    assert GenericIndicatorService._resolve_municipio_from_instalacao("porto de santos") == "3548500"
    assert GenericIndicatorService._resolve_municipio_from_instalacao("Porto de Santos") == "3548500"
    assert GenericIndicatorService._resolve_municipio_from_instalacao("PORTO DE ITAJAI") == "4208203"
    assert GenericIndicatorService._resolve_municipio_from_instalacao("TNG Paranaguá") == "4118204"


def test_resolve_installation_name_prefers_known_numeric_code():
    """Código IBGE de 7 dígitos deve ser aceito diretamente."""
    assert GenericIndicatorService._resolve_municipio_from_instalacao("1234567") == "1234567"


def test_resolve_installation_name_returns_none_when_unknown():
    """Quando não houver correspondência, retorno deve ser explícito como nulo."""
    assert GenericIndicatorService._resolve_municipio_from_instalacao("Porto Inexistente") is None


def test_resolve_area_influencia_uses_normalized_installation_name():
    """Fallback de área de influência deve seguir normalização do nome da instalação."""
    assert GenericIndicatorService._resolve_area_influencia("santos (SP)", tenant_policy={}) == [
        {"id_municipio": "3548500", "peso": 1.0}
    ]
    assert GenericIndicatorService._resolve_area_influencia("PORTO DE ITAQUI", tenant_policy={}) == [
        {"id_municipio": "2111300", "peso": 1.0}
    ]
