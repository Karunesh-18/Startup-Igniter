import { useEffect, useState } from 'react';
import { Rocket, Menu, X } from 'lucide-react';

interface Props {
  onLaunch: () => void;
  onHome: () => void;
  onPhases: () => void;
  onAgents: () => void;
}

export default function Nav({ onLaunch, onHome, onPhases, onAgents }: Props) {
  const [scrolled, setScrolled] = useState(false);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 30);
    window.addEventListener('scroll', onScroll);
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  const links = [
    { label: 'Platform', href: '#platform' },
    { label: 'Crews', href: '#crews' },
    { label: 'Pipeline', href: '#pipeline' },
  ];

  return (
    <nav
      className={`fixed left-0 right-0 top-0 z-50 transition-all duration-500 ${
        scrolled ? 'border-b border-white/5 bg-void/70 backdrop-blur-xl' : 'bg-transparent'
      }`}
    >
      <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
        <button onClick={onHome} className="group flex items-center gap-2.5">
          <div className="relative flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-electric via-indigo to-violet shadow-lg shadow-electric/30 transition-transform group-hover:scale-110">
            <Rocket className="h-4.5 w-4.5 text-white" />
            <span className="absolute inset-0 rounded-xl bg-gradient-to-br from-electric to-violet opacity-0 blur-md transition-opacity group-hover:opacity-60" />
          </div>
          <div className="flex flex-col leading-none">
            <span className="text-sm font-semibold tracking-tight text-white">Startup Igniter</span>
            <span className="font-mono text-[9px] uppercase tracking-[0.25em] text-white/40">AI Operating System</span>
          </div>
        </button>

        <div className="hidden items-center gap-8 md:flex">
          {links.map((l) => (
            <a key={l.label} href={l.href} className="group relative text-sm text-white/60 transition-colors hover:text-white">
              {l.label}
              <span className="absolute -bottom-1 left-0 h-px w-0 bg-gradient-to-r from-electric to-violet transition-all duration-300 group-hover:w-full" />
            </a>
          ))}
          <button onClick={onPhases} className="group relative text-sm text-white/60 transition-colors hover:text-white">
            Phases
            <span className="absolute -bottom-1 left-0 h-px w-0 bg-gradient-to-r from-electric to-violet transition-all duration-300 group-hover:w-full" />
          </button>
          <button onClick={onAgents} className="group relative text-sm text-white/60 transition-colors hover:text-white">
            Agents
            <span className="absolute -bottom-1 left-0 h-px w-0 bg-gradient-to-r from-electric to-violet transition-all duration-300 group-hover:w-full" />
          </button>
        </div>

        <div className="hidden items-center gap-3 md:flex">
          <button onClick={onPhases} className="btn-ghost rounded-full px-4 py-2 text-sm text-white/80">
            Phases
          </button>
          <button onClick={onLaunch} className="btn-primary rounded-full px-5 py-2 text-sm font-medium">
            Launch Mission
          </button>
        </div>

        <button onClick={() => setOpen(!open)} className="rounded-lg border border-white/10 p-2 md:hidden">
          {open ? <X className="h-5 w-5 text-white" /> : <Menu className="h-5 w-5 text-white" />}
        </button>
      </div>

      {open && (
        <div className="border-t border-white/5 bg-void/95 px-6 py-4 backdrop-blur-xl md:hidden">
          <div className="flex flex-col gap-3">
            {links.map((l) => (
              <a key={l.label} href={l.href} onClick={() => setOpen(false)} className="text-sm text-white/70">
                {l.label}
              </a>
            ))}
            <button onClick={() => { onPhases(); setOpen(false); }} className="text-left text-sm text-white/70">
              Phases
            </button>
            <button onClick={() => { onAgents(); setOpen(false); }} className="text-left text-sm text-white/70">
              Agents
            </button>
            <button onClick={onLaunch} className="btn-primary mt-2 rounded-full px-5 py-2 text-sm font-medium">
              Launch Mission
            </button>
          </div>
        </div>
      )}
    </nav>
  );
}
