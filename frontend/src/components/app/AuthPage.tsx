import { useEffect, useState, type FormEvent } from 'react';
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom';
import { AlertTriangle, ArrowLeft, MailCheck, Rocket } from 'lucide-react';
import { useAuth } from '@/lib/auth';
import { authConfigured, supabase } from '@/lib/supabase';
import { Button } from '@/components/ui/button';
import { BackgroundBeams } from '@/components/ui/background-beams';

type Mode = 'signin' | 'signup' | 'reset';

const field =
  'w-full rounded-xl border border-white/10 bg-white/[0.04] px-4 py-3 text-sm text-white placeholder-white/30 focus:border-electric focus:outline-none';

export default function AuthPage() {
  const { user, loading } = useAuth();
  const navigate = useNavigate();
  const from = (useLocation().state as { from?: string } | null)?.from ?? '/app';
  const [mode, setMode] = useState<Mode>('signin');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [googleOn, setGoogleOn] = useState(false);

  // Only offer Google when the Supabase project has the provider enabled.
  useEffect(() => {
    const url = import.meta.env.VITE_SUPABASE_URL as string | undefined;
    if (!url) return;
    fetch(`${url}/auth/v1/settings`, { headers: { apikey: import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY as string } })
      .then((r) => r.json())
      .then((d) => setGoogleOn(Boolean(d?.external?.google)))
      .catch(() => undefined);
  }, []);

  if (!loading && user) return <Navigate to={from} replace />;

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    setNotice(null);
    try {
      if (mode === 'signin') {
        const { error } = await supabase.auth.signInWithPassword({ email, password });
        if (error) throw error;
        navigate(from, { replace: true });
      } else if (mode === 'signup') {
        const { data, error } = await supabase.auth.signUp({
          email,
          password,
          options: { emailRedirectTo: `${window.location.origin}/app` },
        });
        if (error) throw error;
        if (data.session) navigate(from, { replace: true });
        else setNotice('Check your inbox for a confirmation link, then sign in.');
      } else {
        const { error } = await supabase.auth.resetPasswordForEmail(email, { redirectTo: `${window.location.origin}/login` });
        if (error) throw error;
        setNotice('If that address has an account, a reset link is on its way.');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong. Try again.');
    } finally {
      setBusy(false);
    }
  };

  const google = async () => {
    setError(null);
    const { error } = await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: { redirectTo: `${window.location.origin}${from}` },
    });
    if (error) setError(error.message);
  };

  const title = mode === 'signin' ? 'Welcome back' : mode === 'signup' ? 'Create your account' : 'Reset your password';

  return (
    <div className="relative isolate flex min-h-screen items-center justify-center overflow-hidden bg-void px-4 py-10">
      <BackgroundBeams className="-z-10 opacity-40" />
      <div className="w-full max-w-md">
        <Link to="/" className="inline-flex items-center gap-2 text-sm text-white/50 transition-colors hover:text-white">
          <ArrowLeft className="h-4 w-4" aria-hidden="true" />
          Home
        </Link>

        <div className="mt-6 rounded-3xl border border-white/[0.1] bg-charcoal/80 p-7 backdrop-blur-xl">
          <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-electric to-violet">
            <Rocket className="h-5 w-5 text-white" aria-hidden="true" />
          </span>
          <h1 className="mt-5 font-serif text-3xl text-white">{title}</h1>
          <p className="mt-1.5 text-sm text-white/55">
            {mode === 'signup' ? 'Your first three analyses are free.' : 'Your ideas and reports are saved to your account.'}
          </p>

          {!authConfigured && (
            <div role="alert" className="mt-5 flex gap-3 rounded-2xl border border-yellow-400/25 bg-yellow-400/10 p-4 text-sm text-yellow-100">
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
              Sign-in is not configured. Set VITE_SUPABASE_URL and VITE_SUPABASE_PUBLISHABLE_KEY in frontend/.env.local.
            </div>
          )}

          {mode !== 'reset' && googleOn && (
            <>
              <Button type="button" variant="outline" size="lg" className="mt-6 w-full" onClick={google} disabled={!authConfigured}>
                <svg viewBox="0 0 24 24" className="h-4 w-4" aria-hidden="true">
                  <path fill="#EA4335" d="M12 10.2v3.9h5.5c-.2 1.3-1.6 3.9-5.5 3.9a6 6 0 1 1 0-12c1.9 0 3.1.8 3.8 1.5l2.6-2.5A9.8 9.8 0 0 0 12 2a10 10 0 1 0 0 20c5.8 0 9.6-4 9.6-9.8 0-.7-.1-1.2-.2-1.7H12z" />
                </svg>
                Continue with Google
              </Button>
              <div className="my-5 flex items-center gap-3 text-xs text-white/30">
                <span className="h-px flex-1 bg-white/10" />
                or with email
                <span className="h-px flex-1 bg-white/10" />
              </div>
            </>
          )}

          <form onSubmit={submit} className={mode === 'reset' || !googleOn ? 'mt-6 space-y-3' : 'space-y-3'}>
            <label className="block">
              <span className="sr-only">Email</span>
              <input type="email" required autoComplete="email" placeholder="you@company.com" value={email} onChange={(e) => setEmail(e.target.value)} className={field} />
            </label>
            {mode !== 'reset' && (
              <label className="block">
                <span className="sr-only">Password</span>
                <input
                  type="password"
                  required
                  minLength={8}
                  autoComplete={mode === 'signup' ? 'new-password' : 'current-password'}
                  placeholder="Password (8+ characters)"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className={field}
                />
              </label>
            )}
            <Button type="submit" variant="shine" size="lg" className="w-full" loading={busy} disabled={!authConfigured}>
              {mode === 'signin' ? 'Sign in' : mode === 'signup' ? 'Create account' : 'Send reset link'}
            </Button>
          </form>

          {error && (
            <p role="alert" className="mt-4 rounded-xl border border-red-500/25 bg-red-500/10 px-4 py-3 text-sm text-red-200">
              {error}
            </p>
          )}
          {notice && (
            <p role="status" className="mt-4 flex gap-2 rounded-xl border border-teal/30 bg-teal/10 px-4 py-3 text-sm text-teal-300">
              <MailCheck className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
              {notice}
            </p>
          )}

          <div className="mt-6 flex items-center justify-between text-sm text-white/50">
            {mode === 'signin' ? (
              <>
                <button className="hover:text-white" onClick={() => setMode('signup')}>
                  New here? Create an account
                </button>
                <button className="hover:text-white" onClick={() => setMode('reset')}>
                  Forgot password?
                </button>
              </>
            ) : (
              <button className="hover:text-white" onClick={() => setMode('signin')}>
                Back to sign in
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
