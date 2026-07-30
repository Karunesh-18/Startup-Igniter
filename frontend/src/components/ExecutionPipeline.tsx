import { useEffect, useState } from 'react';
import { PIPELINE, CREWS } from '@/data/crews';
import * as Icons from 'lucide-react';

type StageState = 'pending' | 'running' | 'done';

export default function ExecutionPipeline({ running, onComplete }: { running: boolean; onComplete?: () => void }) {
  const [activeStage, setActiveStage] = useState(-1);
  const [stageProgress, setStageProgress] = useState<Record<number, number>>({});
  const [states, setStates] = useState<StageState[]>(Array(12).fill('pending'));

  useEffect(() => {
    if (!running) {
      setActiveStage(-1);
      setStates(Array(12).fill('pending'));
      setStageProgress({});
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
      let p = 0;
      const dur = 1400 + Math.random() * 600;
      const start = performance.now();
      const tick = (now: number) => {
        if (cancelled) return;
        p = Math.min((now - start) / dur, 1);
        setStageProgress((sp) => ({ ...sp, [stage]: p }));
        if (p < 1) {
          requestAnimationFrame(tick);
        } else {
          setStates((s) => s.map((v, i) => (i === stage ? 'done' : v)));
          stage++;
          setTimeout(runStage, 350);
        }
      };
      requestAnimationFrame(tick);
    };
    runStage();
    return () => {
      cancelled = true;
    };
  }, [running, onComplete]);

  return (
    <div className="relative">
      {/* Vertical pipeline */}
      <div className="relative mx-auto max-w-2xl">
        {/* Central line */}
        <div className="absolute left-[27px] top-0 h-full w-px bg-gradient-to-b from-electric via-violet to-pink opacity-30 md:left-1/2 md:-translate-x-1/2" />

        <div className="space-y-3">
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
                className={`relative flex items-center gap-4 transition-all duration-500 ${
                  i % 2 === 1 ? 'md:flex-row-reverse' : ''
                } ${isActive ? 'scale-[1.02]' : 'scale-100'}`}
              >
                {/* Node */}
                <div className="relative z-10 flex-shrink-0 md:w-full md:flex md:justify-center">
                  <div
                    className="relative flex h-14 w-14 items-center justify-center rounded-2xl border transition-all duration-500"
                    style={{
                      borderColor: isDone || isRunning ? crew.color : 'rgba(255,255,255,0.08)',
                      background: isDone || isRunning
                        ? `linear-gradient(135deg, ${crew.color}22, ${crew.color2}11)`
                        : 'rgba(255,255,255,0.02)',
                      boxShadow: isRunning ? `0 0 30px -4px ${crew.color}88` : isDone ? `0 0 16px -6px ${crew.color}66` : 'none',
                    }}
                  >
                    {isRunning && (
                      <span
                        className="absolute inset-0 rounded-2xl animate-ping-ring"
                        style={{ border: `1px solid ${crew.color}` }}
                      />
                    )}
                    <Icon
                      className="h-5 w-5 transition-colors duration-500"
                      style={{ color: isDone || isRunning ? crew.color : 'rgba(255,255,255,0.3)' }}
                    />
                    {isDone && (
                      <span className="absolute -right-1 -top-1 flex h-4 w-4 items-center justify-center rounded-full bg-emerald text-[8px] text-void">
                        <Icons.Check className="h-2.5 w-2.5" strokeWidth={4} />
                      </span>
                    )}
                  </div>
                </div>

                {/* Card */}
                <div className="flex-1 md:flex md:w-full md:justify-center">
                  <div
                    className={`gradient-border-hover noise w-full overflow-hidden rounded-2xl bg-charcoal/60 p-4 backdrop-blur-sm transition-all duration-500 md:max-w-xs ${
                      isActive ? 'opacity-100' : 'opacity-70'
                    }`}
                    style={{
                      borderColor: isActive ? `${crew.color}33` : undefined,
                    }}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-[10px] text-white/30">{String(stage.id).padStart(2, '0')}</span>
                        <h4 className="text-sm font-medium text-white">{stage.name}</h4>
                      </div>
                      <span
                        className="rounded-full px-2 py-0.5 text-[9px] font-medium uppercase tracking-wider"
                        style={{
                          background: isDone ? 'rgba(16,185,129,0.15)' : isRunning ? `${crew.color}22` : 'rgba(255,255,255,0.05)',
                          color: isDone ? '#10b981' : isRunning ? crew.color : 'rgba(255,255,255,0.4)',
                        }}
                      >
                        {isDone ? 'Done' : isRunning ? 'Running' : 'Queued'}
                      </span>
                    </div>
                    <p className="mt-1.5 text-xs leading-relaxed text-white/50">{stage.description}</p>

                    {/* Progress bar */}
                    <div className="mt-3 h-1 overflow-hidden rounded-full bg-white/5">
                      <div
                        className="h-full rounded-full transition-all duration-100"
                        style={{
                          width: `${(isDone ? 100 : prog * 100)}%`,
                          background: `linear-gradient(90deg, ${crew.color}, ${crew.color2})`,
                          boxShadow: isRunning ? `0 0 8px ${crew.color}` : 'none',
                        }}
                      />
                    </div>

                    {/* Metrics */}
                    <div className="mt-3 flex gap-4">
                      {stage.metrics.map((m) => (
                        <div key={m.label}>
                          <div className="text-[9px] uppercase tracking-wider text-white/30">{m.label}</div>
                          <div className="font-mono text-xs font-medium text-white/70">{m.value}</div>
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
    </div>
  );
}
