import type { CartLineItem } from '../types';
import '../styles/cart.css';

type CartModalProps = {
  items: CartLineItem[];
  onClose: () => void;
  onCheckout: () => void;
  onRemoveItem: (id: string) => void;
};

export function CartModal({ items, onClose, onCheckout, onRemoveItem }: CartModalProps) {
  const subtotal = items.reduce((sum, item) => sum + item.price, 0);
  const tax = subtotal * 0.08;
  const total = subtotal + tax;

  return (
    <div className="cart-modal-backdrop" role="dialog" aria-modal="true" aria-label="Cart details">
      <div className="cart-modal">
        <header className="cart-modal__header">
          <div>
            <span className="cart-modal__eyebrow">CAF-E</span>
            <h2>Session Cart</h2>
          </div>
          <button type="button" className="cart-modal__close" onClick={onClose} aria-label="Close cart">
            ×
          </button>
        </header>

        {items.length === 0 ? (
          <div className="cart-modal__empty">
            <p>Your cart is empty. Add a matcha pour to begin checkout.</p>
          </div>
        ) : (
          <div className="cart-modal__body">
            <ul className="cart-modal__list">
              {items.map((item) => (
                <li key={item.id}>
                  <div>
                    <strong>{item.name}</strong>
                    <span>
                      {item.temperature} · {item.milk} · Intensity {item.intensity}%
                    </span>
                    {item.notes ? <span className="cart-modal__notes">{item.notes}</span> : null}
                  </div>
                  <div className="cart-modal__item-meta">
                    <span>${item.price.toFixed(2)}</span>
                    <button type="button" onClick={() => onRemoveItem(item.id)} aria-label={`Remove ${item.name}`}>
                      Remove
                    </button>
                  </div>
                </li>
              ))}
            </ul>

            <div className="cart-modal__summary">
              <div>
                <span>Subtotal</span>
                <span>${subtotal.toFixed(2)}</span>
              </div>
              <div>
                <span>Tax (8%)</span>
                <span>${tax.toFixed(2)}</span>
              </div>
              <div className="cart-modal__total">
                <span>Total</span>
                <strong>${total.toFixed(2)}</strong>
              </div>
            </div>
          </div>
        )}

        <footer className="cart-modal__footer">
          <button type="button" className="cart-modal__secondary" onClick={onClose}>
            Continue ordering
          </button>
          <button type="button" className="cart-modal__primary" onClick={onCheckout} disabled={!items.length}>
            Checkout with Knot
          </button>
        </footer>
      </div>
    </div>
  );
}


