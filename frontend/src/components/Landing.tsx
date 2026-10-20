import { lazy, Suspense, useEffect, useRef, useState, type FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useReducedMotion } from 'motion/react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import Lenis from 'lenis';
import 'lenis/dist/lenis.css';
import { ArrowRight } from 'lucide-react';
import { CREWS } from '@/data/crews';
import { CREW_ICONS } from '@/lib/icons';
import { cn } from '@/lib/utils';
import { Button, buttonVariants } from '@/components/ui/button';
import { Spotlight } from '@/components/ui/spotlight';
import { BackgroundBeams } from '@/components/ui/background-beams';
import { BentoGrid, BentoGridItem } from '@/components/ui/bento-grid';

const ShaderHero = lazy(() => import('./ShaderHero'));

gsap.registerPlugin(ScrollTrigger);

// Static stand-in for the WebGL gradient: shown while it loads and, for
// reduced-motion users, instead of it.
const STATIC_GRADIENT =
  'radial-gradient(ellipse 70% 60% at 80% 30%, rgba(139,92,246,0.35), transparent 70%), radial-gradient(ellipse 60% 60% at 20% 80%, rgba(45,127,249,0.3), transparent 70%)';

const STEPS = [
  { title: 'Describe the idea', body: 'One to three sentences: who it is for and what it does. No deck, no form.' },
  { title: 'Twelve crews work through it', body: 'Each crew runs in order and reads what the earlier crews found, from validation and market sizing through patents, legal, and funding.' },
  { title: 'Read the report', body: 'Scores, market size, competitors, IP position, and a plan, grouped the way an investor would ask for them.' },
];

// Bento layout: the first crew (where every run starts) and the last (where
// it all lands) get the large cells.
const SPAN: Record<number, string> = { 1: 'lg:col-span-2 lg:row-span-2', 12: 'lg:col-span-2' };

/** Lenis smooth scroll + GSAP ScrollTrigger reveals, both skipped under reduced motion. */
function useScrollMotion(root: React.RefObject<HTMLElement>, enabled: boolean) {
  useEffect(() => {
    if (!enabled || !root.current) return;
    const lenis = new Lenis();
    lenis.on('scroll', ScrollTrigger.update);
    const tick = (t: number) => lenis.raf(t * 1000);
    gsap.ticker.add(tick);
    gsap.ticker.lagSmoothing(0);

    const ctx = gsap.context(() => {
      gsap.set('[data-reveal]', { autoAlpha: 0, y: 32 });
      ScrollTrigger.batch('[data-reveal]', {
        start: 'top 88%',
        once: true,
        onEnter: (els) => gsap.to(els, { autoAlpha: 1, y: 0, duration: 0.9, ease: 'power3.out', stagger: 0.08 }),
      });
    }, root);

    return () => {
      ctx.revert();
      gsap.ticker.remove(tick);
      lenis.destroy();
    };
  }, [root, enabled]);
}

export default function Landing() {
  const navigate = useNavigate();
  const reduce = useReducedMotion();
  const rootRef = useRef<HTMLDivElement>(null);
  const [idea, setIdea] = useState('');
  useScrollMotion(rootRef, !reduce);

  const start = (e: FormEvent) => {
    e.preventDefault();
    navigate('/analyze', { state: { idea: idea.trim() } });
  };

  return (
    <div ref={rootRef} className="relative bg-void">
      {/* ── Hero ── */}
      <section className="relative isolate flex min-h-[100svh] items-center overflow-hidden">
        <div className="absolute inset-0 -z-10" style={{ background: STATIC_GRADIENT }} />
        {!reduce && (
          <Suspense fallback={null}>
            <div className="absolute inset-0 -z-10 opacity-80">
              <ShaderHero />
            </div>
          </Suspense>
        )}
        <div className="absolute inset-0 -z-10 bg-gradient-to-b from-void/30 via-void/40 to-void" />
        <Spotlight className="-top-40 left-0 md:-top-20 md:left-60" />

        <div className="relative z-10 mx-auto w-full max-w-6xl px-4 pb-20 pt-32 sm:px-6">
          <h1 className="max-w-4xl font-serif text-[clamp(2.75rem,8vw,6.5rem)] leading-[0.95] tracking-[-0.01em] text-white">
            One idea in.
            <br />
            An investor-ready report out.
          </h1>
          <p className="mt-6 max-w-xl text-lg leading-relaxed text-white/70">
            Twelve specialist AI crews validate your startup idea, size the market, search prior art, and draft the plan,
            each building on what the last one found.
          </p>

          <form onSubmit={start} className="mt-10 max-w-2xl">
            <label htmlFor="hero-idea" className="sr-only">
              Your startup idea
            </label>
            <div className="flex flex-col gap-2 rounded-3xl border border-white/15 bg-void/60 p-2 backdrop-blur-xl sm:flex-row sm:items-center sm:rounded-full">
              <input
                id="hero-idea"
                value={idea}
                onChange={(e) => setIdea(e.target.value)}
                placeholder="e.g. Contract review for small law firms"
                className="min-w-0 flex-1 bg-transparent px-4 py-3 text-base text-white placeholder-white/35 focus:outline-none"
              />
              <Button type="submit" variant="shine" size="lg" className="w-full sm:w-auto">
                Analyze idea
                <ArrowRight className="h-4 w-4" aria-hidden="true" />
              </Button>
            </div>
          </form>
          <Link to="/phases" className="mt-5 inline-block text-sm text-white/55 underline-offset-4 hover:text-white hover:underline">
            Or browse the 12 crews first
          </Link>
        </div>
      </section>

      {/* ── How it works ── */}
      <section id="how" className="relative py-24 sm:py-32">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <h2 data-reveal className="max-w-2xl font-serif text-4xl leading-tight text-white sm:text-5xl">
            How a run works
          </h2>
          <ol className="mt-14 grid gap-px overflow-hidden rounded-2xl border border-white/[0.07] bg-white/[0.07] md:grid-cols-3">
            {STEPS.map((s, i) => (
              <li key={s.title} data-reveal className="bg-void p-6 sm:p-8">
                <span className="font-mono text-sm text-electric-300">{i + 1}</span>
                <h3 className="mt-6 text-xl font-medium text-white">{s.title}</h3>
                <p className="mt-2 leading-relaxed text-white/55">{s.body}</p>
              </li>
            ))}
          </ol>
        </div>
      </section>

      {/* ── Crews ── */}
      <section id="crews" className="relative pb-24 sm:pb-32">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <div data-reveal className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
            <h2 className="max-w-2xl font-serif text-4xl leading-tight text-white sm:text-5xl">The twelve crews</h2>
            <Link to="/agents" className="text-sm text-white/55 underline-offset-4 hover:text-white hover:underline">
              See all {CREWS.reduce((n, c) => n + c.agents.length, 0)} agents
            </Link>
          </div>

          <BentoGrid className="mt-12">
            {CREWS.map((crew) => {
              const Icon = CREW_ICONS[crew.icon];
              const big = crew.id === 1;
              return (
                <Link
                  key={crew.id}
                  to={`/phases/${crew.id}`}
                  data-reveal
                  className={cn('group rounded-2xl', SPAN[crew.id])}
                >
                  <BentoGridItem
                    className="h-full transition-colors duration-300 group-hover:border-white/20"
                    icon={
                      <span
                        className="flex h-10 w-10 items-center justify-center rounded-xl"
                        style={{ background: `${crew.color}1f`, color: crew.color }}
                      >
                        {Icon && <Icon className="h-5 w-5" aria-hidden="true" />}
                      </span>
                    }
                    header={<span className="font-mono text-xs text-white/35">{String(crew.id).padStart(2, '0')}</span>}
                    title={crew.name}
                    description={`${crew.agents.length} agents`}
                  >
                    {big && (
                      <ul className="mt-5 space-y-2 text-sm text-white/60">
                        {crew.agents.map((a) => (
                          <li key={a.id} className="flex items-center gap-2">
                            <span className="h-1 w-1 rounded-full" style={{ background: crew.color }} />
                            {a.name}
                          </li>
                        ))}
                      </ul>
                    )}
                  </BentoGridItem>
                </Link>
              );
            })}
          </BentoGrid>
        </div>
      </section>

      {/* ── CTA ── */}
      <section className="relative isolate overflow-hidden border-t border-white/[0.06] py-28 sm:py-36">
        <BackgroundBeams className="-z-10 opacity-70" />
        <div data-reveal className="mx-auto max-w-3xl px-4 text-center sm:px-6">
          <h2 className="font-serif text-4xl leading-tight text-white sm:text-6xl">Start with one sentence.</h2>
          <p className="mx-auto mt-5 max-w-md text-white/60">A full run takes a few minutes. You can watch each crew finish as it happens.</p>
          <Link to="/analyze" className={cn(buttonVariants({ variant: 'shine', size: 'lg' }), 'mt-10')}>
            Analyze an idea
          </Link>
        </div>
      </section>

      <footer className="border-t border-white/[0.06] py-10">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 px-4 text-sm text-white/40 sm:flex-row sm:px-6">
          <span>Startup Igniter</span>
          <span>AI-generated analysis. Verify before you act on it.</span>
        </div>
      </footer>
    </div>
  );
}
