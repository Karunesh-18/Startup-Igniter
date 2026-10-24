import { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Github } from 'lucide-react';
import { createIdea, startAnalysis } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { AppPage, ApiErrorNote } from './shared';

const EXAMPLES = [
  'AI-powered legal contract reviewer for small businesses in India',
  'Carbon credit marketplace for regenerative agriculture',
  'Mental health companion app for college students using voice AI',
  'Tiffin service connecting home cooks with office workers in Bengaluru',
];

export default function NewIdea() {
  const navigate = useNavigate();
  const [text, setText] = useState((useLocation().state as { idea?: string } | null)?.idea ?? '');
  const [repo, setRepo] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (text.trim().length < 10) return;
    setBusy(true);
    setError(null);
    try {
      const idea = await createIdea({ idea_text: text.trim(), github_repo: repo.trim() || undefined });
      try {
        const run = await startAnalysis(idea.id);
        navigate(`/analysis/${run.analysis_id}`);
      } catch (err) {
        // The idea is saved even if the run was refused (e.g. free quota used up).
        setError(err instanceof Error ? err : new Error('Could not start the analysis.'));
        setBusy(false);
        navigate(`/ideas/${idea.id}`, { state: { notice: err instanceof Error ? err.message : undefined } });
      }
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Could not save the idea.'));
      setBusy(false);
    }
  };

  return (
    <AppPage>
      <h1 className="font-serif text-4xl leading-tight text-white sm:text-6xl">What are you building?</h1>
      <p className="mt-4 max-w-xl text-white/60">
        Describe the idea in one to three sentences. Thirteen crews work through it, check their claims against real sources, and a
        skeptic argues the other side.
      </p>

      <form onSubmit={submit} className="mt-8 rounded-3xl border border-white/[0.12] bg-charcoal/70 p-2 backdrop-blur-xl">
        <label htmlFor="idea" className="sr-only">
          Startup idea
        </label>
        <textarea
          id="idea"
          value={text}
          onChange={(e) => setText(e.target.value)}
          disabled={busy}
          placeholder="e.g. An app that matches home cooks with neighbours who want a weekly meal plan"
          rows={5}
          maxLength={5000}
          className="w-full resize-none rounded-2xl bg-transparent px-4 py-3 text-lg text-white placeholder-white/30 focus:outline-none disabled:opacity-60"
        />
        <div className="flex flex-wrap items-center justify-between gap-3 px-3 pb-2">
          <label className="flex items-center gap-2 text-sm text-white/50">
            <Github className="h-4 w-4" aria-hidden="true" />
            <span className="sr-only">GitHub repository (optional)</span>
            <input
              value={repo}
              onChange={(e) => setRepo(e.target.value)}
              disabled={busy}
              placeholder="owner/repo (optional)"
              className="w-44 rounded-lg border border-white/10 bg-white/[0.04] px-3 py-1.5 text-xs text-white placeholder-white/30 focus:border-electric focus:outline-none"
            />
          </label>
          <div className="flex items-center gap-4">
            <span className="text-xs text-white/35">{text.length} / 5000</span>
            <Button type="submit" variant="shine" loading={busy} disabled={text.trim().length < 10}>
              Start analysis
            </Button>
          </div>
        </div>
      </form>

      <div className="mt-4">
        <ApiErrorNote error={error} />
      </div>

      <div className="mt-6 flex flex-wrap gap-2">
        {EXAMPLES.map((ex) => (
          <button
            key={ex}
            onClick={() => setText(ex)}
            className="rounded-full border border-white/10 px-3.5 py-1.5 text-xs text-white/60 transition-colors hover:border-white/25 hover:text-white"
          >
            {ex}
          </button>
        ))}
      </div>
      <p className="mt-6 text-xs text-white/35">
        Linking a GitHub repo lets the feasibility and product crews read your README, languages and activity.
      </p>
    </AppPage>
  );
}
