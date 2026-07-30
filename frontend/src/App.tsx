import { useEffect, useState } from 'react';
import Landing from '@/components/Landing';
import Dashboard from '@/components/Dashboard';
import AnalysisPage from '@/components/AnalysisPage';
import ResultsPage from '@/components/ResultsPage';
import type { AnalysisResult } from '@/lib/types';

type View = 'landing' | 'dashboard' | 'analysis' | 'results';

function App() {
  const [view, setView] = useState<View>('landing');
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);

  useEffect(() => {
    window.scrollTo(0, 0);
  }, [view]);

  if (view === 'results' && analysisResult) {
    return (
      <ResultsPage
        result={analysisResult}
        onBack={() => setView('landing')}
        onNewMission={() => {
          setAnalysisResult(null);
          setView('analysis');
        }}
      />
    );
  }

  if (view === 'analysis') {
    return (
      <AnalysisPage
        onBack={() => setView('landing')}
        onComplete={(result) => {
          setAnalysisResult(result);
          setView('results');
        }}
      />
    );
  }

  if (view === 'dashboard') {
    return (
      <Dashboard
        onBack={() => setView('landing')}
        onLaunch={() => setView('analysis')}
      />
    );
  }

  return (
    <Landing
      onLaunch={() => setView('analysis')}
      onDashboard={() => setView('dashboard')}
    />
  );
}

export default App;
