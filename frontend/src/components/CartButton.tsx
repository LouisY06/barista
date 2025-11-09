type CartButtonProps = {
  count: number;
  onClick: () => void;
};

export function CartButton({ count, onClick }: CartButtonProps) {
  const label = count === 0 ? 'Open cart' : `Open cart with ${count} item${count === 1 ? '' : 's'}`;

  return (
    <button type="button" className="cart-button" onClick={onClick} aria-label={label}>
      <span className="cart-button__icon" aria-hidden>
        <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="1.5">
          <path d="M3 3h2l1 4h13l-1.2 7H8.2L7 7" strokeLinecap="round" strokeLinejoin="round" />
          <circle cx="9" cy="19" r="1.25" />
          <circle cx="18" cy="19" r="1.25" />
        </svg>
      </span>
      <span className="cart-button__label">Cart</span>
      <span className={`cart-button__badge ${count === 0 ? 'is-empty' : ''}`} aria-hidden>
        {count}
      </span>
    </button>
  );
}


