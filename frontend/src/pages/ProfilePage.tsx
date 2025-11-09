import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import type { KnotReceipt } from '../types';
import '../styles/profile.css';

type ProfilePageProps = {
  receipts: KnotReceipt[];
  loyaltyBalance: number;
};

export function ProfilePage({ receipts, loyaltyBalance }: ProfilePageProps) {
  const navigate = useNavigate();
  const recentReceipts = useMemo(() => receipts.slice(-3).reverse(), [receipts]);
  const latestReceipt = receipts.length ? receipts[receipts.length - 1] : null;
  const latestTxSuffix = latestReceipt?.txId ? latestReceipt.txId.slice(-6) : null;

  return (
    <div className="profile-root">
      <section className="profile-hero">
        <div className="profile-banner" />
        <div className="profile-top">
          <div>
            <h1>Hey, Alana Kwan</h1>
            <p>CAF-E member since 2024 · Precision in Every Pour</p>
          </div>
        </div>
        {latestReceipt ? (
          <div className="profile-status">
            <span>
              Paid via Knot • TX {latestTxSuffix ? `…${latestTxSuffix}` : latestReceipt.txId ?? '—'} • $
              {latestReceipt.subtotal.toFixed(2)}
            </span>
            <span>{latestReceipt.paymentStatus ?? 'CONFIRMED'}</span>
          </div>
        ) : (
          <div className="profile-status muted">
            <span>No Knot payments yet</span>
            <span>Start an order to earn loyalty sparks</span>
          </div>
        )}
        <div className="profile-stats">
          <div>
            <span className="stat-label">Coupons</span>
            <span className="stat-value">0</span>
          </div>
          <div>
            <span className="stat-label">Gift Cards</span>
            <span className="stat-value">0</span>
          </div>
          <div>
            <span className="stat-label">Sparks</span>
            <span className="stat-value">{loyaltyBalance}</span>
            <span className="stat-meta">+1 per Knot capture</span>
          </div>
        </div>
      </section>

      <section className="orders-card">
        <header>
          <div>
            <span className="orders-kicker">Account</span>
            <h2>My Orders</h2>
          </div>
          <button type="button" className="orders-meta" onClick={() => navigate('/orders')}>
            See all →
          </button>
        </header>

        {recentReceipts.length === 0 ? (
          <p className="orders-empty">No Knot receipts yet. Complete a checkout to generate one.</p>
        ) : (
          <ul>
            {recentReceipts.map((receipt) => (
              <li key={receipt.id}>
                <div className="orders-summary">
                  <div>
                    <strong>{receipt.merchant}</strong>
                    <span>{new Date(receipt.createdAt).toLocaleString()}</span>
                  </div>
                  <div>
                    <span className="orders-total">${receipt.subtotal.toFixed(2)}</span>
                    <code>{receipt.id}</code>
                  </div>
                </div>
                <p className="orders-session">Session {receipt.sessionId}</p>
                <div className="orders-items">
                  {receipt.items.map((item) => (
                    <span key={item.id}>
                      {item.name} · {item.temperature} · {item.milk}
                    </span>
                  ))}
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="profile-menu">
        <h2>Account</h2>
        <ul>
          <li>
            <button type="button">
              <span>FAQ</span>
            </button>
          </li>
          <li>
            <button type="button">
              <span>Settings</span>
            </button>
          </li>
          <li>
            <button type="button">
              <span>Payment Methods</span>
            </button>
          </li>
          <li>
            <button type="button">
              <span>Feedback & Suggestions</span>
            </button>
          </li>
        </ul>
      </section>

      <section className="profile-menu">
        <h2>Membership</h2>
        <ul>
          <li>
            <button type="button">
              <span>Invite Friends</span>
              <span className="menu-meta">Earn Sparks</span>
            </button>
          </li>
          <li>
            <button type="button">
              <span>Redeem Rewards</span>
            </button>
          </li>
        </ul>
      </section>
    </div>
  );
}
