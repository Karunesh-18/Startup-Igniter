import { useEffect, useRef, useState } from 'react';
import { Link, NavLink, useLocation, useNavigate } from 'react-router-dom';
import { ChevronDown, CreditCard, LogOut, Menu, Plug, Rocket, X } from 'lucide-react';
import { useAuth } from '@/lib/auth';
import { cn } from '@/lib/utils';
import { buttonVariants } from '@/components/ui/button';

const PUBLIC_LINKS = [
  { to: '/phases', label: 'Crews' },
  { to: '/agents', label: 'Agents' },
  { to: '/pricing', label: 'Pricing' },
];
const MEMBER_LINKS = [
  { to: '/app', label: 'Your ideas' },
  { to: '/pricing', label: 'Pricing' },
  { to: '/phases', label: 'Crews' },
];

export default function Nav() {
  const [scrolled, setScrolled] = useState(false);
  const [open, setOpen] = useState(false);
  const [menu, setMenu] = useState(false);
  const { pathname } = useLocation();
  const { user, signOut } = useAuth();
  const navigate = useNavigate();
  const menuRef = useRef<HTMLDivElement>(null);
  const links = user ? MEMBER_LINKS : PUBLIC_LINKS;

  useEffect(() => {
    setOpen(false);
    setMenu(false);
  }, [pathname]);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 30);
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  useEffect(() => {
    const close = (e: MouseEvent) => !menuRef.current?.contains(e.target as Node) && setMenu(false);
    document.addEventListener('mousedown', close);
    return () => document.removeEventListener('mousedown', close);
  }, []);

  const linkClass = ({ isActive }: { isActive: boolean }) =>
    cn('text-sm transition-colors hover:text-white', isActive ? 'text-white' : 'text-white/60');

  const leave = async () => {
    await signOut();
    navigate('/');
  };

  return (
    <nav
      className={cn(
        'fixed inset-x-0 top-0 z-50 transition-[background-color,border-color] duration-300',
        scrolled || open ? 'border-b border-white/5 bg-void/80 backdrop-blur-xl' : 'border-b border-transparent',
      )}
    >
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3 sm:px-6">
        <Link to={user ? '/app' : '/'} className="flex items-center gap-2.5">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-electric to-violet">
            <Rocket className="h-4 w-4 text-white" aria-hidden="true" />
          </span>
          <span className="text-sm font-semibold tracking-tight text-white">Startup Igniter</span>
        </Link>

        <div className="hidden items-center gap-8 md:flex">
          {links.map((l) => (
            <NavLink key={l.to} to={l.to} className={linkClass}>
              {l.label}
            </NavLink>
          ))}
          {user ? (
            <>
              <Link to="/new" className={buttonVariants({ size: 'sm' })}>
                New idea
              </Link>
              <div className="relative" ref={menuRef}>
                <button
                  onClick={() => setMenu((m) => !m)}
                  aria-expanded={menu}
                  aria-haspopup="menu"
                  className="flex items-center gap-1.5 rounded-full border border-white/10 py-1 pl-1 pr-2.5 text-xs text-white/70 hover:border-white/25"
                >
                  <span className="flex h-6 w-6 items-center justify-center rounded-full bg-violet/30 text-[11px] font-semibold uppercase text-white">
                    {user.email?.[0] ?? '?'}
                  </span>
                  <ChevronDown className="h-3 w-3" aria-hidden="true" />
                  <span className="sr-only">Account menu</span>
                </button>
                {menu && (
                  <div role="menu" className="absolute right-0 top-full mt-2 w-56 rounded-xl border border-white/10 bg-charcoal p-2 shadow-2xl">
                    <p className="truncate px-3 py-2 text-xs text-white/40">{user.email}</p>
                    <Link role="menuitem" to="/billing" className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm text-white/80 hover:bg-white/[0.06]">
                      <CreditCard className="h-4 w-4" aria-hidden="true" />
                      Billing
                    </Link>
                    <Link role="menuitem" to="/integrations" className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm text-white/80 hover:bg-white/[0.06]">
                      <Plug className="h-4 w-4" aria-hidden="true" />
                      Integrations
                    </Link>
                    <button role="menuitem" onClick={leave} className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-white/80 hover:bg-white/[0.06]">
                      <LogOut className="h-4 w-4" aria-hidden="true" />
                      Sign out
                    </button>
                  </div>
                )}
              </div>
            </>
          ) : (
            <>
              <NavLink to="/login" className={linkClass}>
                Sign in
              </NavLink>
              <Link to="/new" className={buttonVariants({ size: 'sm' })}>
                Analyze an idea
              </Link>
            </>
          )}
        </div>

        <button
          onClick={() => setOpen(!open)}
          className="rounded-lg border border-white/10 p-2 md:hidden"
          aria-label={open ? 'Close menu' : 'Open menu'}
          aria-expanded={open}
        >
          {open ? <X className="h-5 w-5 text-white" /> : <Menu className="h-5 w-5 text-white" />}
        </button>
      </div>

      {open && (
        <div className="flex flex-col gap-4 border-t border-white/5 px-4 py-4 md:hidden">
          {links.map((l) => (
            <NavLink key={l.to} to={l.to} className={linkClass}>
              {l.label}
            </NavLink>
          ))}
          {user && (
            <>
              <NavLink to="/billing" className={linkClass}>
                Billing
              </NavLink>
              <NavLink to="/integrations" className={linkClass}>
                Integrations
              </NavLink>
            </>
          )}
          <Link to="/new" className={buttonVariants({ size: 'md' })}>
            {user ? 'New idea' : 'Analyze an idea'}
          </Link>
          {user ? (
            <button onClick={leave} className="text-left text-sm text-white/60">
              Sign out
            </button>
          ) : (
            <NavLink to="/login" className={linkClass}>
              Sign in
            </NavLink>
          )}
        </div>
      )}
    </nav>
  );
}
