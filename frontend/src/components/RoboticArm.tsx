import { memo } from 'react';

/**
 * A lightweight illustrative robotic arm composed of layered SVG paths.
 * Keeps bundle size small while providing a visual anchor for the landing page.
 */
function RoboticArmComponent() {
  return (
    <svg
      role="img"
      aria-labelledby="robotic-arm-title robotic-arm-desc"
      viewBox="0 0 420 320"
      width="100%"
      height="100%"
      style={{ maxWidth: 420 }}
    >
      <title id="robotic-arm-title">Robotic brewing arm illustration</title>
      <desc id="robotic-arm-desc">
        Stylized illustration of a robotic arm pouring a drink with sensor highlights.
      </desc>
      <defs>
        <linearGradient id="arm-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#A4D9B9" />
          <stop offset="50%" stopColor="#7AC7C4" />
          <stop offset="100%" stopColor="#5AB0F3" />
        </linearGradient>
        <linearGradient id="accent-gradient" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor="#FFD68A" />
          <stop offset="100%" stopColor="#FF9EA5" />
        </linearGradient>
        <filter id="glow" x="-40%" y="-40%" width="180%" height="180%">
          <feGaussianBlur stdDeviation="12" result="coloredBlur" />
          <feMerge>
            <feMergeNode in="coloredBlur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>

      <rect x="20" y="200" width="180" height="20" rx="10" fill="#101820" opacity="0.2" />

      <g filter="url(#glow)" opacity="0.65">
        <circle cx="312" cy="86" r="18" fill="url(#accent-gradient)" />
        <circle cx="218" cy="156" r="12" fill="url(#accent-gradient)" />
        <circle cx="160" cy="228" r="10" fill="url(#accent-gradient)" />
      </g>

      <g fill="none" stroke="url(#arm-gradient)" strokeLinecap="round" strokeLinejoin="round">
        <path strokeWidth="32" d="M94 240c48-70 70-118 126-156 68-48 132-22 132-22" />
        <path strokeWidth="20" d="M188 176c58-32 108-48 140-48" opacity="0.8" />
        <path strokeWidth="16" d="M152 236c18-38 42-72 74-96" opacity="0.6" />
      </g>

      <g fill="#101820">
        <ellipse cx="95" cy="250" rx="32" ry="18" opacity="0.24" />
        <circle cx="96" cy="236" r="22" fill="#141B22" stroke="#202A33" strokeWidth="4" />
      </g>

      <g transform="translate(292 140)">
        <path
          d="M32 0c-17.6 0-32 14.4-32 32s14.4 32 32 32h12c8.8 0 16 7.2 16 16v28c0 5.5 4.5 10 10 10s10-4.5 10-10V80c0-30.9-25.1-56-56-56Z"
          fill="#0F1621"
          stroke="url(#arm-gradient)"
          strokeWidth="6"
        />
        <circle cx="32" cy="32" r="16" fill="#111B29" stroke="#1E2834" strokeWidth="6" />
        <circle cx="32" cy="32" r="6" fill="url(#accent-gradient)" />
      </g>

      <g transform="translate(220 228)">
        <path
          d="M64 0H14C6.3 0 0 6.3 0 14s6.3 14 14 14h18c9.9 0 18 8.1 18 18v18c0 6.6 5.4 12 12 12s12-5.4 12-12V18C84 8.1 75.9 0 66 0Z"
          fill="#0F1621"
          stroke="url(#arm-gradient)"
          strokeWidth="6"
        />
        <circle cx="56" cy="64" r="8" fill="url(#accent-gradient)" />
      </g>

      <g transform="translate(60 132)">
        <path
          d="M0 44c0-20.4 16.6-37 37-37s37 16.6 37 37v12c0 20.4-16.6 37-37 37S0 76.4 0 56Z"
          fill="#0F1621"
          stroke="url(#arm-gradient)"
          strokeWidth="6"
        />
        <circle cx="37" cy="56" r="14" fill="#111B29" stroke="#1E2834" strokeWidth="6" />
        <circle cx="37" cy="56" r="6" fill="url(#accent-gradient)" />
      </g>
    </svg>
  );
}

export const RoboticArm = memo(RoboticArmComponent);


