import { useFilterStore } from '../../store/filterStore';
import { Building2 } from 'lucide-react';

export type MunicipioOption = { id_municipio: string; label: string };

// Municípios portuários — agrupados por região, código IBGE 7 dígitos
// Fonte: PORT_TO_IBGE_MAPPING (generic_indicator_service.py)
const MUNICIPIOS_NORTE: MunicipioOption[] = [
    { id_municipio: '1501402', label: 'Belém (PA)' },
    { id_municipio: '1504139', label: 'Barcarena (PA)' },       // Vila do Conde
    { id_municipio: '1302603', label: 'Manaus (AM)' },
    { id_municipio: '1302103', label: 'Itacoatiara (AM)' },
    { id_municipio: '1100205', label: 'Porto Velho (RO)' },
    { id_municipio: '1600600', label: 'Santana (AP)' },
    { id_municipio: '1506807', label: 'Santarém (PA)' },
];

const MUNICIPIOS_NORDESTE: MunicipioOption[] = [
    { id_municipio: '2906501', label: 'Candeias (BA)' },         // Porto de Aratu
    { id_municipio: '2400703', label: 'Areia Branca (RN)' },
    { id_municipio: '2504009', label: 'Cabedelo (PB)' },
    { id_municipio: '2304400', label: 'Fortaleza (CE)' },        // Mucuripe
    { id_municipio: '2913350', label: 'Ilhéus (BA)' },
    { id_municipio: '2704302', label: 'Maceió (AL)' },
    { id_municipio: '2408102', label: 'Natal (RN)' },
    { id_municipio: '2312403', label: 'São Gonçalo do Amarante (CE)' }, // Pecém
    { id_municipio: '2611606', label: 'Recife (PE)' },
    { id_municipio: '2927408', label: 'Salvador (BA)' },
    { id_municipio: '2607208', label: 'Ipojuca (PE)' },          // Suape
    { id_municipio: '2111300', label: 'São Luís (MA)' },         // Itaqui / Alumar
];

const MUNICIPIOS_SUDESTE: MunicipioOption[] = [
    { id_municipio: '3300100', label: 'Angra dos Reis (RJ)' },
    { id_municipio: '3302000', label: 'Itaguaí (RJ)' },
    { id_municipio: '3303302', label: 'Niterói (RJ)' },
    { id_municipio: '3304557', label: 'Rio de Janeiro (RJ)' },
    { id_municipio: '3548500', label: 'Santos (SP)' },
    { id_municipio: '3550703', label: 'São Sebastião (SP)' },
    { id_municipio: '3205309', label: 'Vitória (ES)' },          // Tubarão / TVV / ArcelorMittal
    { id_municipio: '3201207', label: 'Aracruz (ES)' },
];

const MUNICIPIOS_SUL: MunicipioOption[] = [
    { id_municipio: '4101200', label: 'Antonina (PR)' },
    { id_municipio: '4206805', label: 'Imbituba (SC)' },
    { id_municipio: '4208203', label: 'Itajaí (SC)' },
    { id_municipio: '4118204', label: 'Paranaguá (PR)' },
    { id_municipio: '4313409', label: 'Pelotas (RS)' },
    { id_municipio: '4314902', label: 'Porto Alegre (RS)' },
    { id_municipio: '4315602', label: 'Rio Grande (RS)' },
    { id_municipio: '4220000', label: 'São Francisco do Sul (SC)' },
];

export const MUNICIPIOS_PORTUARIOS: MunicipioOption[] = [
    ...MUNICIPIOS_NORTE,
    ...MUNICIPIOS_NORDESTE,
    ...MUNICIPIOS_SUDESTE,
    ...MUNICIPIOS_SUL,
];

export function MunicipioSelector() {
    const { selectedMunicipio, setMunicipio } = useFilterStore();

    return (
        <div className="flex items-center gap-2">
            <div className="relative">
                <label className="sr-only">Selecione o Município</label>
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <Building2 className="h-4 w-4 text-gray-400" />
                </div>
                <select
                    value={selectedMunicipio || ''}
                    onChange={(e) => setMunicipio(e.target.value || null)}
                    className="pl-9 pr-8 py-1.5 text-sm border border-gray-300 rounded-lg focus:ring-primary focus:border-primary bg-white text-gray-700 hover:bg-gray-50 transition-colors cursor-pointer appearance-none min-w-[220px]"
                >
                    <option value="">Todos os Municípios</option>
                    <optgroup label="🌿 Região Norte">
                        {MUNICIPIOS_NORTE.map((m) => (
                            <option key={m.id_municipio} value={m.id_municipio}>
                                {m.label}
                            </option>
                        ))}
                    </optgroup>
                    <optgroup label="☀️ Região Nordeste">
                        {MUNICIPIOS_NORDESTE.map((m) => (
                            <option key={m.id_municipio} value={m.id_municipio}>
                                {m.label}
                            </option>
                        ))}
                    </optgroup>
                    <optgroup label="🏙️ Região Sudeste">
                        {MUNICIPIOS_SUDESTE.map((m) => (
                            <option key={m.id_municipio} value={m.id_municipio}>
                                {m.label}
                            </option>
                        ))}
                    </optgroup>
                    <optgroup label="🌊 Região Sul">
                        {MUNICIPIOS_SUL.map((m) => (
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
