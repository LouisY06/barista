export function Footer() {
  return (
    <footer className="border-t border-white/10 bg-gradient-to-b from-black via-black/95 to-black py-12 text-white">
      <div className="mx-auto flex max-w-6xl flex-col items-center gap-6 px-6 text-center">
        <p className="text-sm text-neutral-400">© 2025 MatchaBot.</p>
        <nav
          className="flex items-center text-sm text-neutral-500"
          style={{ columnGap: '2.5rem', letterSpacing: '0.08em' }}
          aria-label="Footer navigation"
        >
          <a className="transition hover:text-neutral-200" href="/status">
            Status
          </a>
          <a className="transition hover:text-neutral-200" href="/docs">
            Docs
          </a>
          <a
            className="transition hover:text-neutral-200"
            href="https://github.com/yourorg/matchabot"
            target="_blank"
            rel="noreferrer"
          >
            GitHub
          </a>
        </nav>
      </div>
    </footer>
  );
}

