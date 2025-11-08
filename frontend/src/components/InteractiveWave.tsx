import { useEffect, useRef } from 'react';
import '../styles/interactive-wave.css';

const TWO_PI = Math.PI * 2;

function getWaveColors() {
  if (typeof window === 'undefined') return ['rgba(20,20,20,0.06)', 'rgba(20,20,20,0.18)'];
  const style = getComputedStyle(document.documentElement);
  const top = style.getPropertyValue('--wave-stroke-top').trim() || 'rgba(20,20,20,0.06)';
  const bottom = style.getPropertyValue('--wave-stroke-bottom').trim() || 'rgba(20,20,20,0.18)';
  return [top, bottom] as [string, string];
}

function drawWave(
  ctx: CanvasRenderingContext2D,
  width: number,
  height: number,
  time: number,
  offset: number,
  amplitude = 18,
) {
  ctx.beginPath();
  const wavelength = 0.012;
  ctx.moveTo(0, height / 2);
  for (let x = 0; x <= width; x += 6) {
    const y = height / 2 + Math.sin(x * wavelength + time + offset) * amplitude * Math.sin(time * 0.4 + offset);
    ctx.lineTo(x, y);
  }
  ctx.stroke();
}

export function InteractiveWave({ className = '' }: { className?: string }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationRef = useRef<number>();
  const mouseRef = useRef({ x: 0, y: 0, active: false });
  const colorRef = useRef(getWaveColors());

  useEffect(() => {
    colorRef.current = getWaveColors();
  });

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const resize = () => {
      const { innerWidth, innerHeight } = window;
      canvas.width = innerWidth;
      canvas.height = innerHeight * 0.6;
    };

    resize();

    const onMouseMove = (event: MouseEvent) => {
      mouseRef.current = { x: event.clientX, y: event.clientY, active: true };
    };

    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('resize', resize);

    let start = performance.now();

    const render = (now: number) => {
      const time = (now - start) / 900;
      const [topColor, bottomColor] = colorRef.current;
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      const gradient = ctx.createLinearGradient(0, 0, 0, canvas.height);
      gradient.addColorStop(0, topColor);
      gradient.addColorStop(1, bottomColor);
      ctx.strokeStyle = gradient;
      ctx.lineWidth = 1.5;

      for (let i = 0; i < 4; i++) {
        ctx.save();
        ctx.translate(0, i * 18);
        drawWave(ctx, canvas.width, canvas.height, time + i, i * 0.4 + (mouseRef.current.x / canvas.width) * 1.6);
        ctx.restore();
      }

      animationRef.current = requestAnimationFrame(render);
    };

    animationRef.current = requestAnimationFrame(render);

    return () => {
      if (animationRef.current) cancelAnimationFrame(animationRef.current);
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('resize', resize);
    };
  }, []);

  return <canvas ref={canvasRef} className={`interactive-wave ${className}`} role="presentation" />;
}
