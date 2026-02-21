import { useState, useEffect, useCallback, useRef } from 'react';
import { getTaskStatus } from '../api/tasks';
import type { TaskStatus } from '../api/types';

export function useTaskPolling(taskId: string | null, intervalMs = 2000) {
  const [task, setTask] = useState<TaskStatus | null>(null);
  const [isComplete, setIsComplete] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  useEffect(() => {
    if (!taskId) return;

    setIsComplete(false);
    setError(null);

    const poll = async () => {
      try {
        const status = await getTaskStatus(taskId);
        setTask(status);

        if (status.status === 'completed') {
          setIsComplete(true);
          stopPolling();
        } else if (status.status === 'failed') {
          setError(status.error_message || 'Task failed');
          stopPolling();
        }
      } catch (err) {
        setError('Failed to fetch task status');
        stopPolling();
      }
    };

    poll();
    intervalRef.current = setInterval(poll, intervalMs);

    return stopPolling;
  }, [taskId, intervalMs, stopPolling]);

  return { task, isComplete, error, stopPolling };
}
