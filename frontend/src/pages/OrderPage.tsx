import { useMemo, useState } from 'react';
import { StackedMatchaCards } from '../components/StackedMatchaCards';
import '../styles/order.css';

const MILK_OPTIONS = [
  { id: 'whole', name: 'Whole Milk', subtitle: 'Classic ceremonial pairing', price: 7.5 },
  { id: 'skim', name: 'Skim Milk', subtitle: 'Lighter texture, crisp finish', price: 7.25 },
  { id: 'oat', name: 'Oat Milk', subtitle: 'Velvety, toasted oat notes', price: 7.9 },
  { id: 'almond', name: 'Almond Milk', subtitle: 'Delicate nut sweetness', price: 7.9 },
];

const LEVELS = [0.2, 0.4, 0.6, 0.8, 1];

export function OrderPage() {
  const [selectedMilk, setSelectedMilk] = useState(MILK_OPTIONS[0]);
  const [level, setLevel] = useState<number>(LEVELS[3]);
  const [temperature, setTemperature] = useState<'Hot' | 'Cold'>('Hot');
  const [favorite, setFavorite] = useState(false);
  const [cartCount, setCartCount] = useState(0);

  const priceLabel = useMemo(() => `$${selectedMilk.price.toFixed(2)}`, [selectedMilk]);
  const showcaseClass = `matcha-showcase ${temperature === 'Hot' ? 'hot-mode' : 'cold-mode'}`;

  return (
    <div className={showcaseClass}>
      <section className="product-card single">
        <div className="product-media">
          <StackedMatchaCards temperature={temperature} />
        </div>

        <div className="product-details">
          <header>
            <div>
              <h1>{temperature} matcha latte</h1>
              <p>Shade-grown matcha whisked with your choice of milk.</p>
            </div>
            <span className="price-tag">{priceLabel}</span>
          </header>

          <div className="origin-selector">
            <p className="label">Milk Selection</p>
            <div className="origin-pills">
              {MILK_OPTIONS.map((option) => (
                <button
                  key={option.id}
                  type="button"
                  className={`origin-pill ${option.id === selectedMilk.id ? 'active' : ''}`}
                  onClick={() => setSelectedMilk(option)}
                >
                  <span>{option.name}</span>
                </button>
              ))}
            </div>
            <p className="origin-description">{selectedMilk.subtitle}</p>
          </div>

          <div className="origin-selector">
            <p className="label">Serve</p>
            <div className="origin-pills">
              {(['Hot', 'Cold'] as const).map((value) => (
                <button
                  key={value}
                  type="button"
                  className={`origin-pill ${temperature === value ? 'active' : ''}`}
                  onClick={() => setTemperature(value)}
                >
                  <span>{value}</span>
                </button>
              ))}
            </div>
          </div>

          <div className="level-control">
            <p className="label">Matcha level</p>
            <div className="level-bars">
              {LEVELS.map((value) => (
                <button
                  key={value}
                  type="button"
                  className={`level-bar ${value <= level ? 'filled' : ''}`}
                  onClick={() => setLevel(value)}
                  aria-label={`Select matcha intensity ${Math.round(value * 100)}%`}
                />
              ))}
            </div>
            <p className="level-text">Intensity {Math.round(level * 100)}%</p>
          </div>

          <footer className="product-actions">
            <button
              type="button"
              className="primary-cta"
              onClick={() => setCartCount((prev) => prev + 1)}
            >
              Add Item
            </button>
            <button
              type="button"
              className={`favorite-toggle ${favorite ? 'active' : ''}`}
              onClick={() => setFavorite((prev) => !prev)}
              aria-pressed={favorite}
            >
              {favorite ? 'Saved' : 'Save'}
            </button>
          </footer>
        </div>
      </section>

      {cartCount > 0 && (
        <button type="button" className="floating-cart" aria-label={`Open cart, ${cartCount} items`}>
          <span className="cart-icon-mini" aria-hidden>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M7 7h10l1 12H6L7 7Z" />
              <path d="M9 7a3 3 0 0 1 6 0" />
            </svg>
          </span>
          <span className="cart-label">Cart</span>
          <span className="cart-count-pill">{cartCount}</span>
        </button>
      )}
    </div>
  );
}

