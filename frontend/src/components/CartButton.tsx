type CartButtonProps = {
  count: number;
  isOpen?: boolean;
  onClick: () => void;
};

export function CartButton({ count, isOpen = false, onClick }: CartButtonProps) {
  const hasItems = count > 0;

  return (
    <button
      type="button"
      className="cart-button"
      onClick={onClick}
      aria-label={`View cart${hasItems ? `, ${count} item${count === 1 ? '' : 's'}` : ''}`}
      aria-expanded={isOpen}
    >
      <span className="cart-button__icon" aria-hidden>
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
          <path d="M7 9h10l1 11H6L7 9Z" />
          <path d="M9 9a3 3 0 0 1 6 0" />
        </svg>
      </span>
      {hasItems && <span className="cart-button__badge">{count}</span>}
    </button>
  );
}
