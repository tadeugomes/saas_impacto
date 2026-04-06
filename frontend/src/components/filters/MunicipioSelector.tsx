import { useFilterStore } from '../../store/filterStore';
import { Anchor } from 'lucide-react';

export type MunicipioOption = { id_municipio: string; label: string };

// Portos organizados por região — label = nome do porto, value = id_municipio IBGE
// IDs validados contra o mart BigQuery (2026-04).
// Municípios com múltiplos portos (ex: Rio de Janeiro/PortosRio) agregam toda a
// movimentação portuária do município no mart ANTAQ.
const PORTOS_NORTE: MunicipioOption[] = [
  { id_municipio: '1501303', label: 'Porto de Vila do Conde / Barcarena (PA)' },
  { id_municipio: '1506807', label: 'Porto de Santarém (PA)' },
  { id_municipio: '1302603', label: 'Porto de Manaus (AM)' },
  { id_municipio: '1302103', label: 'Porto de Itacoatiara (AM)' },
  { id_municipio: '1100205', label: 'Porto de Porto Velho (RO)' },
];

const PORTOS_NORDESTE: MunicipioOption[] = [
  { id_municipio: '2111300', label: 'Porto do Itaqui (MA)' },
  { id_municipio: '2207702', label: 'Porto de Parnaíba (PI)' },
  { id_municipio: '2312403', label: 'Porto do Pecém (CE)' },
  { id_municipio: '2304400', label: 'Porto do Mucuripe / Fortaleza (CE)' },
  { id_municipio: '2408102', label: 'Porto de Natal (RN)' },
  { id_municipio: '2404507', label: 'Porto de Areia Branca / Guamaré (RN)' },
  { id_municipio: '2503209', label: 'Porto de Cabedelo (PB)' },
  { id_municipio: '2611606', label: 'Porto do Recife (PE)' },
  { id_municipio: '2607208', label: 'Porto de Suape / Ipojuca (PE)' },
  { id_municipio: '2704302', label: 'Porto de Maceió (AL)' },
  { id_municipio: '2919926', label: 'Porto de Aratu / Madre de Deus (BA)' },
  { id_municipio: '2927408', label: 'Porto de Salvador (BA)' },
  { id_municipio: '2913606', label: 'Porto de Ilhéus (BA)' },
];

const PORTOS_SUDESTE: MunicipioOption[] = [
  { id_municipio: '3548500', label: 'Porto de Santos (SP)' },
  { id_municipio: '3550703', label: 'Porto de São Sebastião (SP)' },
  { id_municipio: '3304557', label: 'PortosRio — Rio de Janeiro (RJ)' },
  { id_municipio: '3302007', label: 'Porto de Itaguaí (RJ)' },
  { id_municipio: '3205309', label: 'Porto de Vitória / Capuaba (ES)' },
  { id_municipio: '3201207', label: 'Porto de Aracruz (ES)' },
];

const PORTOS_SUL: MunicipioOption[] = [
  { id_municipio: '4118204', label: 'Portos do Paraná / Paranaguá (PR)' },
  { id_municipio: '4101200', label: 'Porto de Antonina (PR)' },
  { id_municipio: '4216206', label: 'Porto de São Francisco do Sul (SC)' },
  { id_municipio: '4208203', label: 'Porto de Itajaí (SC)' },
  { id_municipio: '4207304', label: 'Porto de Imbituba (SC)' },
  { id_municipio: '4315602', label: 'Porto de Rio Grande (RS)' },
  { id_municipio: '4313409', label: 'Porto de Pelotas (RS)' },
  { id_municipio: '4314902', label: 'Porto de Porto Alegre (RS)' },
];

export const MUNICIPIOS_PORTUARIOS: MunicipioOption[] = [
  ...PORTOS_NORTE,
  ...PORTOS_NORDESTE,
  ...PORTOS_SUDESTE,
  ...PORTOS_SUL,
];

export function MunicipioSelector() {
  const { selectedMunicipio, setMunicipio } = useFilterStore();

  return (
    <div className="flex items-center gap-2">
      <div className="relative">
        <label className="sr-only">Selecione o Porto</label>
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <Anchor className="h-4 w-4 text-gray-400" />
        </div>
        <select
          value={selectedMunicipio || ''}
          onChange={(e) => setMunicipio(e.target.value || null)}
          className="pl-9 pr-8 py-1.5 text-sm border border-gray-300 rounded-lg focus:ring-primary focus:border-primary bg-white text-gray-700 hover:bg-gray-50 transition-colors cursor-pointer appearance-none min-w-[280px]"
        >
          <option value="">Todos os Portos</option>
          <optgroup label="🌿 Região Norte">
            {PORTOS_NORTE.map((m) => (
              <option key={m.id_municipio} value={m.id_municipio}>
                {m.label}
              </option>
            ))}
          </optgroup>
          <optgroup label="☀️ Região Nordeste">
            {PORTOS_NORDESTE.map((m) => (
              <option key={m.id_municipio} value={m.id_municipio}>
                {m.label}
              </option>
            ))}
          </optgroup>
          <optgroup label="🏙️ Região Sudeste">
            {PORTOS_SUDESTE.map((m) => (
              <option key={m.id_municipio} value={m.id_municipio}>
                {m.label}
              </option>
            ))}
          </optgroup>
          <optgroup label="🌊 Região Sul">
            {PORTOS_SUL.map((m) => (
              <option key={m.id_municipio} value={m.id_municipio}>
                {m.label}
              </option>
            ))}
          </optgroup>
        </select>
        <div className="absolute inset-y-0 right-0 pr-2 flex items-center pointer-events-none">
          <svg className="h-4 w-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </div>
    </div>
  );
}
