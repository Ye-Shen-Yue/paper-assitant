import { useEffect, useRef, useCallback } from 'react';
import { trackActivity, type UserActivity } from '../api/recommendations';

const USER_ID_KEY = 'scholarlens_user_id';
const SESSION_START_KEY = 'scholarlens_session_start';

/**
 * Generate or retrieve persistent user ID for anonymous users
 */
export function getUserId(): string {
  let userId = localStorage.getItem(USER_ID_KEY);
  if (!userId) {
    userId = `user_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    localStorage.setItem(USER_ID_KEY, userId);
  }
  return userId;
}

/**
 * Clear user data (for privacy)
 */
export function clearUserData(): void {
  localStorage.removeItem(USER_ID_KEY);
  localStorage.removeItem(SESSION_START_KEY);
}

/**
 * Hook to track user activity on paper pages
 */
export function usePaperTracking(paperId: string | undefined) {
  const startTimeRef = useRef<number>(Date.now());
  const scrollDepthRef = useRef<number>(0);
  const hasTrackedViewRef = useRef<boolean>(false);
  const userId = getUserId();

  // Track scroll depth
  useEffect(() => {
    if (!paperId) return;

    const handleScroll = () => {
      const scrollTop = window.scrollY;
      const docHeight = document.documentElement.scrollHeight - window.innerHeight;
      const depth = docHeight > 0 ? scrollTop / docHeight : 0;
      scrollDepthRef.current = Math.max(scrollDepthRef.current, depth);
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, [paperId]);

  // Track page view
  useEffect(() => {
    if (!paperId || hasTrackedViewRef.current) return;

    hasTrackedViewRef.current = true;
    startTimeRef.current = Date.now();

    // Track initial view
    trackActivity({
      user_id: userId,
      paper_id: paperId,
      activity_type: 'view',
      duration_seconds: 0,
      meta_info: { source: 'direct' },
    }).catch(console.error);

    // Track duration when leaving
    return () => {
      const duration = Math.floor((Date.now() - startTimeRef.current) / 1000);
      if (duration > 5) { // Only track if stayed more than 5 seconds
        trackActivity({
          user_id: userId,
          paper_id: paperId,
          activity_type: 'view',
          duration_seconds: duration,
          meta_info: {
            scroll_depth: Math.round(scrollDepthRef.current * 100),
            session_duration: duration,
          },
        }).catch(console.error);
      }
    };
  }, [paperId, userId]);

  // Function to track custom activities
  const track = useCallback(
    async (activityType: UserActivity['activity_type'], metaInfo?: Record<string, unknown>) => {
      if (!paperId) return;

      await trackActivity({
        user_id: userId,
        paper_id: paperId,
        activity_type: activityType,
        meta_info: metaInfo,
      });
    },
    [paperId, userId]
  );

  return { track, userId };
}

/**
 * Hook to track reading time for a specific section
 */
export function useReadingTimeTracking(
  paperId: string | undefined,
  sectionType: string
) {
  const startTimeRef = useRef<number>(Date.now());
  const userId = getUserId();

  useEffect(() => {
    if (!paperId) return;

    startTimeRef.current = Date.now();

    return () => {
      const duration = Math.floor((Date.now() - startTimeRef.current) / 1000);
      if (duration > 10) { // Only track if stayed more than 10 seconds
        trackActivity({
          user_id: userId,
          paper_id: paperId,
          activity_type: 'scroll',
          duration_seconds: duration,
          meta_info: { section_type: sectionType },
        }).catch(console.error);
      }
    };
  }, [paperId, sectionType, userId]);
}
