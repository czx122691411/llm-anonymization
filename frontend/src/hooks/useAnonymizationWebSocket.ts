/**
 * useAnonymizationWebSocket - WebSocket hook for real-time anonymization progress
 *
 * Submits an async anonymization task and listens via WebSocket for:
 * - TRACE step progress (5-step flow)
 * - RPS optimization attempts
 * - Per-iteration intermediate results
 * - Final completion/error
 * Falls back to polling if WebSocket disconnects.
 */

import { useState, useEffect, useRef, useCallback } from 'react';

const API_BASE = 'http://localhost:8000';
const WS_BASE = 'ws://localhost:8000';

// ── Data types from backend progress messages ──

export interface InferenceDetail {
  attribute: string;
  guess: string;
  certainty: number;
  inference?: string;
  success?: boolean;
}

export interface TRACEStepData {
  step: number;
  step_name: string;
  description: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  detail?: Record<string, any>;
}

export interface RPSStepData {
  stage: number;
  attempt: number;
  current_suffix: string;
  tried_suffix: string;
  probability: number;
  probability_before: number;
  probability_after: number;
  accepted: boolean;
  stopping_condition_met: boolean;
}

export interface IterationIntermediate {
  iteration: number;
  before_text: string;
  after_text: string;
  inferences: InferenceDetail[];
  attention_words: string[];
  leakage_chains: any[];
  improvements: string[];
  certainty_before: number;
  certainty_after: number;
}

export interface ExecutionState {
  wsConnected: boolean;
  taskId: string | null;
  status: 'idle' | 'connecting' | 'running' | 'completed' | 'failed';
  currentStep: string;
  progress: number;
  // TRACE step data
  traceSteps: TRACEStepData[];
  // RPS step data
  rpsSteps: RPSStepData[];
  // Per-iteration results
  iterations: IterationIntermediate[];
  // Final result
  result: any | null;
  error: string | null;
}

export function useAnonymizationWebSocket() {
  const [state, setState] = useState<ExecutionState>({
    wsConnected: false,
    taskId: null,
    status: 'idle',
    currentStep: '',
    progress: 0,
    traceSteps: [],
    rpsSteps: [],
    iterations: [],
    result: null,
    error: null,
  });

  const wsRef = useRef<WebSocket | null>(null);
  const taskIdRef = useRef<string | null>(null);
  const pollTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const mountedRef = useRef(true);

  // Cleanup on unmount
  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
      if (wsRef.current) wsRef.current.close();
      if (pollTimerRef.current) clearInterval(pollTimerRef.current);
    };
  }, []);

  const connectWebSocket = useCallback((taskId: string) => {
    if (wsRef.current) wsRef.current.close();

    const ws = new WebSocket(`${WS_BASE}/api/unified/progress/${taskId}`);
    wsRef.current = ws;

    ws.onopen = () => {
      if (!mountedRef.current) return;
      setState(prev => ({ ...prev, wsConnected: true, status: 'running' }));
    };

    ws.onmessage = (event) => {
      if (!mountedRef.current) return;
      try {
        const msg = JSON.parse(event.data);

        switch (msg.type) {
          case 'connected':
            setState(prev => ({ ...prev, status: 'running' }));
            break;

          case 'progress': {
            const data = msg.data;
            const traceStep = data.trace_step || null;
            const rpsStep = data.rps_step || null;
            const intermediate = data.intermediate || null;

            setState(prev => {
              const updates: Partial<ExecutionState> = {
                currentStep: data.step_name || prev.currentStep,
                progress: data.step_progress || prev.progress,
              };

              // Append TRACE step data if present
              if (traceStep) {
                updates.traceSteps = [...prev.traceSteps, traceStep];
              }

              // Append RPS step data if present
              if (rpsStep) {
                updates.rpsSteps = [...prev.rpsSteps, rpsStep];
              }

              // Append iteration intermediate if present
              if (intermediate) {
                updates.iterations = [...prev.iterations, intermediate];
              }

              return { ...prev, ...updates };
            });
            break;
          }

          case 'complete':
            setState(prev => ({
              ...prev,
              status: 'completed',
              result: msg.result || null,
              progress: 100,
            }));
            // Close WebSocket after completion
            ws.close();
            break;

          case 'error':
            setState(prev => ({
              ...prev,
              status: 'failed',
              error: msg.error?.message || msg.message || 'Unknown error',
            }));
            ws.close();
            break;

          case 'cancelled':
            setState(prev => ({
              ...prev,
              status: 'failed',
              error: 'Task was cancelled',
            }));
            ws.close();
            break;
        }
      } catch (e) {
        console.error('Failed to parse WS message:', e);
      }
    };

    ws.onclose = () => {
      if (!mountedRef.current) return;
      setState(prev => ({ ...prev, wsConnected: false }));
    };

    ws.onerror = (e) => {
      console.error('WebSocket error:', e);
      if (!mountedRef.current) return;
      setState(prev => ({ ...prev, wsConnected: false }));
    };
  }, []);

  const startPolling = useCallback((taskId: string) => {
    if (pollTimerRef.current) clearInterval(pollTimerRef.current);

    pollTimerRef.current = setInterval(async () => {
      if (!mountedRef.current) return;
      try {
        const res = await fetch(`${API_BASE}/api/unified/task/${taskId}`);
        if (!res.ok) return;
        const data = await res.json();

        if (data.status === 'completed') {
          setState(prev => ({
            ...prev,
            status: 'completed',
            result: data.result || null,
            progress: 100,
          }));
          if (pollTimerRef.current) clearInterval(pollTimerRef.current);
        } else if (data.status === 'failed') {
          setState(prev => ({
            ...prev,
            status: 'failed',
            error: data.error?.message || 'Task failed',
          }));
          if (pollTimerRef.current) clearInterval(pollTimerRef.current);
        } else if (data.progress) {
          setState(prev => ({
            ...prev,
            currentStep: data.progress.step_name || prev.currentStep,
            progress: data.progress.step_progress || prev.progress,
          }));
        }
      } catch {
        // Polling failed silently, will retry
      }
    }, 2000);
  }, []);

  const submitTask = useCallback(async (requestBody: any) => {
    // Reset state
    setState({
      wsConnected: false,
      taskId: null,
      status: 'connecting',
      currentStep: '',
      progress: 0,
      traceSteps: [],
      rpsSteps: [],
      iterations: [],
      result: null,
      error: null,
    });

    try {
      // Submit async task
      const submitRes = await fetch(`${API_BASE}/api/unified/anonymize/async`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...requestBody,
          options: {
            ...requestBody.options,
            enable_progress_stream: true,
          },
        }),
      });

      if (!submitRes.ok) {
        const errData = await submitRes.json().catch(() => ({}));
        throw new Error(errData.detail || `HTTP ${submitRes.status}`);
      }

      const submitData = await submitRes.json();
      const taskId = submitData.task_id;
      taskIdRef.current = taskId;

      setState(prev => ({ ...prev, taskId }));

      // Connect WebSocket and start polling fallback
      connectWebSocket(taskId);
      startPolling(taskId);

    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to submit task';
      setState(prev => ({ ...prev, status: 'failed', error: message }));
    }
  }, [connectWebSocket, startPolling]);

  const cancelTask = useCallback(async () => {
    const taskId = taskIdRef.current;
    if (!taskId) return;
    try {
      await fetch(`${API_BASE}/api/unified/task/${taskId}/cancel`, { method: 'POST' });
    } catch {
      // Ignore cancel errors
    }
    if (wsRef.current) wsRef.current.close();
    if (pollTimerRef.current) clearInterval(pollTimerRef.current);
    setState(prev => ({ ...prev, status: 'idle', error: 'Cancelled' }));
  }, []);

  const reset = useCallback(() => {
    if (wsRef.current) wsRef.current.close();
    if (pollTimerRef.current) clearInterval(pollTimerRef.current);
    setState({
      wsConnected: false,
      taskId: null,
      status: 'idle',
      currentStep: '',
      progress: 0,
      traceSteps: [],
      rpsSteps: [],
      iterations: [],
      result: null,
      error: null,
    });
  }, []);

  return {
    ...state,
    submitTask,
    cancelTask,
    reset,
  };
}
