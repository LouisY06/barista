import type { CartLineItem, KnotReceipt } from '../types';
import '../styles/checkout.css';

type CheckoutPageProps = {
  cartCount: number;
  items: CartLineItem[];
  onProcessPayment: () => void;
  paymentState: 'idle' | 'processing' | 'success';
  lastReceipt: KnotReceipt | null;
};

export function CheckoutPage({ cartCount, items, onProcessPayment, paymentState, lastReceipt }: CheckoutPageProps) {
  const subtotal = items.reduce((sum, item) => sum + item.price, 0);

  return (
    <div className="checkout-root">
      <section className="checkout-panel">
        <header>
          <span className="checkout-kicker">CAF-E</span>
          <h1>Checkout</h1>
          <p>
            Review your crafted pours and confirm your session. Knot securely authenticates your saved merchant account before
            releasing the order.
          </p>
        </header>

        <div className="checkout-summary">
          <div className="knot-info">
            <div>
              <span className="summary-label">Items queued</span>
              <span className="summary-value">{cartCount}</span>
            </div>
            <div className="knot-tooltip-trigger" aria-describedby="knot-tooltip">
              Why Knot?
              <div id="knot-tooltip" className="knot-tooltip">
                Knot handles secure authentication with the merchant before CAF-E commits your charge. Sessions expire after
                each checkout, keeping credentials safe.
              </div>
            </div>
          </div>
          <p className="summary-note">
            Knot will authorize this purchase against your linked merchant profile. Subtotal <strong>${subtotal.toFixed(2)}</strong>.
          </p>

          {cartCount > 0 && (
            <ul className="checkout-list">
              {items.map((item) => (
                <li key={item.id}>
                  <div>
                    <strong>{item.name}</strong>
                    <span>${item.price.toFixed(2)}</span>
                  </div>
                  <p>
                    {item.temperature} · {item.milk} · Intensity {item.intensity}%
                  </p>
                </li>
              ))}
            </ul>
          )}

          {lastReceipt && (
            <div className="checkout-receipt">
              <header>
                <span>Knot Receipt</span>
                <code>{lastReceipt.txId ?? lastReceipt.id}</code>
              </header>
              <p>
                Session <strong>{lastReceipt.sessionId}</strong> · {new Date(lastReceipt.createdAt).toLocaleString()} · Total $
                {lastReceipt.subtotal.toFixed(2)} · Loyalty +{lastReceipt.loyaltyDelta ?? 0} ·{' '}
                {lastReceipt.paymentStatus ?? 'PENDING'}
              </p>
            </div>
          )}
        </div>

        <footer>
          <button
            type="button"
            className="checkout-primary"
            onClick={onProcessPayment}
            disabled={cartCount === 0 || paymentState === 'processing'}
          >
            {paymentState === 'processing' ? 'Processing with Knot…' : 'Pay with Knot'}
          </button>
          <button type="button" className="checkout-secondary" onClick={() => history.back()}>
            Back to menu
          </button>
        </footer>
      </section>
    </div>
  );
}

