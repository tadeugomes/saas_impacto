export interface TempoMedioEsperaData {
  id_instalacao: string;
  ano: number;
  tempo_medio_espera_horas: number;
  total_atracacoes: number;
}

export interface DistribuicaoTipoNavioData {
  id_instalacao: string;
  ano: number;
  tipo_navegacao: string;
  qtd_atracacoes: number;
  percentual: number;
}

export interface IndicatorData {
  code: string;
  name: string;
  description: string;
  unit: string;
  unctad: boolean;
  data: any[];
}
