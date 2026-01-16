import { useFilterStore } from '../../store/filterStore';
import { Anchor } from 'lucide-react';

// Portos brasileiros organizados por região
const PORTO_OPTIONS = [
    // REGIÃO NORTE
    { value: 'Amapá', label: 'Amapá (AP)' },
    { value: 'Belém', label: 'Belém (PA)' },
    { value: 'Itaqui', label: 'Itaqui (MA)' },
    { value: 'Itacoatiara', label: 'Itacoatiara (AM)' },
    { value: 'Manaus', label: 'Manaus (AM)' },
    { value: 'Pecém', label: 'Pecém (CE)' },
    { value: 'Porto Velho', label: 'Porto Velho (RO)' },
    { value: 'Santarém', label: 'Santarém (PA)' },
    { value: 'Vila do Conde', label: 'Vila do Conde (PA)' },

    // REGIÃO NORDESTE
    { value: 'Aratu', label: 'Aratu (BA)' },
    { value: 'Cabedelo', label: 'Cabedelo (PB)' },
    { value: 'Fortaleza', label: 'Fortaleza (CE)' },
    { value: 'Mucuripe', label: 'Mucuripe (CE)' },
    { value: 'Ilhéus', label: 'Ilhéus (BA)' },
    { value: 'Imbui', label: 'Imbui (BA)' },
    { value: 'Itaparica', label: 'Itaparica (BA)' },
    { value: 'Jacuípe', label: 'Jacuípe (BA)' },
    { value: 'Maceió', label: 'Maceió (AL)' },
    { value: 'Natal', label: 'Natal (RN)' },
    { value: 'Recife', label: 'Recife (PE)' },
    { value: 'Salvador', label: 'Salvador (BA)' },
    { value: 'Suape', label: 'Suape (PE)' },
    { value: 'São Luís', label: 'São Luís (MA)' },

    // REGIÃO CENTRO-OESTE
    { value: 'Alvorada do Norte', label: 'Alvorada do Norte (GO)' },

    // REGIÃO SUDESTE
    { value: 'Angra dos Reis', label: 'Angra dos Reis (RJ)' },
    { value: 'Aracruz', label: 'Aracruz (ES)' },
    { value: 'Cabo Frio', label: 'Cabo Frio (RJ)' },
    { value: 'Caraguatatuba', label: 'Caraguatatuba (SP)' },
    { value: 'Itaguaí', label: 'Itaguaí (RJ)' },
    { value: 'Macaé', label: 'Macaé (RJ)' },
    { value: 'Niterói', label: 'Niterói (RJ)' },
    { value: 'Rio de Janeiro', label: 'Rio de Janeiro (RJ)' },
    { value: 'São Sebastião', label: 'São Sebastião (SP)' },
    { value: 'Sepetiba', label: 'Sepetiba (RJ)' },
    { value: 'Vila Velha', label: 'Vila Velha (ES)' },
    { value: 'Vitória', label: 'Vitória (ES)' },

    // REGIÃO SUL
    { value: 'Antonina', label: 'Antonina (PR)' },
    { value: 'Araquari', label: 'Araquari (SC)' },
    { value: 'Balneário Camboriú', label: 'Balneário Camboriú (SC)' },
    { value: 'Barra do Sul', label: 'Barra do Sul (SC)' },
    { value: 'Braço do Norte', label: 'Braço do Norte (SC)' },
    { value: 'Capivari de Baixo', label: 'Capivari de Baixo (SC)' },
    { value: 'Garopaba', label: 'Garopaba (SC)' },
    { value: 'Imbituba', label: 'Imbituba (SC)' },
    { value: 'Itajaí', label: 'Itajaí (SC)' },
    { value: 'Itapoá', label: 'Itapoá (SC)' },
    { value: 'Laguna', label: 'Laguna (SC)' },
    { value: 'Navegantes', label: 'Navegantes (SC)' },
    { value: 'Paranaguá', label: 'Paranaguá (PR)' },
    { value: 'Penha', label: 'Penha (SC)' },
    { value: 'Rio Grande', label: 'Rio Grande (RS)' },
    { value: 'São Francisco do Sul', label: 'São Francisco do Sul (SC)' },
    { value: 'Torres', label: 'Torres (RS)' },

    // ESTADO DE SÃO PAULO (Principais)
    { value: 'Bertioga', label: 'Bertioga (SP)' },
    { value: 'Cubatão', label: 'Cubatão (SP)' },
    { value: 'Santos', label: 'Santos (SP)' },
    { value: 'São Vicente', label: 'São Vicente (SP)' },

    // TERMINAIS ESPECÍFICOS (TUPs)
    { value: 'DP World Santos', label: 'DP World Santos' },
    { value: 'Portonave Santos', label: 'Portonave Santos' },
    { value: 'Santos Brasil', label: 'Santos Brasil' },
    { value: 'TCP Paranaguá', label: 'TCP Paranaguá' },
    { value: 'TNG Paranaguá', label: 'TNG Paranaguá' },
    { value: 'Portonave Itajaí', label: 'Portonave Itajaí' },
    { value: 'CSN Itaguaí', label: 'CSN Itaguaí' },
    { value: 'Valec Itaqui', label: 'Valec Itaqui' },
    { value: 'Alumar', label: 'Alumar' },
    { value: 'SZP Pecém', label: 'SZP Pecém' },
    { value: 'TCU Suape', label: 'TCU Suape' },
    { value: 'TVV Vitória', label: 'TVV Vitória' },
    { value: 'ArcelorMittal Tubarão', label: 'ArcelorMittal Tubarão' },
];

export function InstallationSelector() {
    const { selectedInstallation, setInstallation } = useFilterStore();

    return (
        <div className="flex items-center gap-2">
            <div className="relative">
                <label className="sr-only">Selecione o Porto</label>
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <Anchor className="h-4 w-4 text-gray-400" />
                </div>
                <select
                    value={selectedInstallation || ''}
                    onChange={(e) => setInstallation(e.target.value || null)}
                    className="pl-9 pr-8 py-1.5 text-sm border border-gray-300 rounded-lg focus:ring-primary focus:border-primary bg-white text-gray-700 hover:bg-gray-50 transition-colors cursor-pointer appearance-none min-w-[200px]"
                >
                    <option value="">Todos os Portos</option>
                    {PORTO_OPTIONS.map((option) => (
                        <option key={option.value} value={option.value}>
                            {option.label}
                        </option>
                    ))}
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
