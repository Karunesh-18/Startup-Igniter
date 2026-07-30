// ============================================================
// useAnalysis — execution lifecycle hook
// Manages the full run-analysis flow with animated step progress
// ============================================================

import { useCallback, useRef, useState } from 'react';
import { runAnalysis } from '@/lib/api';
import type { AnalysisResult, AgentStep } from '@/lib/types';

// 20 real agents across Crews 1, 2, 3 (matching backend)
const AGENT_SEQUENCE: Omit<AgentStep, 'status' | 'progress'>[] = [
  // Crew 1 — Idea Validation (6)
  { id: 1,  name: 'Startup Idea Analyzer',      crew: 1, crewName: 'Idea Validation' },
  { id: 2,  name: 'Problem Statement Decoder',  crew: 1, crewName: 'Idea Validation' },
  { id: 3,  name: 'Customer Identification',    crew: 1, crewName: 'Idea Validation' },
  { id: 4,  name: 'Value Proposition Auditor',  crew: 1, crewName: 'Idea Validation' },
  { id: 5,  name: 'Category Classifier',        crew: 1, crewName: 'Idea Validation' },
  { id: 6,  name: 'Innovation Scoring Engine',  crew: 1, crewName: 'Idea Validation' },
  // Crew 2 — Market Research (7)
  { id: 7,  name: 'Market Research Analyst',    crew: 2, crewName: 'Market Research' },
  { id: 8,  name: 'Industry Analysis Agent',    crew: 2, crewName: 'Market Research' },
  { id: 9,  name: 'Trend Analysis Agent',       crew: 2, crewName: 'Market Research' },
  { id: 10, name: 'Competitor Discovery',       crew: 2, crewName: 'Market Research' },
  { id: 11, name: 'Competitor Comparison',      crew: 2, crewName: 'Market Research' },
  { id: 12, name: 'Customer Persona Generator', crew: 2, crewName: 'Market Research' },
  { id: 13, name: 'TAM/SAM/SOM Calculator',     crew: 2, crewName: 'Market Research' },
  // Crew 3 — Research & Patent (7)
  { id: 14, name: 'Patent Search Agent',        crew: 3, crewName: 'Research & Patent' },
  { id: 15, name: 'Research Paper Analyzer',    crew: 3, crewName: 'Research & Patent' },
  { id: 16, name: 'Existing Solution Analyzer', crew: 3, crewName: 'Research & Patent' },
  { id: 17, name: 'Innovation Gap Identifier',  crew: 3, crewName: 'Research & Patent' },
  { id: 18, name: 'Technology Readiness',       crew: 3, crewName: 'Research & Patent' },
  { id: 19, name: 'IP Strategy Architect',      crew: 3, crewName: 'Research & Patent' },
  { id: 20, name: 'Research & Patent Summarizer', crew: 3, crewName: 'Research & Patent' },
];

function makeInitialSteps(): AgentStep[] {
  return AGENT_SEQUENCE.map((a) => ({ ...a, status: 'pending', progress: 0 }));
}

export type AnalysisStatus = 'idle' | 'running' | 'done' | 'error';

export interface UseAnalysisReturn {
  status: AnalysisStatus;
  steps: AgentStep[];
  activeStep: number;
  result: AnalysisResult | null;
  error: string | null;
  submit: (ideaText: string, mockMode?: boolean) => void;
  reset: () => void;
}

export function useAnalysis(): UseAnalysisReturn {
  const [status, setStatus] = useState<AnalysisStatus>('idle');
  const [steps, setSteps] = useState<AgentStep[]>(makeInitialSteps());
  const [activeStep, setActiveStep] = useState(-1);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const cancelRef = useRef(false);

  const animateSteps = useCallback((onDone: () => void) => {
    let i = 0;
    cancelRef.current = false;

    const tick = () => {
      if (cancelRef.current || i >= AGENT_SEQUENCE.length) {
        onDone();
        return;
      }
      setActiveStep(i);
      setSteps((prev) =>
        prev.map((s, idx) => (idx === i ? { ...s, status: 'running', progress: 0 } : s))
      );

      // Animate progress bar for this step
      const stepDuration = 1600 + Math.random() * 800;
      const start = performance.now();
      const frame = (now: number) => {
        if (cancelRef.current) return;
        const p = Math.min((now - start) / stepDuration, 1);
        setSteps((prev) =>
          prev.map((s, idx) => (idx === i ? { ...s, progress: p } : s))
        );
        if (p < 1) {
          requestAnimationFrame(frame);
        } else {
          setSteps((prev) =>
            prev.map((s, idx) => (idx === i ? { ...s, status: 'done', progress: 1 } : s))
          );
          i++;
          setTimeout(tick, 300);
        }
      };
      requestAnimationFrame(frame);
    };

    tick();
  }, []);

  const submit = useCallback(
    (ideaText: string, mockMode = false) => {
      setStatus('running');
      setSteps(makeInitialSteps());
      setActiveStep(-1);
      setResult(null);
      setError(null);

      // Start animation & API call in parallel
      let apiDone = false;
      let animDone = false;
      let apiResult: AnalysisResult | null = null;
      let apiError: string | null = null;

      const tryFinish = () => {
        if (apiDone && animDone) {
          if (apiError) {
            setError(apiError);
            setStatus('error');
          } else {
            setResult(apiResult);
            setStatus('done');
          }
        }
      };

      // API call
      runAnalysis({ idea_text: ideaText, mock_mode: mockMode })
        .then((data) => {
          apiResult = data;
          apiDone = true;
          tryFinish();
        })
        .catch((err: Error) => {
          apiError = err.message;
          apiDone = true;
          cancelRef.current = true;
          tryFinish();
        });

      // Step animation — paced to cover ~40 seconds of UI feedback
      animateSteps(() => {
        animDone = true;
        tryFinish();
      });
    },
    [animateSteps]
  );

  const reset = useCallback(() => {
    cancelRef.current = true;
    setStatus('idle');
    setSteps(makeInitialSteps());
    setActiveStep(-1);
    setResult(null);
    setError(null);
  }, []);

  return { status, steps, activeStep, result, error, submit, reset };
}
