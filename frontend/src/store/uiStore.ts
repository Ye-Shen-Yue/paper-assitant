import { create } from 'zustand';

interface UIStore {
  theme: 'academic' | 'creative' | 'minimal';
  language: 'en' | 'zh';
  bilingualMode: boolean;
  readingMode: 'scan' | 'deep' | 'critical';
  sidebarOpen: boolean;
  setTheme: (theme: 'academic' | 'creative' | 'minimal') => void;
  setLanguage: (language: 'en' | 'zh') => void;
  setBilingualMode: (enabled: boolean) => void;
  setReadingMode: (mode: 'scan' | 'deep' | 'critical') => void;
  toggleSidebar: () => void;
}

export const useUIStore = create<UIStore>((set) => ({
  theme: 'academic',
  language: 'en',
  bilingualMode: false,
  readingMode: 'deep',
  sidebarOpen: true,
  setTheme: (theme) => set({ theme }),
  setLanguage: (language) => set({ language }),
  setBilingualMode: (enabled) => set({ bilingualMode: enabled }),
  setReadingMode: (mode) => set({ readingMode: mode }),
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
}));
