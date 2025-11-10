import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import type { KnotReceipt } from '../types';
import '../styles/profile.css';

type OrdersPageProps = {
  receipts: KnotReceipt[];
};

export function OrdersPage({ receipts }: OrdersPageProps) {
  const navigate = useNavigate();
  const orderedReceipts = useMemo(() => receipts.slice().reverse(), [receipts]);

  return (
    <div className="profile-root orders-view">
      <section className="orders-card">
        <header>
          <div>
            <span className="orders-kicker">Account</span>
            <h2>All Receipts</h2>
            <span className="orders-count">
              {orderedReceipts.length}{' '}
              {orderedReceipts.length === 1 ? 'receipt' : 'receipts'}
            </span>
          </div>
          <button type="button" className="orders-meta" onClick={() => navigate('/profile')}>
            Back to profile
          </button>
        </header>

        {orderedReceipts.length === 0 ? (
          <p className="orders-empty">No Knot receipts yet. Complete a checkout to generate one.</p>
        ) : (
          <ul>
            {orderedReceipts.map((receipt) => (
              <li key={receipt.id}>
                <div className="orders-summary">
                  <div>
                    <strong>{receipt.merchant}</strong>
                    <span>{new Date(receipt.createdAt).toLocaleString()}</span>
                  </div>
                  <div>
                    <span className="orders-total">${receipt.subtotal.toFixed(2)}</span>
                      <code>{receipt.txId ?? receipt.id}</code>
                  </div>
                </div>
                <p className="orders-session">
                  Session {receipt.sessionId} · Loyalty +{receipt.loyaltyDelta ?? 0} · {receipt.paymentStatus ?? 'CONFIRMED'}
                </p>
                <div className="orders-items">
                  {receipt.items.map((item, index) => (
                    <span key={item.id ?? `${receipt.id}-${index}`}>
                      {item.name} · {item.temperature} · {item.milk}
                    </span>
                  ))}
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}

