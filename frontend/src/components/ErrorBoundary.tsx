import { Component, type ErrorInfo, type ReactNode } from 'react';
import { AlertTriangle, RotateCcw, Home } from 'lucide-react';

interface Props {
  children: ReactNode;
}

interface State {
  error: Error | null;
}

/**
 * Catches render errors anywhere below it in the tree. ResultsPage in
 * particular is ~800 lines of optional chaining over AI-generated JSON —
 * one unexpected shape (a field arriving as a string instead of an object,
 * a null where a list was expected) used to white-screen the entire app
 * after a multi-minute wait, with no recovery path but a manual refresh
 * (which, before the router migration, also destroyed the result — see
 * App.tsx's route-level sessionStorage restore).
 */
export default class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('Unhandled render error:', error, info.componentStack);
  }

  render() {
    if (this.state.error) {
      return (
        <div className="relative flex min-h-screen items-center justify-center bg-void px-6">
          <div className="gradient-border noise max-w-md rounded-3xl bg-charcoal/50 p-8 text-center backdrop-blur-xl">
            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-red-500/15 border border-red-500/30">
              <AlertTriangle className="h-7 w-7 text-red-400" aria-hidden="true" />
            </div>
            <h1 className="mt-6 text-xl font-medium text-white">Something went wrong</h1>
            <p className="mt-2 text-sm text-white/50">
              This page hit an unexpected error rendering its content. Your analysis result
              (if any) is unaffected — reloading or going home will recover it.
            </p>
            <p className="mt-3 rounded-lg bg-black/30 px-3 py-2 font-mono text-[11px] text-white/40" role="alert">
              {this.state.error.message}
            </p>
            <div className="mt-6 flex justify-center gap-3">
              <button
                onClick={() => window.location.reload()}
                className="btn-primary flex items-center gap-2 rounded-full px-5 py-2 text-sm font-medium"
              >
                <RotateCcw className="h-4 w-4" aria-hidden="true" />
                Reload
              </button>
              <a
                href="/"
                className="btn-ghost flex items-center gap-2 rounded-full px-5 py-2 text-sm font-medium text-white/80"
              >
                <Home className="h-4 w-4" aria-hidden="true" />
                Home
              </a>
            </div>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
