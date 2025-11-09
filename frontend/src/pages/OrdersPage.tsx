import type { KnotReceipt } from '../types';
import '../styles/orders.css';

type OrdersPageProps = {
  receipts: KnotReceipt[];
};

export function OrdersPage({ receipts }: OrdersPageProps) {
  const reversed = [...receipts].reverse();

  return (
    <div className="orders-root">
      <header className="orders-header">
        <div>
          <span className="orders-kicker">CAF-E Ledger</span>
          <h1>Order History</h1>
          <p>
            Every Knot-authorized session appears here with settlement status, loyalty earned, and itemized pours. Use this log
            to audit your robotic brews.
          </p>
        </div>
      </header>

      {reversed.length === 0 ? (
        <div className="orders-empty">No orders yet. Place a matcha pour to populate this history.</div>
      ) : (
        <ul className="orders-list">
          {reversed.map((receipt) => (
            <li key={receipt.id}>
              <div className="orders-list__head">
                <div>
                  <strong>{receipt.merchant}</strong>
                  <span>{new Date(receipt.createdAt).toLocaleString()}</span>
                </div>
                <div className="orders-list__meta">
                  <span className={`orders-status orders-status--${(receipt.paymentStatus ?? 'pending').toLowerCase()}`}>
                    {receipt.paymentStatus ?? 'PENDING'}
                  </span>
                  <span className="orders-total">${receipt.subtotal.toFixed(2)}</span>
                </div>
              </div>

              <div className="orders-list__body">
                <div className="orders-id">
                  <span>Order</span>
                  <code>{receipt.orderId ?? '—'}</code>
                </div>
                <div className="orders-id">
                  <span>Session</span>
                  <code>{receipt.sessionId}</code>
                </div>
                <div className="orders-id">
                  <span>Knot TX</span>
                  <code>{receipt.txId ?? 'Pending'}</code>
                </div>
                <div className="orders-id">
                  <span>Loyalty</span>
                  <strong>+{receipt.loyaltyDelta ?? 0}</strong>
                </div>
              </div>

              <div className="orders-items">
                {receipt.items.map((item) => (
                  <div key={item.id}>
                    <strong>{item.name}</strong>
                    <span>
                      {item.temperature} · {item.milk} · Intensity {item.intensity}%
                    </span>
                  </div>
                ))}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}


