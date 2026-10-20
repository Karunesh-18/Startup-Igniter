import { useRef, type KeyboardEvent, type ReactNode } from 'react';
import { cn } from '@/lib/utils';

export interface TabItem {
  key: string;
  label: ReactNode;
  disabled?: boolean;
}

interface TabsProps {
  tabs: TabItem[];
  active: string;
  onChange: (key: string) => void;
  idPrefix: string;
  label?: string;
  className?: string;
}

/**
 * Accessible tablist (role/aria wiring + arrow/Home/End keys). Pair with
 * `<TabPanel>` per panel. Scrolls horizontally when tabs overflow.
 */
export function Tabs({ tabs, active, onChange, idPrefix, label = 'Sections', className }: TabsProps) {
  const refs = useRef<Record<string, HTMLButtonElement | null>>({});
  const enabled = tabs.filter((t) => !t.disabled);

  const handleKeyDown = (e: KeyboardEvent<HTMLButtonElement>, key: string) => {
    const i = enabled.findIndex((t) => t.key === key);
    const next =
      e.key === 'ArrowRight' ? enabled[(i + 1) % enabled.length]
      : e.key === 'ArrowLeft' ? enabled[(i - 1 + enabled.length) % enabled.length]
      : e.key === 'Home' ? enabled[0]
      : e.key === 'End' ? enabled[enabled.length - 1]
      : null;
    if (!next) return;
    e.preventDefault();
    onChange(next.key);
    refs.current[next.key]?.focus();
  };

  return (
    <div role="tablist" aria-label={label} className={cn('flex gap-1 overflow-x-auto', className)}>
      {tabs.map((tab) => {
        const isActive = active === tab.key;
        return (
          <button
            key={tab.key}
            ref={(el) => {
              refs.current[tab.key] = el;
            }}
            role="tab"
            id={`${idPrefix}-tab-${tab.key}`}
            aria-selected={isActive}
            aria-controls={`${idPrefix}-panel-${tab.key}`}
            tabIndex={isActive ? 0 : -1}
            disabled={tab.disabled}
            onClick={() => onChange(tab.key)}
            onKeyDown={(e) => handleKeyDown(e, tab.key)}
            className={cn(
              'shrink-0 rounded-full px-4 py-2 text-sm transition-colors duration-200 disabled:cursor-not-allowed disabled:opacity-30',
              isActive ? 'bg-white text-void' : 'text-white/55 hover:bg-white/[0.06] hover:text-white',
            )}
          >
            {tab.label}
          </button>
        );
      })}
    </div>
  );
}

export function TabPanel({ idPrefix, tabKey, children }: { idPrefix: string; tabKey: string; children: ReactNode }) {
  return (
    <div role="tabpanel" id={`${idPrefix}-panel-${tabKey}`} aria-labelledby={`${idPrefix}-tab-${tabKey}`} tabIndex={0}>
      {children}
    </div>
  );
}
