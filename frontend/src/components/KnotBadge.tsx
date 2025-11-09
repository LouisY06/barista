import { useState } from 'react';

export function KnotBadge() {
  const [open, setOpen] = useState(false);

  return (
    <div
      className={`knot-badge ${open ? 'is-open' : ''}`}
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
      onFocus={() => setOpen(true)}
      onBlur={() => setOpen(false)}
      tabIndex={0}
      role="button"
      aria-label="What is Knot checkout?"
    >
      <span className="knot-badge__dot">?</span>
      <div className="knot-badge__popover">
        <span className="knot-badge__title">Knot checkout</span>
        <p>Knot securely verifies your saved merchant credentials before authorizing this purchase.</p>
      </div>
    </div>
  );
}
