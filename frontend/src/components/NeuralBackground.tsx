import { useEffect, useRef } from 'react';

interface Particle {
  x: number;
  y: number;
  vx: number;
  vy: number;
  size: number;
  hue: number;
  alpha: number;
}

interface Beam {
  x: number;
  y: number;
  angle: number;
  speed: number;
  length: number;
  hue: number;
  alpha: number;
}

export default function NeuralBackground({ density = 0.7 }: { density?: number }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let w = (canvas.width = canvas.offsetWidth * window.devicePixelRatio);
    let h = (canvas.height = canvas.offsetHeight * window.devicePixelRatio);
    let dpr = window.devicePixelRatio;

    const particles: Particle[] = [];
    const beams: Beam[] = [];
    const count = Math.floor((w * h) / (26000 / density));

    const hues = [210, 260, 280, 190, 160, 320];

    for (let i = 0; i < count; i++) {
      particles.push({
        x: Math.random() * w,
        y: Math.random() * h,
        vx: (Math.random() - 0.5) * 0.3 * dpr,
        vy: (Math.random() - 0.5) * 0.3 * dpr,
        size: (Math.random() * 1.6 + 0.4) * dpr,
        hue: hues[Math.floor(Math.random() * hues.length)],
        alpha: Math.random() * 0.5 + 0.15,
      });
    }

    for (let i = 0; i < 5; i++) {
      beams.push({
        x: Math.random() * w,
        y: Math.random() * h,
        angle: Math.random() * Math.PI * 2,
        speed: (Math.random() * 0.4 + 0.2) * dpr,
        length: (Math.random() * 120 + 80) * dpr,
        hue: hues[Math.floor(Math.random() * hues.length)],
        alpha: Math.random() * 0.15 + 0.05,
      });
    }

    let mouseX = w / 2;
    let mouseY = h / 2;
    const onMove = (e: MouseEvent) => {
      const rect = canvas.getBoundingClientRect();
      mouseX = (e.clientX - rect.left) * dpr;
      mouseY = (e.clientY - rect.top) * dpr;
    };
    window.addEventListener('mousemove', onMove);

    const onResize = () => {
      w = canvas.width = canvas.offsetWidth * dpr;
      h = canvas.height = canvas.offsetHeight * dpr;
    };
    window.addEventListener('resize', onResize);

    let raf = 0;
    const maxDist = 130 * dpr;

    const render = () => {
      ctx.clearRect(0, 0, w, h);

      // Light beams
      beams.forEach((b) => {
        b.x += Math.cos(b.angle) * b.speed;
        b.y += Math.sin(b.angle) * b.speed;
        if (b.x < -b.length || b.x > w + b.length) b.angle = Math.PI - b.angle;
        if (b.y < -b.length || b.y > h + b.length) b.angle = -b.angle;

        const grad = ctx.createLinearGradient(b.x, b.y, b.x + Math.cos(b.angle) * b.length, b.y + Math.sin(b.angle) * b.length);
        grad.addColorStop(0, `hsla(${b.hue}, 90%, 65%, 0)`);
        grad.addColorStop(0.5, `hsla(${b.hue}, 90%, 65%, ${b.alpha})`);
        grad.addColorStop(1, `hsla(${b.hue}, 90%, 65%, 0)`);
        ctx.strokeStyle = grad;
        ctx.lineWidth = 1.5 * dpr;
        ctx.beginPath();
        ctx.moveTo(b.x, b.y);
        ctx.lineTo(b.x + Math.cos(b.angle) * b.length, b.y + Math.sin(b.angle) * b.length);
        ctx.stroke();
      });

      // Particles
      particles.forEach((p) => {
        p.x += p.vx;
        p.y += p.vy;
        if (p.x < 0 || p.x > w) p.vx *= -1;
        if (p.y < 0 || p.y > h) p.vy *= -1;

        // Mouse attraction
        const dx = mouseX - p.x;
        const dy = mouseY - p.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < maxDist * 1.5) {
          p.vx += (dx / dist) * 0.008;
          p.vy += (dy / dist) * 0.008;
        }
        p.vx *= 0.99;
        p.vy *= 0.99;

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        ctx.fillStyle = `hsla(${p.hue}, 85%, 65%, ${p.alpha})`;
        ctx.fill();
      });

      // Connections
      for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
          const dx = particles[i].x - particles[j].x;
          const dy = particles[i].y - particles[j].y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < maxDist) {
            const a = (1 - dist / maxDist) * 0.18;
            const hue = (particles[i].hue + particles[j].hue) / 2;
            ctx.strokeStyle = `hsla(${hue}, 80%, 60%, ${a})`;
            ctx.lineWidth = 0.6 * dpr;
            ctx.beginPath();
            ctx.moveTo(particles[i].x, particles[i].y);
            ctx.lineTo(particles[j].x, particles[j].y);
            ctx.stroke();
          }
        }
      }

      raf = requestAnimationFrame(render);
    };
    render();

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener('mousemove', onMove);
      window.removeEventListener('resize', onResize);
    };
  }, [density]);

  return <canvas ref={canvasRef} className="absolute inset-0 h-full w-full" />;
}
