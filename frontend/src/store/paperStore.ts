import { create } from 'zustand';
import type { PaperSummary, PaperDetail } from '../api/types';

interface PaperStore {
  papers: PaperSummary[];
  currentPaper: PaperDetail | null;
  loading: boolean;
  error: string | null;
  setPapers: (papers: PaperSummary[]) => void;
  setCurrentPaper: (paper: PaperDetail | null) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  removePaper: (id: string) => void;
}

export const usePaperStore = create<PaperStore>((set) => ({
  papers: [],
  currentPaper: null,
  loading: false,
  error: null,
  setPapers: (papers) => set({ papers }),
  setCurrentPaper: (paper) => set({ currentPaper: paper }),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
  removePaper: (id) => set((state) => ({
    papers: state.papers.filter((p) => p.id !== id),
  })),
}));
