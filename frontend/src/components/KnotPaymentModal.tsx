import React, { useEffect, useMemo, useState } from 'react';
import type { CartLineItem, KnotReceipt } from '../types';

type Step = {
  code: string;
  title: string;
  detail: string;
};

type KnotPaymentModalProps = {
  items: CartLineItem[];
  onClose: () => void;
  onComplete: (receipt: KnotReceipt) => void;
  orderId: string | null;
  apiBase: string;
};

const STEPS: Step[] = [
  {
    code: 'MERCHANT_CLICKED',
    title: 'Merchant Selected',
    detail: 'CAF-E kiosk connection initialized.',
  },
  {
    code: 'LOGIN_STARTED',
    title: 'Authenticating',
    detail: 'Secure Knot session exchanging credentials.',
  },
  {
    code: 'AUTHENTICATED',
    title: 'Merchant Verified',
    detail: 'Knot confirmed account credentials.',
  },
  {
    code: 'PAYMENT_CAPTURED',
    title: 'Payment Authorized',
    detail: 'Transaction captured and loyalty credited.',
  },
];

export function KnotPaymentModal({ items, onClose, onComplete, orderId, apiBase }: KnotPaymentModalProps) {
  const [activeStep, setActiveStep] = useState(0);
  const [serverStatus, setServerStatus] = useState<'idle' | 'pending' | 'error'>('idle');
  const amountCents = useMemo(() => Math.round(items.reduce((sum, item) => sum + item.price, 0) * 100), [items]);

  useEffect(() => {
    if (!items.length) return;

    const runCompletion = async () => {
      const total = items.reduce((sum, item) => sum + item.price, 0);
      const receipt: KnotReceipt = {
        id: `rec_${Math.random().toString(36).slice(2, 10)}`,
        sessionId: `sess_${Math.random().toString(36).slice(2, 12)}`,
        merchant: 'CAF-E Autonomous Bar',
        subtotal: parseFloat(total.toFixed(2)),
        items,
        createdAt: new Date().toISOString(),
        paymentStatus: 'PENDING',
      };

      if (!orderId) {
        onComplete(receipt);
        return;
      }

      setServerStatus('pending');
      try {
        const response = await fetch(`${apiBase}/pay/knot`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            orderId,
            amountCents,
            method: 'knot',
            items,
          }),
        });

        if (!response.ok) {
          throw new Error('Payment failed');
        }

        const payload = await response.json();
        receipt.paymentStatus = payload.status ?? 'CONFIRMED';
        receipt.txId = payload.txId;
        receipt.loyaltyDelta = payload.loyaltyDelta ?? 0;
        receipt.orderId = payload.orderId ?? orderId;
        receipt.currency = 'USD';
        setServerStatus('idle');
        onComplete(receipt);
      } catch (error) {
        console.warn('Knot payment error', error);
        setServerStatus('error');
        receipt.paymentStatus = 'FAILED';
        onComplete(receipt);
      }
    };

    const timers = STEPS.map((_, index) =>
      window.setTimeout(() => {
        setActiveStep(index);
        if (index === STEPS.length - 1) {
          window.setTimeout(() => {
            void runCompletion();
          }, 600);
        }
      }, (index + 1) * 900)
    );

    return () => {
      timers.forEach((id) => window.clearTimeout(id));
    };
  }, [items, onComplete, orderId, apiBase, amountCents]);

  return (
    <div className="knot-modal-backdrop" role="dialog" aria-modal="true" aria-label="Knot checkout">
      <div className="knot-modal">
        <header className="knot-modal__header">
          <div>
            <span className="knot-modal__title">Authenticating with Knot</span>
            <p className="knot-modal__subtitle">
              Securing your merchant session and authorizing payment.
              {serverStatus === 'pending' ? ' Finalizing settlement…' : null}
              {serverStatus === 'error' ? ' Unable to reach Knot services.' : null}
            </p>
          </div>
          <button type="button" className="knot-modal__close" onClick={onClose} aria-label="Cancel payment">
            ×
          </button>
        </header>

        <ol className="knot-modal__timeline">
          {STEPS.map((step, index) => {
            const status = index < activeStep ? 'done' : index === activeStep ? 'active' : 'pending';
            return (
              <li key={step.code} className={`timeline-item ${status}`}>
                <div className="timeline-dot" aria-hidden>
                  {index < activeStep ? '✓' : index + 1}
                </div>
                <div>
                  <strong>{step.title}</strong>
                  <span>{step.detail}</span>
                  <code>{step.code}</code>
                </div>
              </li>
            );
          })}
        </ol>

        <footer className="knot-modal__footer">
          <button type="button" className="knot-modal__secondary" onClick={onClose}>
            Cancel authorization
          </button>
        </footer>
      </div>
    </div>
  );
}

