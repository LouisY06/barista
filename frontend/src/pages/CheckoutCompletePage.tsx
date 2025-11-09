import { useNavigate } from 'react-router-dom';
import type { KnotReceipt } from '../types';
import '../styles/checkout.css';

type CheckoutCompletePageProps = {
  receipt: KnotReceipt | null;
};

export function CheckoutCompletePage({ receipt }: CheckoutCompletePageProps) {
  const navigate = useNavigate();

  return (
    <div className="checkout-root">
      <section className="checkout-panel checkout-complete">
        <header>
          <span className="checkout-kicker">CAF-E</span>
          <h1>{receipt?.paymentStatus === 'CONFIRMED' ? 'Payment Confirmed' : 'Payment Pending'}</h1>
          <p>
            {receipt?.paymentStatus === 'CONFIRMED'
              ? 'Your Knot-linked merchant account authorized this order. A receipt has been saved to your profile.'
              : 'Knot is verifying this transaction. We will trigger the brew once settlement is acknowledged.'}
          </p>
        </header>

        {receipt ? (
          <div className="checkout-receipt emphasized">
            <header>
              <span>Knot Receipt</span>
              <code>{receipt.txId ?? receipt.id}</code>
            </header>
            <p>
              Session <strong>{receipt.sessionId}</strong> · {new Date(receipt.createdAt).toLocaleString()} · Total $
              {receipt.subtotal.toFixed(2)} · Loyalty +{receipt.loyaltyDelta ?? 0} ·{' '}
              {receipt.paymentStatus ?? 'PENDING'}
            </p>
            <div className="checkout-complete-items">
              {receipt.items.map((item) => (
                <div key={item.id}>
                  <strong>{item.name}</strong>
                  <span>
                    {item.temperature} · {item.milk} · Intensity {item.intensity}%
                  </span>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="checkout-receipt emphasized">
            <p>Receipt data unavailable. Return to the menu to begin a new order.</p>
          </div>
        )}

        <footer>
          <button type="button" className="checkout-primary" onClick={() => navigate('/order')}>
            start a new order
          </button>
          <button type="button" className="checkout-secondary" onClick={() => navigate('/profile')}>
            view receipts
          </button>
        </footer>
      </section>
    </div>
  );
}

