import { useMemo, useRef, useState } from 'react';
import '../styles/kiosk.css';

type MenuItem = {
  id: string;
  name: string;
  price: number;
  tag?: string;
};

type SizeOption = { label: string; value: 'Small' | 'Medium' | 'Large'; price: number };
type MilkOption = { label: string; value: string; price: number };
type AddonOption = { label: string; value: string; price: number };

type CustomizationState = {
  size: SizeOption;
  ice: string;
  sweetness: string;
  milk: MilkOption;
  addons: AddonOption[];
  quantity: number;
};

type CartEntry = {
  id: string;
  item: MenuItem;
  customization: CustomizationState;
  total: number;
};

const signatureItems: MenuItem[] = [
  { id: 'cloud-matcha', name: 'Cloud Matcha Latte', price: 8.99, tag: 'Popular' },
  { id: 'emerald-dream', name: 'Emerald Dream', price: 9.49 },
  { id: 'sakura-matcha', name: 'Sakura Matcha', price: 9.99, tag: 'New' },
  { id: 'zen-garden', name: 'Zen Garden', price: 8.49 },
];

const fusionItems: MenuItem[] = [
  { id: 'honey-matcha', name: 'Honey Matcha', price: 8.79 },
  { id: 'coconut-matcha', name: 'Coconut Matcha', price: 9.49, tag: 'Popular' },
  { id: 'strawberry-matcha', name: 'Strawberry Matcha', price: 9.99 },
  { id: 'vanilla-matcha', name: 'Vanilla Bean Matcha', price: 8.99 },
];

const sizeOptions: SizeOption[] = [
  { label: 'Small', value: 'Small', price: 0 },
  { label: 'Medium +$1', value: 'Medium', price: 1 },
  { label: 'Large +$2', value: 'Large', price: 2 },
];

const iceOptions = ['No Ice', 'Light Ice', 'Regular Ice', 'Extra Ice'];
const sweetnessOptions = ['0%', '25%', '50%', '75%', '100%'];

const milkOptions: MilkOption[] = [
  { label: 'Whole Milk', value: 'Whole Milk', price: 0 },
  { label: 'Oat Milk +$0.75', value: 'Oat Milk', price: 0.75 },
  { label: 'Almond Milk +$0.75', value: 'Almond Milk', price: 0.75 },
  { label: 'Soy Milk +$0.50', value: 'Soy Milk', price: 0.5 },
];

const addonOptions: AddonOption[] = [
  { label: 'Boba +$1', value: 'Boba', price: 1 },
  { label: 'Grass Jelly +$0.75', value: 'Grass Jelly', price: 0.75 },
  { label: 'Pudding +$0.75', value: 'Pudding', price: 0.75 },
  { label: 'Cream Foam +$1.25', value: 'Cream Foam', price: 1.25 },
  { label: 'Extra Shot +$2', value: 'Extra Shot', price: 2 },
];

const defaultCustomization = (): CustomizationState => ({
  size: sizeOptions[0],
  ice: iceOptions[2],
  sweetness: sweetnessOptions[3],
  milk: milkOptions[0],
  addons: [],
  quantity: 1,
});

const getInitial = (name: string) => (name ? name.charAt(0).toUpperCase() : '');

export function KioskConsole() {
  const [activeCategory, setActiveCategory] = useState('signature');
  const [cart, setCart] = useState<CartEntry[]>([]);
  const [selectedItem, setSelectedItem] = useState<MenuItem | null>(null);
  const [customization, setCustomization] = useState<CustomizationState | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [syncState, setSyncState] = useState<'idle' | 'syncing' | 'complete'>('idle');

  const signatureRef = useRef<HTMLDivElement | null>(null);
  const fusionRef = useRef<HTMLDivElement | null>(null);

  const cartSummary = useMemo(() => {
    const count = cart.reduce((sum, entry) => sum + entry.customization.quantity, 0);
    const total = cart.reduce((sum, entry) => sum + entry.total, 0);
    return { count, total };
  }, [cart]);

  const modalTotal = useMemo(() => {
    if (!selectedItem || !customization) return 0;
    const base =
      selectedItem.price +
      customization.size.price +
      customization.milk.price +
      customization.addons.reduce((sum, addon) => sum + addon.price, 0);
    return base * customization.quantity;
  }, [selectedItem, customization]);

  const handleOpenModal = (item: MenuItem) => {
    setSelectedItem(item);
    setCustomization(defaultCustomization());
    setModalOpen(true);
  };

  const handleCloseModal = () => {
    setModalOpen(false);
    setSelectedItem(null);
    setCustomization(null);
  };

  const toggleAddon = (option: AddonOption) => {
    setCustomization((prev) => {
      if (!prev) return prev;
      const exists = prev.addons.find((addon) => addon.value === option.value);
      if (exists) {
        return { ...prev, addons: prev.addons.filter((addon) => addon.value !== option.value) };
      }
      return { ...prev, addons: [...prev.addons, option] };
    });
  };

  const handleConfirm = () => {
    if (!selectedItem || !customization) return;
    const entry: CartEntry = {
      id: `${selectedItem.id}-${Date.now()}`,
      item: selectedItem,
      customization: {
        ...customization,
        addons: [...customization.addons],
      },
      total: modalTotal,
    };
    setCart((prev) => [...prev, entry]);
    handleCloseModal();
  };

  const handleCheckout = () => {
    if (!cart.length) return;
    window.alert(`Order authorized · $${cartSummary.total.toFixed(2)}\nYour drinks will deploy in 5 minutes.`);
    setCart([]);
  };

  const handleSyncTaste = () => {
    if (syncState === 'syncing' || syncState === 'complete') return;
    setSyncState('syncing');
    setTimeout(() => setSyncState('complete'), 1000);
  };

  const handleCategoryClick = (key: string) => {
    setActiveCategory(key);
    if (key === 'signature') {
      signatureRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    } else if (key === 'fusion') {
      fusionRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  return (
    <div className="kiosk-root">
      <div className="console">
        <header className="console-header">
          <div className="grid">
            <div className="branding">
              <h1>MATCHA HAVEN</h1>
              <p>Autonomous Tea Atelier · Kyoto Precision</p>
            </div>
            <div className="status-card">
              <div>
                <strong>SESSION</strong>
                <p className="pill">
                  <svg viewBox="0 0 24 24" fill="none">
                    <path d="M3 12h18M3 17h18M3 7h18" strokeWidth="1.5" stroke="currentColor" />
                  </svg>
                  Ready for command
                </p>
              </div>
              <span>580 pts</span>
            </div>
          </div>

          <nav className="category-nav">
            <button
              className={`nav-chip ${activeCategory === 'signature' ? 'active' : ''}`}
              onClick={() => handleCategoryClick('signature')}
              type="button"
            >
              Signature <span className="badge">LIVE</span>
            </button>
            <button
              className={`nav-chip ${activeCategory === 'fusion' ? 'active' : ''}`}
              onClick={() => handleCategoryClick('fusion')}
              type="button"
            >
              Fusion
            </button>
            <button className={`nav-chip ${activeCategory === 'seasonal' ? 'active' : ''}`} onClick={() => handleCategoryClick('seasonal')} type="button">
              Seasonal
            </button>
            <button className={`nav-chip ${activeCategory === 'classics' ? 'active' : ''}`} onClick={() => handleCategoryClick('classics')} type="button">
              Classics
            </button>
            <button className={`nav-chip ${activeCategory === 'lattes' ? 'active' : ''}`} onClick={() => handleCategoryClick('lattes')} type="button">
              Lattes
            </button>
          </nav>
        </header>

        <main className="console-main">
          <section className="special">
            <div>
              <h3>Quantum Infusion Offer</h3>
              <p>Second beverage on us. Sync taste profile & we’ll mirror it instantly.</p>
            </div>
            <button
              type="button"
              className="cta"
              onClick={handleSyncTaste}
              disabled={syncState === 'syncing' || syncState === 'complete'}
            >
              {syncState === 'idle' && 'Sync Taste DNA'}
              {syncState === 'syncing' && 'Syncing…'}
              {syncState === 'complete' && 'Profile Synced'}
            </button>
          </section>

          <section ref={signatureRef}>
            <div className="section-heading">Signature Collection</div>
            <div className="menu-grid">
              {signatureItems.map((item) => (
                <div
                  key={item.id}
                  className={`menu-card ${selectedItem?.id === item.id ? 'selected' : ''}`}
                  onClick={() => handleOpenModal(item)}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(event) => event.key === 'Enter' && handleOpenModal(item)}
                >
                  <div className="glyph">{getInitial(item.name)}</div>
                  <h4>{item.name}</h4>
                  <div className="price">${item.price.toFixed(2)}</div>
                  {item.tag ? <span className="tag">{item.tag}</span> : null}
                </div>
              ))}
            </div>
          </section>

          <section ref={fusionRef}>
            <div className="section-heading">Matcha Fusion Lab</div>
            <div className="menu-grid">
              {fusionItems.map((item) => (
                <div
                  key={item.id}
                  className={`menu-card ${selectedItem?.id === item.id ? 'selected' : ''}`}
                  onClick={() => handleOpenModal(item)}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(event) => event.key === 'Enter' && handleOpenModal(item)}
                >
                  <div className="glyph">{getInitial(item.name)}</div>
                  <h4>{item.name}</h4>
                  <div className="price">${item.price.toFixed(2)}</div>
                  {item.tag ? <span className="tag">{item.tag}</span> : null}
                </div>
              ))}
            </div>
          </section>
        </main>

        <footer className="console-footer">
          <div className="cart-bar">
            <div className="cart-meta">
              <div className="cart-count">{cartSummary.count}</div>
              <div>
                <strong
                  className="section-heading"
                  style={{ marginBottom: 6, letterSpacing: '0.18em', fontSize: 11 }}
                >
                  CURRENT ORDER QUEUE
                </strong>
                <p style={{ color: 'var(--text-soft)', fontSize: 13 }}>Live drink synthesis · 2 min average</p>
              </div>
              <span className="cart-total">${cartSummary.total.toFixed(2)}</span>
            </div>
            <button className="checkout" type="button" onClick={handleCheckout} disabled={!cartSummary.count}>
              Authorize Brew
            </button>
          </div>
        </footer>
      </div>

      <div className={`modal ${modalOpen ? 'active' : ''}`}>
        <div className="modal-card" role="dialog" aria-modal="true" aria-hidden={!modalOpen}>
          <div className="modal-header">
            <h2>Customize Drink Protocol</h2>
            <button type="button" className="close-btn" onClick={handleCloseModal}>
              &times;
            </button>
          </div>

          {selectedItem && customization && (
            <>
              <div className="drink-focus">
                <div className="glyph">{getInitial(selectedItem.name)}</div>
                <div style={{ fontSize: '1.4rem', fontWeight: 600, letterSpacing: '0.08em' }}>{selectedItem.name}</div>
                <div className="price">${selectedItem.price.toFixed(2)}</div>
              </div>

              <div className="options">
                <div className="option-group">
                  <h5>Size Vector</h5>
                  <div className="chip-group">
                    {sizeOptions.map((option) => (
                      <button
                        key={option.value}
                        type="button"
                        className={`chip-option ${
                          customization.size.value === option.value ? 'active' : ''
                        }`}
                        onClick={() =>
                          setCustomization((prev) => (prev ? { ...prev, size: option } : prev))
                        }
                      >
                        {option.label}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="option-group">
                  <h5>Thermal Profile</h5>
                  <div className="chip-group">
                    {iceOptions.map((option) => (
                      <button
                        key={option}
                        type="button"
                        className={`chip-option ${customization.ice === option ? 'active' : ''}`}
                        onClick={() =>
                          setCustomization((prev) => (prev ? { ...prev, ice: option } : prev))
                        }
                      >
                        {option}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="option-group">
                  <h5>Sweetness</h5>
                  <div className="chip-group">
                    {sweetnessOptions.map((option) => (
                      <button
                        key={option}
                        type="button"
                        className={`chip-option ${customization.sweetness === option ? 'active' : ''}`}
                        onClick={() =>
                          setCustomization((prev) => (prev ? { ...prev, sweetness: option } : prev))
                        }
                      >
                        {option}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="option-group">
                  <h5>Add-ons</h5>
                  <div className="chip-group">
                    {addonOptions.map((option) => {
                      const active = customization.addons.some((addon) => addon.value === option.value);
                      return (
                        <button
                          key={option.value}
                          type="button"
                          className={`chip-option ${active ? 'active' : ''}`}
                          onClick={() => toggleAddon(option)}
                        >
                          {option.label}
                        </button>
                      );
                    })}
                  </div>
                </div>

                <div className="option-group">
                  <h5>Milk Matrix</h5>
                  <div className="chip-group">
                    {milkOptions.map((option) => (
                      <button
                        key={option.value}
                        type="button"
                        className={`chip-option ${customization.milk.value === option.value ? 'active' : ''}`}
                        onClick={() =>
                          setCustomization((prev) => (prev ? { ...prev, milk: option } : prev))
                        }
                      >
                        {option.label}
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              <div className="quantity">
                <button
                  type="button"
                  className="qty-button"
                  onClick={() =>
                    setCustomization((prev) =>
                      prev ? { ...prev, quantity: Math.max(1, prev.quantity - 1) } : prev,
                    )
                  }
                >
                  −
                </button>
                <span>{customization.quantity}</span>
                <button
                  type="button"
                  className="qty-button"
                  onClick={() =>
                    setCustomization((prev) => (prev ? { ...prev, quantity: prev.quantity + 1 } : prev))
                  }
                >
                  +
                </button>
              </div>

              <button type="button" className="confirm-btn" onClick={handleConfirm}>
                Deploy to Cart · <span>${modalTotal.toFixed(2)}</span>
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

