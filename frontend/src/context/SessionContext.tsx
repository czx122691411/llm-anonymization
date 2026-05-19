import React, { createContext, useContext, useReducer, useCallback } from 'react';

// ---- Types ----
export type CommentStatus = 'pending' | 'processing' | 'done' | 'rejected';

export interface Comment {
  index: number;
  originalText: string;
  status: CommentStatus;
  rounds: AnonymizationRound[];
  riskScore: number;
  finalAnonymizedText: string | null;
}

export interface AnonymizationRound {
  roundNum: number;
  anonymizedText: string;
  inferences: Record<string, AttrInference>;
  maxConfidence: number;
  quality: QualityScores | null;
}

export interface AttrInference {
  attribute: string;
  guesses: string[];
  confidence: number;
  inference: string;
  hitGroundTruth: boolean | null;
}

export interface QualityScores {
  privacy_protection: number;
  utility_preservation: number;
  text_quality: number;
  inference_blocking: number;
}

export interface PrivacySnapshot {
  commentCount: number;
  attributeConfidences: Record<string, number>;
  maxConfidence: number;
}

interface SessionState {
  sessionId: string;
  persona: Record<string, string>;
  comments: Comment[];
  privacyHistory: PrivacySnapshot[];
  selectedCommentIndex: number;
  selectedRound: number;
}

type SessionAction =
  | { type: 'ADD_COMMENT'; text: string }
  | { type: 'DELETE_COMMENT'; index: number }
  | { type: 'SET_COMMENT_STATUS'; index: number; status: CommentStatus }
  | { type: 'ADD_ROUND_RESULT'; index: number; round: AnonymizationRound }
  | { type: 'SELECT_COMMENT'; index: number }
  | { type: 'SELECT_ROUND'; round: number }
  | { type: 'SET_PERSONA'; persona: Record<string, string> }
  | { type: 'ADD_PRIVACY_SNAPSHOT'; snapshot: PrivacySnapshot }
  | { type: 'UPDATE_RISK_SCORE'; index: number; score: number }
  | { type: 'LOAD_SESSION'; data: { sessionId: string; persona: Record<string, string>; comments: any[]; privacyHistory?: PrivacySnapshot[] } }
  | { type: 'RESET' };

// ---- Reducer ----
function sessionReducer(state: SessionState, action: SessionAction): SessionState {
  switch (action.type) {
    case 'ADD_COMMENT': {
      const newComment: Comment = {
        index: state.comments.length,
        originalText: action.text,
        status: 'pending',
        rounds: [],
        riskScore: 0,
        finalAnonymizedText: null,
      };
      return { ...state, comments: [...state.comments, newComment] };
    }
    case 'DELETE_COMMENT':
      return {
        ...state,
        comments: state.comments
          .filter((_, i) => i !== action.index)
          .map((c, i) => ({ ...c, index: i })),
      };
    case 'SET_COMMENT_STATUS':
      return {
        ...state,
        comments: state.comments.map((c) =>
          c.index === action.index ? { ...c, status: action.status } : c
        ),
      };
    case 'ADD_ROUND_RESULT':
      return {
        ...state,
        comments: state.comments.map((c) =>
          c.index === action.index
            ? {
                ...c,
                rounds: [...c.rounds, action.round],
                finalAnonymizedText: action.round.anonymizedText,
              }
            : c
        ),
      };
    case 'SELECT_COMMENT':
      return { ...state, selectedCommentIndex: action.index, selectedRound: 0 };
    case 'SELECT_ROUND':
      return { ...state, selectedRound: action.round };
    case 'SET_PERSONA':
      return { ...state, persona: action.persona };
    case 'ADD_PRIVACY_SNAPSHOT':
      return { ...state, privacyHistory: [...state.privacyHistory, action.snapshot] };
    case 'UPDATE_RISK_SCORE':
      return {
        ...state,
        comments: state.comments.map((c) =>
          c.index === action.index ? { ...c, riskScore: action.score } : c
        ),
      };
    case 'LOAD_SESSION': {
      const comments: Comment[] = (action.data.comments || []).map((c: any, i: number) => ({
        index: i,
        originalText: c.original_text || c.originalText || '',
        status: (c.status || 'done') as CommentStatus,
        riskScore: c.risk_score || c.riskScore || 0,
        finalAnonymizedText: c.rounds?.[c.rounds.length - 1]?.anonymized_text || null,
        rounds: (c.rounds || []).map((r: any, ri: number) => ({
          roundNum: r.round_num ?? r.roundNum ?? ri,
          anonymizedText: r.anonymized_text || r.anonymizedText || '',
          inferences: { test: r.inferences || [], chains: r.chains || [] } as any,
          maxConfidence: r.max_confidence ?? r.maxConfidence ?? 0,
          quality: r.quality || null,
        })),
      }));
      return {
        ...state,
        sessionId: action.data.sessionId || state.sessionId,
        persona: action.data.persona || {},
        comments,
        privacyHistory: action.data.privacyHistory || [],
        selectedCommentIndex: 0,
        selectedRound: 0,
      };
    }
    case 'RESET':
      return createInitialState();
    default:
      return state;
  }
}

function createInitialState(): SessionState {
  return {
    sessionId: `session_${Date.now()}`,
    persona: {},
    comments: [],
    privacyHistory: [],
    selectedCommentIndex: 0,
    selectedRound: 0,
  };
}

// ---- Context ----
interface SessionContextValue {
  state: SessionState;
  addComment: (text: string) => void;
  deleteComment: (index: number) => void;
  setCommentStatus: (index: number, status: CommentStatus) => void;
  addRoundResult: (index: number, round: AnonymizationRound) => void;
  selectComment: (index: number) => void;
  selectRound: (round: number) => void;
  setPersona: (persona: Record<string, string>) => void;
  addPrivacySnapshot: (snapshot: PrivacySnapshot) => void;
  updateRiskScore: (index: number, score: number) => void;
  loadSession: (data: any) => void;
  reset: () => void;
  selectedComment: Comment | null;
}

const SessionContext = createContext<SessionContextValue | null>(null);

export const SessionProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [state, dispatch] = useReducer(sessionReducer, undefined, createInitialState);

  const addComment = useCallback((text: string) => dispatch({ type: 'ADD_COMMENT', text }), []);
  const deleteComment = useCallback((index: number) => dispatch({ type: 'DELETE_COMMENT', index }), []);
  const setCommentStatus = useCallback(
    (index: number, status: CommentStatus) => dispatch({ type: 'SET_COMMENT_STATUS', index, status }),
    []
  );
  const addRoundResult = useCallback(
    (index: number, round: AnonymizationRound) => dispatch({ type: 'ADD_ROUND_RESULT', index, round }),
    []
  );
  const selectComment = useCallback((index: number) => dispatch({ type: 'SELECT_COMMENT', index }), []);
  const selectRound = useCallback((round: number) => dispatch({ type: 'SELECT_ROUND', round }), []);
  const setPersona = useCallback(
    (persona: Record<string, string>) => dispatch({ type: 'SET_PERSONA', persona }),
    []
  );
  const addPrivacySnapshot = useCallback(
    (snapshot: PrivacySnapshot) => dispatch({ type: 'ADD_PRIVACY_SNAPSHOT', snapshot }),
    []
  );
  const updateRiskScore = useCallback(
    (index: number, score: number) => dispatch({ type: 'UPDATE_RISK_SCORE', index, score }),
    []
  );
  const loadSession = useCallback((data: any) => dispatch({ type: 'LOAD_SESSION', data }), []);
  const reset = useCallback(() => dispatch({ type: 'RESET' }), []);

  const selectedComment =
    state.comments.length > 0 && state.selectedCommentIndex < state.comments.length
      ? state.comments[state.selectedCommentIndex]
      : null;

  return (
    <SessionContext.Provider
      value={{
        state,
        addComment,
        deleteComment,
        setCommentStatus,
        addRoundResult,
        selectComment,
        selectRound,
        setPersona,
        addPrivacySnapshot,
        updateRiskScore,
        loadSession,
        reset,
        selectedComment,
      }}
    >
      {children}
    </SessionContext.Provider>
  );
};

export function useSession(): SessionContextValue {
  const ctx = useContext(SessionContext);
  if (!ctx) throw new Error('useSession must be used within SessionProvider');
  return ctx;
}
