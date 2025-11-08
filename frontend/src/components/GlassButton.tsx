import type { ButtonHTMLAttributes, ReactNode } from 'react';
import '../styles/glass-button.css';

type GlassButtonProps = {
  children: ReactNode;
  icon?: ReactNode;
} & ButtonHTMLAttributes<HTMLButtonElement>;

export function GlassButton({ children, icon, className = '', ...props }: GlassButtonProps) {
  return (
    <button className={`glass-button ${className}`} {...props}>
      <span className="glass-button__outer" />
      <span className="glass-button__inner">
        <span className="glass-button__label">{children}</span>
        {icon ? <span className="glass-button__icon">{icon}</span> : null}
      </span>
    </button>
  );
}
