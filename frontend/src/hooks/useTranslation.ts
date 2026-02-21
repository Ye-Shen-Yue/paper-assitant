import { useCallback } from 'react';
import { useUIStore } from '../store/uiStore';
import { t, type Language } from '../utils/i18n';

export function useT() {
  const language = useUIStore((s) => s.language) as Language;
  const tr = useCallback((key: string) => t(key, language), [language]);
  return tr;
}
