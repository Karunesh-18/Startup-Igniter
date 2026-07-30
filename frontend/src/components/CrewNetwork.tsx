import { useEffect, useRef, useState } from 'react';
import { CREWS } from '@/data/crews';

interface NodePos {
  x: number;
  y: number;
  crew: number;
  agent: number;
  baseAngle: number;
  orbit: number;
}

export default function CrewNetwork({ active = false, compact = false }: { active?: boolean; compact?: boolean }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [hovered, setHovered] = useState<{ crew: number; agent: number } | null>(null);
  const [progress, setProgress] = useState(0);
  const nodesRef = useRef<NodePos[]>([]);
  const animRef = useRef(0);
  const hoveredRef = useRef<{ crew: number; agent: number } | null>(null);
  const frameRef = useRef(0);
  const activeRef = useRef(active);
  const progressRef = useRef(progress);

  useEffect(() => {
    activeRef.current = active;
  }, [active]);

  useEffect(() => {
    progressRef.current = progress;
  }, [progress]);

  // Build node positions: 12 clusters arranged in a ring, each with 6 agents in a small orbit
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const dpr = window.devicePixelRatio;
    let w = (canvas.width = canvas.offsetWidth * dpr);
    let h = (canvas.height = canvas.offsetHeight * dpr);

    const cx = w / 2;
    const cy = h / 2;
    const clusterRadius = Math.min(w, h) * 0.34;
    const agentOrbit = Math.min(w, h) * 0.075;

    const nodes: NodePos[] = [];
    CREWS.forEach((crew, ci) => {
      const clusterAngle = (ci / CREWS.length) * Math.PI * 2 - Math.PI / 2;
      const ccx = cx + Math.cos(clusterAngle) * clusterRadius;
      const ccy = cy + Math.sin(clusterAngle) * clusterRadius;
      crew.agents.forEach((agent, ai) => {
        const agentAngle = (ai / crew.agents.length) * Math.PI * 2;
        nodes.push({
          x: ccx + Math.cos(agentAngle) * agentOrbit,
          y: ccy + Math.sin(agentAngle) * agentOrbit,
          crew: crew.id,
          agent: agent.id,
          baseAngle: clusterAngle,
          orbit: agentOrbit,
        });
      });
    });
    nodesRef.current = nodes;

    const onResize = () => {
      w = canvas.width = canvas.offsetWidth * dpr;
      h = canvas.height = canvas.offsetHeight * dpr;
    };
    window.addEventListener('resize', onResize);

    const render = () => {
      const ctx = canvas.getContext('2d');
      if (!ctx) return;
      ctx.clearRect(0, 0, w, h);
      frameRef.current += 0.016;
      const frame = frameRef.current;
      const curActive = activeRef.current;
      const curProgress = progressRef.current;
      const curHovered = hoveredRef.current;

      const t = curActive ? Math.min(curProgress, 1) : 0.35;

      // Center hub
      const hubGrad = ctx.createRadialGradient(cx, cy, 0, cx, cy, 40 * dpr);
      hubGrad.addColorStop(0, `rgba(139,92,246,${0.4 * t})`);
      hubGrad.addColorStop(1, 'rgba(139,92,246,0)');
      ctx.fillStyle = hubGrad;
      ctx.beginPath();
      ctx.arc(cx, cy, 40 * dpr, 0, Math.PI * 2);
      ctx.fill();

      ctx.beginPath();
      ctx.arc(cx, cy, 6 * dpr, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(255,255,255,${0.6 * t + 0.2})`;
      ctx.fill();

      // Cluster center positions
      const clusterCenters = CREWS.map((crew, ci) => {
        const clusterAngle = (ci / CREWS.length) * Math.PI * 2 - Math.PI / 2;
        return {
          x: cx + Math.cos(clusterAngle) * clusterRadius,
          y: cy + Math.sin(clusterAngle) * clusterRadius,
          color: crew.color,
          color2: crew.color2,
          id: crew.id,
        };
      });

      // Connections from hub to clusters
      clusterCenters.forEach((cc, ci) => {
        const pulse = curActive ? (Math.sin(frame * 2 + ci) * 0.5 + 0.5) : 0;
        const grad = ctx.createLinearGradient(cx, cy, cc.x, cc.y);
        grad.addColorStop(0, `rgba(139,92,246,${0.15 * t})`);
        grad.addColorStop(1, hexToRgba(cc.color, 0.25 * t + pulse * 0.15));
        ctx.strokeStyle = grad;
        ctx.lineWidth = 1.2 * dpr;
        ctx.beginPath();
        ctx.moveTo(cx, cy);
        ctx.lineTo(cc.x, cc.y);
        ctx.stroke();

        // Data packet
        if (curActive) {
          const pp = ((frame * 0.3 + ci * 0.15) % 1);
          const px = cx + (cc.x - cx) * pp;
          const py = cy + (cc.y - cy) * pp;
          ctx.beginPath();
          ctx.arc(px, py, 2.5 * dpr, 0, Math.PI * 2);
          ctx.fillStyle = hexToRgba(cc.color, 0.9);
          ctx.fill();
        }
      });

      // Inter-cluster connections (adjacent clusters)
      for (let i = 0; i < clusterCenters.length; i++) {
        const a = clusterCenters[i];
        const b = clusterCenters[(i + 1) % clusterCenters.length];
        ctx.strokeStyle = `rgba(255,255,255,${0.04 * t})`;
        ctx.lineWidth = 0.8 * dpr;
        ctx.beginPath();
        ctx.moveTo(a.x, a.y);
        ctx.lineTo(b.x, b.y);
        ctx.stroke();
      }

      // Nodes
      nodesRef.current.forEach((node, ni) => {
        const crew = CREWS[node.crew - 1];
        const cluster = clusterCenters[node.crew - 1];
        const orbitAngle = (node.agent % 6) / 6 * Math.PI * 2 + frame * 0.2;
        const wobble = Math.sin(frame + ni) * 2 * dpr;
        const ax = cluster.x + Math.cos(orbitAngle) * (agentOrbit + wobble);
        const ay = cluster.y + Math.sin(orbitAngle) * (agentOrbit + wobble);

        const isHovered = curHovered?.crew === node.crew && curHovered?.agent === node.agent;
        const nodeSize = (isHovered ? 4 : 2.5) * dpr;
        const glow = curActive ? (Math.sin(frame * 1.5 + ni * 0.3) * 0.3 + 0.7) : 0.4;

        // Glow
        const ng = ctx.createRadialGradient(ax, ay, 0, ax, ay, nodeSize * 4);
        ng.addColorStop(0, hexToRgba(crew.color, 0.5 * t * glow));
        ng.addColorStop(1, hexToRgba(crew.color, 0));
        ctx.fillStyle = ng;
        ctx.beginPath();
        ctx.arc(ax, ay, nodeSize * 4, 0, Math.PI * 2);
        ctx.fill();

        // Node
        ctx.beginPath();
        ctx.arc(ax, ay, nodeSize, 0, Math.PI * 2);
        ctx.fillStyle = hexToRgba(crew.color, 0.9 * t + 0.15);
        ctx.fill();
        ctx.strokeStyle = hexToRgba(crew.color2, 0.5 * t);
        ctx.lineWidth = 0.8 * dpr;
        ctx.stroke();

        // Connection to cluster center
        ctx.strokeStyle = hexToRgba(crew.color, 0.15 * t);
        ctx.lineWidth = 0.5 * dpr;
        ctx.beginPath();
        ctx.moveTo(cluster.x, cluster.y);
        ctx.lineTo(ax, ay);
        ctx.stroke();

        // Update node ref for hover detection
        nodesRef.current[ni].x = ax;
        nodesRef.current[ni].y = ay;
      });

      // Cluster centers
      clusterCenters.forEach((cc, ci) => {
        const crew = CREWS[ci];
        const pulse = curActive ? (Math.sin(frame * 1.5 + ci) * 0.3 + 0.7) : 0.5;
        const cg = ctx.createRadialGradient(cc.x, cc.y, 0, cc.x, cc.y, 14 * dpr);
        cg.addColorStop(0, hexToRgba(crew.color, 0.6 * t * pulse));
        cg.addColorStop(1, hexToRgba(crew.color, 0));
        ctx.fillStyle = cg;
        ctx.beginPath();
        ctx.arc(cc.x, cc.y, 14 * dpr, 0, Math.PI * 2);
        ctx.fill();

        ctx.beginPath();
        ctx.arc(cc.x, cc.y, 4 * dpr, 0, Math.PI * 2);
        ctx.fillStyle = hexToRgba(crew.color2, 0.9 * t + 0.2);
        ctx.fill();
      });

      animRef.current = requestAnimationFrame(render);
    };
    render();

    return () => {
      cancelAnimationFrame(animRef.current);
      window.removeEventListener('resize', onResize);
    };
  }, []);

  // Animate progress when active
  useEffect(() => {
    if (!active) {
      setProgress(0);
      return;
    }
    setProgress(0);
    let raf = 0;
    let start = performance.now();
    const tick = (now: number) => {
      const elapsed = now - start;
      const p = Math.min(elapsed / 3000, 1);
      setProgress(p);
      if (p < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [active]);

  const onMove = (e: React.MouseEvent) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const dpr = window.devicePixelRatio;
    const mx = (e.clientX - rect.left) * dpr;
    const my = (e.clientY - rect.top) * dpr;
    let nearest: { crew: number; agent: number } | null = null;
    let minDist = 20 * dpr;
    nodesRef.current.forEach((n) => {
      const d = Math.sqrt((n.x - mx) ** 2 + (n.y - my) ** 2);
      if (d < minDist) {
        minDist = d;
        nearest = { crew: n.crew, agent: n.agent };
      }
    });
    hoveredRef.current = nearest;
    setHovered(nearest);
  };

  const onLeave = () => {
    hoveredRef.current = null;
    setHovered(null);
  };

  return (
    <div className="relative h-full w-full">
      <canvas
        ref={canvasRef}
        onMouseMove={onMove}
        onMouseLeave={onLeave}
        className="h-full w-full cursor-crosshair"
      />
      {hovered && (
        <div className="pointer-events-none absolute left-1/2 top-4 -translate-x-1/2 rounded-full border border-white/10 bg-charcoal/80 px-4 py-1.5 text-xs backdrop-blur-xl">
          <span className="font-mono text-white/60">AGENT</span>{' '}
          <span className="font-medium text-white">
            {CREWS[hovered.crew - 1].agents.find((a) => a.id === hovered.agent)?.name}
          </span>
          <span className="mx-2 text-white/20">·</span>
          <span className="text-gradient">{CREWS[hovered.crew - 1].name}</span>
        </div>
      )}
      {!compact && (
        <div className="pointer-events-none absolute bottom-4 left-1/2 -translate-x-1/2 flex items-center gap-6 text-[10px] uppercase tracking-[0.2em] text-white/40">
          <span className="flex items-center gap-1.5"><span className="h-1.5 w-1.5 rounded-full bg-electric" />12 Crews</span>
          <span className="flex items-center gap-1.5"><span className="h-1.5 w-1.5 rounded-full bg-violet" />72 Agents</span>
          <span className="flex items-center gap-1.5"><span className="h-1.5 w-1.5 rounded-full bg-emerald" />Live Sync</span>
        </div>
      )}
    </div>
  );
}

function hexToRgba(hex: string, a: number) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r},${g},${b},${a})`;
}
