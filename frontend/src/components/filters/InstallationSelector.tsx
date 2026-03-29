import { useFilterStore } from '../../store/filterStore';
import { Anchor } from 'lucide-react';

export type PortoOption = { value: string; label: string };

// Portos Organizados — confirmados no BigQuery (porto_atracacao exato)
export const PORTOS_ORGANIZADOS: PortoOption[] = [
    // REGIÃO NORTE
    { value: 'Belém', label: 'Belém (PA)' },
    { value: 'Itaqui', label: 'Itaqui (MA)' },
    { value: 'Manaus', label: 'Manaus (AM)' },
    { value: 'Porto Velho', label: 'Porto Velho (RO)' },
    { value: 'Santana', label: 'Santana (AP)' },
    { value: 'Santarém', label: 'Santarém (PA)' },
    { value: 'Vila do Conde', label: 'Vila do Conde (PA)' },
    // REGIÃO NORDESTE
    { value: 'Aratu', label: 'Aratu (BA)' },
    { value: 'Areia Branca', label: 'Areia Branca (RN)' },
    { value: 'Cabedelo', label: 'Cabedelo (PB)' },
    { value: 'Fortaleza', label: 'Fortaleza (CE)' },
    { value: 'Ilhéus', label: 'Ilhéus (BA)' },
    { value: 'Maceió', label: 'Maceió (AL)' },
    { value: 'Natal', label: 'Natal (RN)' },
    { value: 'Recife', label: 'Recife (PE)' },
    { value: 'Salvador', label: 'Salvador (BA)' },
    { value: 'Suape', label: 'Suape (PE)' },
    // REGIÃO SUDESTE
    { value: 'Angra dos Reis', label: 'Angra dos Reis (RJ)' },
    { value: 'Itaguaí', label: 'Itaguaí (RJ)' },
    { value: 'Niterói', label: 'Niterói (RJ)' },
    { value: 'Rio de Janeiro', label: 'Rio de Janeiro (RJ)' },
    { value: 'Santos', label: 'Santos (SP)' },
    { value: 'São Sebastião', label: 'São Sebastião (SP)' },
    { value: 'Vitória', label: 'Vitória (ES)' },
    // REGIÃO SUL
    { value: 'Antonina', label: 'Antonina (PR)' },
    { value: 'Imbituba', label: 'Imbituba (SC)' },
    { value: 'Itajaí', label: 'Itajaí (SC)' },
    { value: 'Paranaguá', label: 'Paranaguá (PR)' },
    { value: 'Pelotas', label: 'Pelotas (RS)' },
    { value: 'Porto Alegre', label: 'Porto Alegre (RS)' },
    { value: 'Rio Grande', label: 'Rio Grande (RS)' },
    { value: 'São Francisco do Sul', label: 'São Francisco do Sul (SC)' },
];

// Terminais de Uso Privado (TUPs) — operação privada, nome exato do BigQuery
export const TERMINAIS_PRIVADOS: PortoOption[] = [
    { value: 'DP World Santos', label: 'DP World Santos (SP)' },
    { value: 'Portonave - Terminais Portuários de Navegantes', label: 'Portonave (SC)' },
    { value: 'Terminal Portuário Privativo da Alumar', label: 'Alumar (MA)' },
    { value: 'Terminal Portuário do Pecém', label: 'Terminal do Pecém (CE)' },
    { value: 'Terminal de Tubarão', label: 'Terminal de Tubarão — ArcelorMittal (ES)' },
];

// Lista unificada para compatibilidade com código existente (ex: Module11View)
export const PORTO_OPTIONS: PortoOption[] = [
    ...PORTOS_ORGANIZADOS,
    ...TERMINAIS_PRIVADOS,
];

export function InstallationSelector() {
    const { selectedInstallation, setInstallation } = useFilterStore();

    return (
        <div className="flex items-center gap-2">
            <div className="relative">
                <label className="sr-only">Selecione o Porto ou Terminal</label>
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <Anchor className="h-4 w-4 text-gray-400" />
                </div>
                <select
                    value={selectedInstallation || ''}
                    onChange={(e) => setInstallation(e.target.value || null)}
                    className="pl-9 pr-8 py-1.5 text-sm border border-gray-300 rounded-lg focus:ring-primary focus:border-primary bg-white text-gray-700 hover:bg-gray-50 transition-colors cursor-pointer appearance-none min-w-[200px]"
                >
                    <option value="">Todos os Portos</option>
                    <optgroup label="⚓ Porto Organizado">
                        {PORTOS_ORGANIZADOS.map((option) => (
                            <option key={option.value} value={option.value}>
                                {option.label}
                            </option>
                        ))}
                    </optgroup>
                    <optgroup label="🏭 Terminal Privativo (TUP)">
                        {TERMINAIS_PRIVADOS.map((option) => (
                            <option key={option.value} value={option.value}>
                                {option.label}
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
