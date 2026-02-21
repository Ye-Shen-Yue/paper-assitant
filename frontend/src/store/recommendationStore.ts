import { create } from 'zustand';
import type { UserProfile, RecommendationItem, TrendData, UserCollection } from '../api/recommendations';

interface RecommendationStore {
  // User profile
  profile: UserProfile | null;
  profileLoading: boolean;
  setProfile: (profile: UserProfile | null) => void;
  setProfileLoading: (loading: boolean) => void;

  // Recommendations
  recommendations: RecommendationItem[];
  recommendationsLoading: boolean;
  setRecommendations: (recommendations: RecommendationItem[]) => void;
  setRecommendationsLoading: (loading: boolean) => void;

  // Trend data
  trendData: TrendData | null;
  trendDataLoading: boolean;
  setTrendData: (data: TrendData | null) => void;
  setTrendDataLoading: (loading: boolean) => void;

  // Collections
  collections: UserCollection[];
  collectionsLoading: boolean;
  setCollections: (collections: UserCollection[]) => void;
  setCollectionsLoading: (loading: boolean) => void;
  addCollection: (collection: UserCollection) => void;
  removeCollection: (id: string) => void;
}

export const useRecommendationStore = create<RecommendationStore>((set) => ({
  // Profile
  profile: null,
  profileLoading: false,
  setProfile: (profile) => set({ profile }),
  setProfileLoading: (profileLoading) => set({ profileLoading }),

  // Recommendations
  recommendations: [],
  recommendationsLoading: false,
  setRecommendations: (recommendations) => set({ recommendations }),
  setRecommendationsLoading: (recommendationsLoading) => set({ recommendationsLoading }),

  // Trend data
  trendData: null,
  trendDataLoading: false,
  setTrendData: (trendData) => set({ trendData }),
  setTrendDataLoading: (trendDataLoading) => set({ trendDataLoading }),

  // Collections
  collections: [],
  collectionsLoading: false,
  setCollections: (collections) => set({ collections }),
  setCollectionsLoading: (collectionsLoading) => set({ collectionsLoading }),
  addCollection: (collection) =>
    set((state) => ({ collections: [...state.collections, collection] })),
  removeCollection: (id) =>
    set((state) => ({
      collections: state.collections.filter((c) => c.id !== id),
    })),
}));
