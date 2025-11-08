import '../styles/theme-toggle.css';

type Theme = 'light' | 'dark';

type ThemeToggleProps = {
  theme: Theme;
  onToggle: () => void;
};

export function ThemeToggle({ theme, onToggle }: ThemeToggleProps) {
  const isDark = theme === 'dark';

  return (
    <button
      type="button"
      className={`theme-toggle ${isDark ? 'is-on' : 'is-off'}`}
      aria-pressed={isDark}
      onClick={onToggle}
      title="Toggle light/dark mode"
    >
      <span className="toggle-surface" aria-hidden>
        <span className="toggle-base" />
        <span className="toggle-active" />
        <span className="toggle-shine" />
        <span className="toggle-shadow" />
        <span className="toggle-thumb">
          <span className="toggle-thumb-core" />
          <span className="toggle-thumb-glow" />
        </span>
      </span>
      <span className="toggle-label">{isDark ? 'Dark' : 'Light'}</span>
    </button>
  );
}
