import { lazy, Suspense, useEffect } from 'react';
import { Navigate, Route, Routes, useLocation, useNavigate, useParams } from 'react-router-dom';
import Landing from '@/components/Landing';
import AnalysisPage from '@/components/AnalysisPage';
import PhaseListPage from '@/components/PhaseListPage';
import PhaseDetailPage from '@/components/PhaseDetailPage';
import AgentListPage from '@/components/AgentListPage';
import AgentDetailPage from '@/components/AgentDetailPage';
import Nav from '@/components/Nav';
import AuthPage from '@/components/app/AuthPage';
import Dashboard from '@/components/app/Dashboard';
import NewIdea from '@/components/app/NewIdea';
import IdeaPage from '@/components/app/IdeaPage';
import Pricing from '@/components/app/Pricing';
import Billing from '@/components/app/Billing';
import Integrations from '@/components/app/Integrations';
import { RequireAuth } from '@/lib/auth';
import ErrorBoundary from '@/components/ErrorBoundary';

// Recharts lives only in the report, so keep it out of the main chunk.
const ResultsPage = lazy(() => import('@/components/results/ResultsPage'));

// Thin adapters from route params to the explorer pages' existing callback props.
function PhasesRoute() {
  const navigate = useNavigate();
  return <PhaseListPage onBack={() => navigate('/')} onSelectPhase={(id) => navigate(`/phases/${id}`)} onAgents={() => navigate('/agents')} />;
}

function PhaseRoute() {
  const navigate = useNavigate();
  const id = Number(useParams().id);
  return (
    <PhaseDetailPage
      crewId={id}
      onBack={() => navigate('/phases')}
      onSelectAgent={(a) => navigate(`/agents/${a}`)}
      onLaunch={() => navigate('/new')}
    />
  );
}

function AgentsRoute() {
  const navigate = useNavigate();
  return <AgentListPage onBack={() => navigate('/')} onSelectAgent={(id) => navigate(`/agents/${id}`)} onPhases={() => navigate('/phases')} />;
}

function AgentRoute() {
  return <AgentDetailPage agentId={Number(useParams().id)} />;
}

const FULLSCREEN = ['/analysis', '/results', '/login'];

export default function App() {
  const { pathname } = useLocation();
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [pathname]);
  const showNav = !FULLSCREEN.some((p) => pathname.startsWith(p));

  return (
    <>
      {showNav && <Nav />}
      {/* Keyed by path so an error on one page clears when you navigate away. */}
      <ErrorBoundary key={pathname}>
        <Suspense fallback={<div className="min-h-screen bg-void" />}>
          <Routes>
            <Route path="/" element={<Landing />} />
            <Route path="/login" element={<AuthPage />} />
            <Route path="/pricing" element={<Pricing />} />
            <Route path="/app" element={<RequireAuth><Dashboard /></RequireAuth>} />
            <Route path="/new" element={<RequireAuth><NewIdea /></RequireAuth>} />
            <Route path="/ideas/:id" element={<RequireAuth><IdeaPage /></RequireAuth>} />
            <Route path="/billing" element={<RequireAuth><Billing /></RequireAuth>} />
            <Route path="/integrations" element={<RequireAuth><Integrations /></RequireAuth>} />
            <Route path="/analysis/:id" element={<RequireAuth><AnalysisPage /></RequireAuth>} />
            <Route path="/results/:id" element={<RequireAuth><ResultsPage /></RequireAuth>} />
            <Route path="/analyze" element={<Navigate to="/new" replace />} />
            <Route path="/phases" element={<PhasesRoute />} />
            <Route path="/phases/:id" element={<PhaseRoute />} />
            <Route path="/agents" element={<AgentsRoute />} />
            <Route path="/agents/:id" element={<AgentRoute />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Suspense>
      </ErrorBoundary>
    </>
  );
}
