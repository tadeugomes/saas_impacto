export type MunicipioLabelMap = Record<string, string>;

const MUNICIPIO_ID_RE = /^\d{1,7}$/;

export function normalizeMunicipioId(value: unknown): string {
  if (value === null || value === undefined) {
    return '';
  }

  if (typeof value === 'number') {
    return String(Math.trunc(value));
  }

  if (typeof value !== 'string') {
    return '';
  }

  const normalized = value
    .normalize('NFD')
    .replace(/\p{Diacritic}/gu, '')
    .toUpperCase()
    .replace(/[^A-Z0-9_-]/g, ' ')
    .trim();

  const digits = normalized.replace(/\D/g, '');
  if (MUNICIPIO_ID_RE.test(digits)) {
    return digits.replace(/^0+/, '') || digits;
  }

  return '';
}

export function isLikelyIdNameMismatch(id: string, name: string): boolean {
  const cleanId = normalizeMunicipioId(id);
  if (!cleanId) {
    return false;
  }

  const normalizedName = (name || '')
    .normalize('NFD')
    .replace(/\p{Diacritic}/gu, '')
    .trim()
    .toUpperCase();

  if (!normalizedName) {
    return false;
  }

  if (MUNICIPIO_ID_RE.test(normalizedName.replace(/\D/g, ''))) {
    return true;
  }

  if (normalizedName.includes(cleanId)) {
    return true;
  }

  return false;
}

export function toMunicipioLabel(id: string, labels: MunicipioLabelMap, options?: { showCode?: boolean }): string {
  const normalizedId = normalizeMunicipioId(id);
  const label = labels[normalizedId] ?? labels[`${normalizedId}`];
  const showCode = options?.showCode ?? true;
  if (label) {
    return showCode ? `${label} (${normalizedId})` : label;
  }
  return showCode ? normalizedId : id;
}

export function resolveMunicipioLabel(
  municipio: string | null | undefined,
  labels: MunicipioLabelMap,
  options: { showCode?: boolean } = {},
): string {
  if (!municipio) {
    return 'N/D';
  }

  return toMunicipioLabel(municipio, labels, options);
}

export function formatMunicipioLabelList(
  municipios: string[] | null | undefined,
  labels: MunicipioLabelMap,
): string {
  if (!municipios || municipios.length === 0) {
    return '';
  }

  return municipios
    .map((municipio) => toMunicipioLabel(municipio, labels, { showCode: false }))
    .filter(Boolean)
    .join('; ');
}

