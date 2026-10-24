import { useEffect, useRef, useState } from 'react';
import { Check, Loader2, SendHorizontal, X } from 'lucide-react';
import { chatHistory, decideProposal, PaywallError, sendChat } from '@/lib/api';
import type { ChatMessage } from '@/lib/types';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { ErrorNote, UpgradeCard } from './shared';

const STARTERS = [
  'What is the weakest assumption in this idea?',
  'Who should I sell to first?',
  'How would you cut the scope for a 4-week MVP?',
];

function Proposal({ msg, onDecide }: { msg: ChatMessage; onDecide: (action: 'accept' | 'dismiss') => Promise<void> }) {
  const [busy, setBusy] = useState<'accept' | 'dismiss' | null>(null);
  const p = msg.proposal;
  if (!p) return null;
  const decide = async (a: 'accept' | 'dismiss') => {
    setBusy(a);
    await onDecide(a).finally(() => setBusy(null));
  };
  return (
    <div className="mt-3 rounded-xl border border-electric/30 bg-electric/10 p-4">
      <p className="text-xs font-medium uppercase tracking-wide text-electric-300">Proposed change to your idea</p>
      <ul className="mt-2 space-y-1 text-sm text-white/80">
        {p.changes.map((c, i) => (
          <li key={i}>• {c}</li>
        ))}
      </ul>
      {msg.proposal_status === 'pending' ? (
        <div className="mt-3 flex gap-2">
          <Button size="sm" onClick={() => decide('accept')} loading={busy === 'accept'} disabled={busy !== null}>
            <Check className="h-3.5 w-3.5" aria-hidden="true" />
            Apply to idea
          </Button>
          <Button size="sm" variant="ghost" onClick={() => decide('dismiss')} loading={busy === 'dismiss'} disabled={busy !== null}>
            <X className="h-3.5 w-3.5" aria-hidden="true" />
            Dismiss
          </Button>
        </div>
      ) : (
        <p className="mt-2 text-xs text-white/50">
          {msg.proposal_status === 'accepted' ? 'Applied. Re-run the analysis to update the verdict.' : 'Dismissed.'}
        </p>
      )}
    </div>
  );
}

export default function ChatPanel({ ideaId, onIdeaChanged }: { ideaId: string; onIdeaChanged: () => void }) {
  const [messages, setMessages] = useState<ChatMessage[] | null>(null);
  const [input, setInput] = useState('');
  const [streaming, setStreaming] = useState<string | null>(null);
  const [locked, setLocked] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatHistory(ideaId)
      .then(setMessages)
      .catch((e: unknown) => {
        setMessages([]);
        if (e instanceof PaywallError) setLocked(e.message);
        else setError(e instanceof Error ? e.message : 'Could not load the chat.');
      });
  }, [ideaId]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ block: 'nearest' });
  }, [messages, streaming]);

  const send = async (text: string) => {
    const content = text.trim();
    if (!content || streaming !== null) return;
    setInput('');
    setError(null);
    setStreaming('');
    setMessages((m) => [...(m ?? []), { id: `tmp-${Date.now()}`, role: 'user', content, proposal: null, proposal_status: null, created_at: new Date().toISOString() }]);
    try {
      await sendChat(ideaId, content, {
        onDelta: (d) => setStreaming((s) => (s ?? '') + d),
        onMessage: (m) => setMessages((all) => [...(all ?? []), m]),
      });
    } catch (e) {
      if (e instanceof PaywallError) setLocked(e.message);
      else setError(e instanceof Error ? e.message : 'The message failed.');
    } finally {
      setStreaming(null);
    }
  };

  const decide = async (msg: ChatMessage, action: 'accept' | 'dismiss') => {
    try {
      const r = await decideProposal(msg.id, action);
      setMessages((all) => (all ?? []).map((m) => (m.id === msg.id ? r.message : m)));
      if (action === 'accept') onIdeaChanged();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not apply the change.');
    }
  };

  if (messages === null) return <Loader2 className="mx-auto mt-12 h-5 w-5 animate-spin text-electric" aria-label="Loading chat" />;

  return (
    <div className="flex flex-col rounded-2xl border border-white/[0.07] bg-charcoal/60">
      <div className="max-h-[28rem] min-h-[16rem] space-y-4 overflow-y-auto p-4" aria-live="polite">
        {messages.length === 0 && !locked && (
          <div className="py-6 text-center">
            <p className="text-sm text-white/55">Talk the idea through. I know your idea and its latest report.</p>
            <div className="mt-4 flex flex-wrap justify-center gap-2">
              {STARTERS.map((s) => (
                <button key={s} onClick={() => send(s)} className="rounded-full border border-white/10 px-3 py-1.5 text-xs text-white/60 hover:border-white/25 hover:text-white">
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}
        {messages.map((m) => (
          <div key={m.id} className={cn('flex flex-col', m.role === 'user' ? 'items-end' : 'items-start')}>
            <div
              className={cn(
                'max-w-[85%] whitespace-pre-wrap rounded-2xl px-4 py-2.5 text-sm leading-relaxed',
                m.role === 'user' ? 'bg-electric text-white' : 'bg-white/[0.06] text-white/85',
              )}
            >
              {m.content}
            </div>
            {m.role === 'assistant' && m.proposal && (
              <div className="w-full max-w-[85%]">
                <Proposal msg={m} onDecide={(a) => decide(m, a)} />
              </div>
            )}
          </div>
        ))}
        {streaming !== null && (
          <div className="max-w-[85%] whitespace-pre-wrap rounded-2xl bg-white/[0.06] px-4 py-2.5 text-sm leading-relaxed text-white/85">
            {streaming || <Loader2 className="h-4 w-4 animate-spin text-white/40" aria-label="Thinking" />}
          </div>
        )}
        <div ref={endRef} />
      </div>

      <div className="space-y-3 border-t border-white/[0.07] p-3">
        {locked && <UpgradeCard message={locked} />}
        <ErrorNote error={error} />
        <form
          className="flex items-end gap-2"
          onSubmit={(e) => {
            e.preventDefault();
            send(input);
          }}
        >
          <label className="sr-only" htmlFor="chat-input">
            Message your AI co-founder
          </label>
          <textarea
            id="chat-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                send(input);
              }
            }}
            rows={2}
            maxLength={2000}
            disabled={Boolean(locked) || streaming !== null}
            placeholder={locked ? 'Pro feature' : 'e.g. What if we target students instead?'}
            className="flex-1 resize-none rounded-xl border border-white/10 bg-white/[0.04] px-3 py-2 text-sm text-white placeholder-white/30 focus:border-electric focus:outline-none disabled:opacity-50"
          />
          <Button type="submit" size="icon" aria-label="Send message" disabled={!input.trim() || Boolean(locked) || streaming !== null}>
            <SendHorizontal className="h-4 w-4" />
          </Button>
        </form>
      </div>
    </div>
  );
}
