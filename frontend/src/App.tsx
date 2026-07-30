import { useEffect, useState } from 'react';
import Landing from '@/components/Landing';
import AnalysisPage from '@/components/AnalysisPage';
import ResultsPage from '@/components/ResultsPage';
import PhaseListPage from '@/components/PhaseListPage';
import PhaseDetailPage from '@/components/PhaseDetailPage';
import AgentListPage from '@/components/AgentListPage';
import AgentDetailPage from '@/components/AgentDetailPage';
import Nav from '@/components/Nav';
import type { AnalysisResult } from '@/lib/types';

type View = 'landing' | 'analysis' | 'results' | 'phases' | 'phase-detail' | 'agents' | 'agent-detail';

function App() {
  const [view, setView] = useState<View>('landing');
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [selectedCrew, setSelectedCrew] = useState<number>(1);
  const [selectedAgent, setSelectedAgent] = useState<number>(1);

  useEffect(() => {
    window.scrollTo(0, 0);
  }, [view]);

  // Pages that don't show the landing Nav
  const standaloneViews: View[] = ['analysis', 'results'];
  const showNav = !standaloneViews.includes(view);

  const nav = showNav ? (
    <Nav
      onLaunch={() => setView('analysis')}
      onHome={() => setView('landing')}
      onPhases={() => setView('phases')}
      onAgents={() => setView('agents')}
    />
  ) : null;

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

  if (view === 'phase-detail') {
    return (
      <>
        {nav}
        <PhaseDetailPage
          crewId={selectedCrew}
          onBack={() => setView('phases')}
          onSelectAgent={(id) => {
            setSelectedAgent(id);
            setView('agent-detail');
          }}
          onLaunch={() => setView('analysis')}
        />
      </>
    );
  }

  if (view === 'phases') {
    return (
      <>
        {nav}
        <PhaseListPage
          onBack={() => setView('landing')}
          onSelectPhase={(id) => {
            setSelectedCrew(id);
            setView('phase-detail');
          }}
          onAgents={() => setView('agents')}
        />
      </>
    );
  }

  if (view === 'agent-detail') {
    return (
      <>
        {nav}
        <AgentDetailPage
          agentId={selectedAgent}
          onBack={() => setView('agents')}
          onSelectPhase={(id) => {
            setSelectedCrew(id);
            setView('phase-detail');
          }}
        />
      </>
    );
  }

  if (view === 'agents') {
    return (
      <>
        {nav}
        <AgentListPage
          onBack={() => setView('landing')}
          onSelectAgent={(id) => {
            setSelectedAgent(id);
            setView('agent-detail');
          }}
          onPhases={() => setView('phases')}
        />
      </>
    );
  }

  // Landing (default)
  return (
    <>
      {nav}
      <Landing
        onLaunch={() => setView('analysis')}
        onPhases={() => setView('phases')}
        onAgents={() => setView('agents')}
      />
    </>
  );
}

export default App;
