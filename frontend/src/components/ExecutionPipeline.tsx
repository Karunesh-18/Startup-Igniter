import { useEffect, useRef, useState } from 'react';
import { PIPELINE, CREWS } from '@/data/crews';
import * as Icons from 'lucide-react';

type StageState = 'pending' | 'running' | 'done';

/* ── Light-flow particle drawn between consecutive nodes ─────────────── */
function FlowParticle({ color, progress }: { color: string; progress: number }) {
  // progress: 0→1, where it is along the connector line (top→bottom)
  const top = `${progress * 100}%`;
  return (
    <span
      className="absolute left-1/2 -translate-x-1/2 pointer-events-none"
      style={{
        top,
        width: 8,
        height: 8,
        borderRadius: '50%',
        background: color,
        boxShadow: `0 0 12px 4px ${color}cc, 0 0 24px 8px ${color}66`,
        transform: 'translateX(-50%)',
        transition: 'top 0.05s linear',
        opacity: 0.95,
        zIndex: 20,
      }}
    />
  );
}

export default function ExecutionPipeline({ running, onComplete }: { running: boolean; onComplete?: () => void }) {
  const [activeStage, setActiveStage] = useState(-1);
  const [stageProgress, setStageProgress] = useState<Record<number, number>>({});
  const [states, setStates] = useState<StageState[]>(Array(12).fill('pending'));
  // flowProgress: 0→1 how far the light has travelled from node i to node i+1
  const [flowProgress, setFlowProgress] = useState<Record<number, number>>({});
  const stageRefs = useRef<(HTMLDivElement | null)[]>([]);
  const containerRef = useRef<HTMLDivElement>(null);

  // reset
  useEffect(() => {
    if (!running) {
      setActiveStage(-1);
      setStates(Array(12).fill('pending'));
      setStageProgress({});
      setFlowProgress({});
      return;
    }

    let cancelled = false;
    let stage = 0;

    const runStage = () => {
      if (cancelled || stage >= 12) {
        if (!cancelled) onComplete?.();
        return;
      }

      setActiveStage(stage);
      setStates((s) => s.map((v, i) => (i === stage ? 'running' : v)));

      // Scroll active stage into view smoothly
      setTimeout(() => {
        stageRefs.current[stage]?.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }, 80);

      let p = 0;
      const dur = 1600 + Math.random() * 800;
      const start = performance.now();

      const tick = (now: number) => {
        if (cancelled) return;
        p = Math.min((now - start) / dur, 1);
        setStageProgress((sp) => ({ ...sp, [stage]: p }));
        if (p < 1) {
          requestAnimationFrame(tick);
        } else {
          setStates((s) => s.map((v, i) => (i === stage ? 'done' : v)));
          // animate the flow particle from this stage to next
          if (stage < 11) {
            animateFlow(stage, () => {
              stage++;
              setTimeout(runStage, 200);
            });
          } else {
            stage++;
            setTimeout(runStage, 200);
          }
        }
      };
      requestAnimationFrame(tick);
    };

    // Animate a light flowing downward from stageIdx to stageIdx+1
    const animateFlow = (from: number, done: () => void) => {
      const flowDur = 500;
      const start = performance.now();
      const go = (now: number) => {
        if (cancelled) return;
        const t = Math.min((now - start) / flowDur, 1);
        setFlowProgress((fp) => ({ ...fp, [from]: t }));
        if (t < 1) {
          requestAnimationFrame(go);
        } else {
          done();
        }
      };
      setFlowProgress((fp) => ({ ...fp, [from]: 0 }));
      requestAnimationFrame(go);
    };

    runStage();
    return () => { cancelled = true; };
  }, [running, onComplete]);

  return (
    <div ref={containerRef} className="relative">
      {/* Vertical central spine */}
      <div className="absolute left-[35px] top-0 h-full w-px md:left-1/2 md:-translate-x-1/2"
        style={{
          background: 'linear-gradient(to bottom, #2d7ff9, #8b5cf6, #ec4899)',
          opacity: 0.18,
        }}
      />

      {/* Flowing light segments — one per gap between stages */}
      {PIPELINE.slice(0, 11).map((stage, i) => {
        const t = flowProgress[i];
        if (t === undefined || t <= 0 || t >= 1) return null;
        const crew = CREWS[stage.crew - 1];
        return (
          <div
            key={`flow-${i}`}
            className="absolute left-[35px] md:left-1/2"
            style={{
              top: 0,
              width: 1,
              height: '100%',
              pointerEvents: 'none',
              zIndex: 15,
            }}
          >
            <FlowParticle color={crew.color} progress={t} />
          </div>
        );
      })}

      <div className="space-y-4">
        {PIPELINE.map((stage, i) => {
          const crew = CREWS[stage.crew - 1];
          const state = states[i];
          const prog = stageProgress[i] ?? 0;
          const Icon = (Icons as any)[stage.icon] ?? Icons.Circle;
          const isActive = i === activeStage;
          const isDone = state === 'done';
          const isRunning = state === 'running';

          return (
            <div
              key={stage.id}
              ref={(el) => { stageRefs.current[i] = el; }}
              className={`relative flex items-center gap-4 transition-all duration-700 ${
                i % 2 === 1 ? 'md:flex-row-reverse' : ''
              } ${isActive ? 'scale-[1.015]' : 'scale-100'}`}
            >
              {/* ── Node bubble ── */}
              <div className="relative z-10 flex-shrink-0 md:w-full md:flex md:justify-center">
                <div
                  className="relative flex h-[70px] w-[70px] items-center justify-center rounded-2xl border transition-all duration-500"
                  style={{
                    borderColor: isDone || isRunning ? crew.color : 'rgba(255,255,255,0.07)',
                    background:
                      isDone || isRunning
                        ? `linear-gradient(135deg, ${crew.color}28, ${crew.color2}14)`
                        : 'rgba(255,255,255,0.02)',
                    boxShadow: isRunning
                      ? `0 0 40px -4px ${crew.color}99, 0 0 80px -16px ${crew.color}55`
                      : isDone
                      ? `0 0 20px -6px ${crew.color}66`
                      : 'none',
                  }}
                >
                  {/* Pulsing ring on running */}
                  {isRunning && (
                    <>
                      <span
                        className="absolute inset-0 rounded-2xl animate-ping-ring"
                        style={{ border: `1.5px solid ${crew.color}` }}
                      />
                      <span
                        className="absolute inset-[-6px] rounded-[18px] animate-ping-ring"
                        style={{ border: `1px solid ${crew.color}55`, animationDelay: '0.4s' }}
                      />
                    </>
                  )}

                  <Icon
                    className="h-6 w-6 transition-colors duration-500"
                    style={{ color: isDone || isRunning ? crew.color : 'rgba(255,255,255,0.25)' }}
                  />

                  {isDone && (
                    <span className="absolute -right-1.5 -top-1.5 flex h-5 w-5 items-center justify-center rounded-full bg-emerald text-[8px] text-void">
                      <Icons.Check className="h-3 w-3" strokeWidth={4} />
                    </span>
                  )}
                </div>
              </div>

              {/* ── Card ── */}
              <div className="flex-1 md:flex md:w-full md:justify-center">
                <div
                  className={`gradient-border-hover noise w-full overflow-hidden rounded-2xl bg-charcoal/60 p-5 backdrop-blur-sm transition-all duration-500 md:max-w-sm ${
                    isActive ? 'opacity-100' : 'opacity-60'
                  }`}
                  style={{
                    borderColor: isRunning ? `${crew.color}44` : undefined,
                    boxShadow: isRunning ? `0 0 0 1px ${crew.color}22, inset 0 0 30px ${crew.color}08` : undefined,
                  }}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-[10px] text-white/30">{String(stage.id).padStart(2, '0')}</span>
                      <h4 className="text-sm font-medium text-white">{stage.name}</h4>
                    </div>
                    <span
                      className="rounded-full px-2 py-0.5 text-[9px] font-medium uppercase tracking-wider transition-all duration-300"
                      style={{
                        background: isDone
                          ? 'rgba(16,185,129,0.15)'
                          : isRunning
                          ? `${crew.color}22`
                          : 'rgba(255,255,255,0.05)',
                        color: isDone ? '#10b981' : isRunning ? crew.color : 'rgba(255,255,255,0.35)',
                      }}
                    >
                      {isDone ? 'Done' : isRunning ? 'Running' : 'Queued'}
                    </span>
                  </div>

                  <p className="mt-2 text-xs leading-relaxed text-white/45">{stage.description}</p>

                  {/* Progress bar with glow */}
                  <div className="mt-3 h-1 overflow-hidden rounded-full bg-white/5">
                    <div
                      className="h-full rounded-full transition-all duration-100"
                      style={{
                        width: `${isDone ? 100 : prog * 100}%`,
                        background: `linear-gradient(90deg, ${crew.color}, ${crew.color2})`,
                        boxShadow: isRunning ? `0 0 10px 2px ${crew.color}99` : 'none',
                      }}
                    />
                  </div>

                  {/* Metrics */}
                  <div className="mt-3 flex gap-4">
                    {stage.metrics.map((m) => (
                      <div key={m.label}>
                        <div className="text-[9px] uppercase tracking-wider text-white/30">{m.label}</div>
                        <div
                          className="font-mono text-xs font-medium transition-colors duration-300"
                          style={{ color: isDone || isRunning ? crew.color : 'rgba(255,255,255,0.5)' }}
                        >
                          {m.value}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
