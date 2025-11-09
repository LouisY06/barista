import type { KnotReceipt } from '../types';
import '../styles/status.css';

type StatusPageProps = {
  latestReceipt: KnotReceipt | null;
  loyaltyBalance: number;
  receipts: KnotReceipt[];
};

export function StatusPage({ latestReceipt, loyaltyBalance, receipts }: StatusPageProps) {
  const txSuffix = latestReceipt?.txId ? latestReceipt.txId.slice(-6) : null;

  return (
    <div className="status-root">
      <section className="status-hero">
        <div>
          <span className="status-kicker">Brew Queue</span>
          <h1>CAF-E Session Status</h1>
          {latestReceipt ? (
            <p>
              Paid via Knot • TX: {latestReceipt.txId}{' '}
              {latestReceipt.paymentStatus ? <>• {latestReceipt.paymentStatus}</> : null}
            </p>
          ) : (
            <p>No active brews. Start an order to generate a Knot transaction.</p>
          )}
        </div>
        <div className="status-balance">
          <span className="label">Loyalty Points</span>
          <strong>{loyaltyBalance}</strong>
          <span className="caption">+1 credited per Knot settlement</span>
        </div>
      </section>

      <section className="status-ledger">
        <header>
          <h2>Settlement Ledger</h2>
          {txSuffix ? <span>Last TX …{txSuffix}</span> : null}
        </header>
        {receipts.length === 0 ? (
          <p className="status-empty">No Knot transactions recorded yet.</p>
        ) : (
          <ul>
            {receipts
              .slice()
              .reverse()
              .map((receipt) => (
                <li key={receipt.id}>
                  <div>
                    <strong>{receipt.merchant}</strong>
                    <span>{new Date(receipt.createdAt).toLocaleString()}</span>
                  </div>
                  <div>
                    <span className="status-total">${receipt.subtotal.toFixed(2)}</span>
                    <span className="status-tx">TX {receipt.txId ?? '—'}</span>
                    <span className="status-loyalty">
                      +{receipt.loyaltyDelta ?? 0} loyalty · {receipt.paymentStatus ?? 'PENDING'}
                    </span>
                  </div>
                </li>
              ))}
          </ul>
        )}
      </section>
    </div>
  );
}


