import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import './styles/app.css';
import { LandingPage } from './pages/LandingPage';
import { OrderPage } from './pages/OrderPage';
import { RewardsPage } from './pages/RewardsPage';
import { ProfilePage } from './pages/ProfilePage';
import { CheckoutPage } from './pages/CheckoutPage';
import { CheckoutCompletePage } from './pages/CheckoutCompletePage';
import { OrdersPage } from './pages/OrdersPage';
import { StatusPage } from './pages/StatusPage';
import { HeaderTabs } from './components/HeaderTabs';
import { ThemeToggle } from './components/ThemeToggle';
import { CartButton } from './components/CartButton';
import { CartModal } from './components/CartModal';
import { KnotPaymentModal } from './components/KnotPaymentModal';
import type { CartLineItem, KnotReceipt } from './types';

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:5001/api';

const generateId = (prefix: string) => `${prefix}_${Math.random().toString(36).slice(2, 10)}`;

type Theme = 'light' | 'dark';

const STORAGE_KEY = 'caf-e-theme';
const RECEIPTS_STORAGE_KEY = 'caf-e-receipts';

function AppShell() {
  const navigate = useNavigate();
  const [theme, setTheme] = useState<Theme>(() => {
    if (typeof window === 'undefined') return 'light';
    const stored = window.localStorage.getItem(STORAGE_KEY);
    return stored === 'dark' ? 'dark' : 'light';
  });
  const [cartItems, setCartItems] = useState<CartLineItem[]>([]);
  const [cartOpen, setCartOpen] = useState(false);
  const [paymentState, setPaymentState] = useState<'idle' | 'processing' | 'success'>('idle');
  const [paymentOpen, setPaymentOpen] = useState(false);
  const [paymentItems, setPaymentItems] = useState<CartLineItem[]>([]);
  const [receipts, setReceipts] = useState<KnotReceipt[]>([]);
  const [latestReceipt, setLatestReceipt] = useState<KnotReceipt | null>(null);
  const [currentOrderId, setCurrentOrderId] = useState<string | null>(null);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    try {
      const stored = window.localStorage.getItem(RECEIPTS_STORAGE_KEY);
      if (!stored) return;
      const parsed = JSON.parse(stored);
      if (!Array.isArray(parsed) || parsed.length === 0) return;

      const normalized: KnotReceipt[] = parsed
        .map((entry: any, receiptIndex: number) => {
          if (!entry || typeof entry !== 'object') return null;
          const lineItems = Array.isArray(entry.items ?? entry.line_items)
            ? (entry.items ?? entry.line_items).map((item: any, itemIndex: number) => ({
                id: item?.id ?? item?.drinkId ?? generateId(`item_${receiptIndex}_${itemIndex}`),
                drinkId: item?.drinkId ?? item?.drink_id ?? 'custom',
                name: item?.name ?? 'Custom Pour',
                milk: item?.milk ?? 'Whole Milk',
                temperature: item?.temperature === 'Cold' ? 'Cold' : 'Hot',
                intensity: Number(item?.intensity ?? 80),
                price: Number(item?.price ?? 0),
              }))
            : [];

          const createdAt = entry.createdAt ?? entry.created_at ?? new Date().toISOString();

          return {
            id: entry.id ?? entry.receipt_id ?? generateId(`rec_${receiptIndex}`),
            sessionId: entry.sessionId ?? entry.session_id ?? 'unknown',
            orderId: entry.orderId ?? entry.order_id,
            merchant: entry.merchant ?? 'CAF-E Autonomous Bar',
            subtotal: Number(entry.subtotal ?? entry.total ?? 0),
            items: lineItems,
            createdAt,
            currency: entry.currency ?? 'USD',
            txId: entry.txId ?? entry.tx_id,
            paymentStatus: entry.paymentStatus ?? entry.payment_status ?? 'CONFIRMED',
            loyaltyDelta: entry.loyaltyDelta ?? entry.loyalty_delta ?? 0,
          } satisfies KnotReceipt;
        })
        .filter(Boolean) as KnotReceipt[];

      if (!normalized.length) return;
      setReceipts((prev) => (prev.length ? prev : normalized));
      setLatestReceipt((prev) => prev ?? normalized[normalized.length - 1]);
    } catch (error) {
      console.warn('Failed to restore receipts from storage', error);
    }
  }, []);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    try {
      if (!receipts.length) {
        window.localStorage.removeItem(RECEIPTS_STORAGE_KEY);
        return;
      }
      window.localStorage.setItem(RECEIPTS_STORAGE_KEY, JSON.stringify(receipts));
    } catch (error) {
      console.warn('Failed to persist receipts to storage', error);
    }
  }, [receipts]);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      window.localStorage.setItem(STORAGE_KEY, theme);
    }
  }, [theme]);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
  }, [theme]);

  const themeClass = useMemo(() => (theme === 'dark' ? 'dark' : 'light'), [theme]);
  const cartCount = cartItems.length;
  const loyaltyBalance = useMemo(
    () => receipts.reduce((sum, receipt) => sum + (receipt.loyaltyDelta ?? 0), 0),
    [receipts]
  );

  const syncReceiptsFromBackend = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/receipts?limit=25`);
      if (!response.ok) return;
      const payload = await response.json();
      if (!Array.isArray(payload?.receipts)) return;

      const normalized: KnotReceipt[] = payload.receipts.map((entry: any, receiptIndex: number) => {
        const rawItems = Array.isArray(entry.line_items ?? entry.items)
          ? (entry.line_items ?? entry.items)
          : [];
        const items: CartLineItem[] = rawItems.map((item: any, itemIndex: number) => ({
          id: item?.id ?? item?.drinkId ?? generateId(`item_${receiptIndex}_${itemIndex}`),
          drinkId: item?.drinkId ?? item?.drink_id ?? 'custom',
          name: item?.name ?? item?.label ?? 'Custom Pour',
          milk: item?.milk ?? 'Whole Milk',
          temperature: item?.temperature === 'Cold' ? 'Cold' : 'Hot',
          intensity: Number(item?.intensity ?? item?.strength ?? 80),
          price: Number(item?.price ?? item?.amount ?? 0),
        }));

        return {
          id: entry.receipt_id ?? entry.id ?? generateId('rec'),
          sessionId: entry.session_id ?? entry.sessionId ?? 'unknown',
          orderId: entry.order_id ?? entry.orderId,
          merchant:
            entry.raw_payload?.merchant ??
            entry.metadata?.merchant ??
            entry.merchant ??
            'CAF-E Autonomous Bar',
          subtotal: Number(entry.total ?? entry.subtotal ?? 0),
          items,
          createdAt: entry.created_at ?? entry.createdAt ?? new Date().toISOString(),
          currency: entry.currency ?? entry.raw_payload?.currency ?? 'USD',
          txId: entry.tx_id ?? entry.raw_payload?.txId ?? entry.raw_payload?.tx_id,
          paymentStatus: entry.payment_status ?? entry.raw_payload?.paymentStatus ?? 'CONFIRMED',
          loyaltyDelta: entry.loyalty_delta ?? entry.raw_payload?.loyaltyDelta ?? 0,
        } satisfies KnotReceipt;
      });

      setReceipts(normalized);
      setLatestReceipt(normalized[normalized.length - 1] ?? null);
    } catch (error) {
      console.warn('Failed to fetch stored receipts', error);
    }
  }, []);

  useEffect(() => {
    void syncReceiptsFromBackend();
  }, [syncReceiptsFromBackend]);

  const ensureOrderId = useCallback(() => {
    setCurrentOrderId((prev) => prev ?? generateId('ord'));
  }, []);

  const handleAddToCart = (item: CartLineItem) => {
    ensureOrderId();
    setCartItems((prev) => [...prev, item]);
    setCartOpen(true);
    setPaymentState('idle');
  };

  const handleOpenCart = () => setCartOpen(true);
  const handleCloseCart = () => setCartOpen(false);
  const handleToggleCart = () => setCartOpen((prev) => !prev);
  const handleCheckout = () => {
    setCartOpen(false);
    navigate('/checkout');
  };

  const handleProcessPayment = () => {
    if (!cartItems.length || paymentState === 'processing') return;
    ensureOrderId();
    setPaymentItems(cartItems);
    setPaymentState('processing');
    setPaymentOpen(true);
  };

  const archiveOrderWithBackend = useCallback(
    async (orderId: string, items: CartLineItem[], receipt: KnotReceipt) => {
      const orderPayload = {
        order_id: orderId,
        status: receipt.paymentStatus === 'CONFIRMED' ? 'paid' : 'pending',
        total: receipt.subtotal,
        currency: receipt.currency ?? 'USD',
        customer_id: 'guest',
        items: items.map((item) => ({
          id: item.id,
          drinkId: item.drinkId,
          name: item.name,
          temperature: item.temperature,
          milk: item.milk,
          intensity: item.intensity,
          price: item.price,
        })),
        metadata: {
          sessionId: receipt.sessionId,
          merchant: receipt.merchant,
          createdAt: receipt.createdAt,
          knotTxId: receipt.txId,
          loyaltyDelta: receipt.loyaltyDelta ?? 0,
        },
        knot_tx_id: receipt.txId,
        payment_status: receipt.paymentStatus,
        loyalty_earned: receipt.loyaltyDelta ?? 0,
        paid: receipt.paymentStatus === 'CONFIRMED',
      };

      try {
        await fetch(`${API_BASE}/orders/archive`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(orderPayload),
        });
      } catch (error) {
        console.warn('Failed to archive order', error);
      }
    },
    []
  );

  const archiveReceiptWithBackend = useCallback(async (receipt: KnotReceipt) => {
    const receiptPayload = {
      receipt_id: receipt.id,
      order_id: receipt.orderId,
      session_id: receipt.sessionId,
      total: receipt.subtotal,
      currency: receipt.currency ?? 'USD',
      line_items: receipt.items,
      raw_payload: receipt,
      created_at: receipt.createdAt,
      tx_id: receipt.txId,
      loyalty_delta: receipt.loyaltyDelta ?? 0,
      payment_status: receipt.paymentStatus,
    };

    try {
      await fetch(`${API_BASE}/receipts`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(receiptPayload),
      });
    } catch (error) {
      console.warn('Failed to archive receipt', error);
    }
  }, []);

  const handlePaymentComplete = (receipt: KnotReceipt) => {
    const orderId = currentOrderId ?? generateId('ord');
    const enrichedReceipt: KnotReceipt = {
      ...receipt,
      orderId,
      currency: receipt.currency ?? 'USD',
      loyaltyDelta: receipt.loyaltyDelta ?? 0,
    };

    setReceipts((prev) => [...prev, enrichedReceipt]);
    setLatestReceipt(enrichedReceipt);
    setCartItems([]);
    setPaymentState('success');
    setPaymentOpen(false);
    setCurrentOrderId(null);

    void archiveOrderWithBackend(orderId, receipt.items, enrichedReceipt);
    void archiveReceiptWithBackend(enrichedReceipt);
    void syncReceiptsFromBackend();

    navigate('/checkout/complete');
  };

  const handlePaymentCancel = () => {
    setPaymentState('idle');
    setPaymentOpen(false);
  };

  return (
    <div className={`app-shell ${themeClass}`}>
      <header className="app-bar">
        <span className="brand-mark">CAF-E</span>
        <div className="header-controls">
          <HeaderTabs />
          <CartButton count={cartCount} isOpen={cartOpen} onClick={handleToggleCart} />
          <ThemeToggle theme={theme} onToggle={() => setTheme(theme === 'dark' ? 'light' : 'dark')} />
        </div>
      </header>

      <main className="app-main">
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route
            path="/order"
            element={<OrderPage cartCount={cartCount} onAddToCart={handleAddToCart} onOpenCart={handleOpenCart} />}
          />
          <Route path="/rewards" element={<RewardsPage loyaltyBalance={loyaltyBalance} />} />
          <Route path="/profile" element={<ProfilePage receipts={receipts} loyaltyBalance={loyaltyBalance} />} />
          <Route path="/status" element={<StatusPage latestReceipt={latestReceipt} loyaltyBalance={loyaltyBalance} receipts={receipts} />} />
          <Route
            path="/orders"
            element={<OrdersPage receipts={receipts} />}
          />
          <Route
            path="/checkout"
            element={
              <CheckoutPage
                cartCount={cartCount}
                items={cartItems}
                onProcessPayment={handleProcessPayment}
                paymentState={paymentState}
                lastReceipt={latestReceipt}
              />
            }
          />
          <Route
            path="/checkout/complete"
            element={<CheckoutCompletePage receipt={latestReceipt} />}
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>

      {cartOpen && <CartModal items={cartItems} onClose={handleCloseCart} onCheckout={handleCheckout} />}
      {paymentOpen && (
        <KnotPaymentModal
          items={paymentItems}
          onClose={handlePaymentCancel}
          onComplete={handlePaymentComplete}
          orderId={currentOrderId}
          apiBase={API_BASE}
        />
      )}
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AppShell />
    </BrowserRouter>
  );
}
