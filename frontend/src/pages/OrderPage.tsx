import { useEffect, useMemo, useState } from 'react';
import { drinks } from '../data/drinks';
import type { CartLineItem, Drink, DrinkCategory } from '../types';
import '../styles/order.css';

const MILK_OPTIONS = [
  { id: 'whole', name: 'Whole Milk', subtitle: 'Classic ceremonial pairing', delta: 0 },
  { id: 'skim', name: 'Skim Milk', subtitle: 'Lighter texture, crisp finish', delta: -0.25 },
  { id: 'oat', name: 'Oat Milk', subtitle: 'Velvety, toasted oat notes', delta: 0.4 },
  { id: 'almond', name: 'Almond Milk', subtitle: 'Delicate nut sweetness', delta: 0.4 },
];

const LEVELS = [0.2, 0.4, 0.6, 0.8, 1];

type Temperature = 'Hot' | 'Cold';

type OrderPageProps = {
  cartCount: number;
  onAddToCart: (item: CartLineItem) => void;
  onOpenCart: () => void;
};

const FALLBACK_IMAGE =
  'https://images.unsplash.com/photo-1670468642364-6cacadfb7bb0?w=1200&auto=format&fit=crop&sat=-20';

const getAvailableTemperatures = (drink?: Drink): Temperature[] => {
  if (!drink) return ['Hot'];
  const hot = drink.tags.includes('hot');
  const cold = drink.tags.includes('cold');
  if (hot && cold) return ['Hot', 'Cold'];
  if (hot) return ['Hot'];
  if (cold) return ['Cold'];
  return ['Hot'];
};

export function OrderPage({ cartCount, onAddToCart, onOpenCart }: OrderPageProps) {
  const [selectedCategory, setSelectedCategory] = useState<DrinkCategory | 'All'>('All');
  const [selectedDrinkId, setSelectedDrinkId] = useState<string>(drinks[0]?.id ?? '');
  const [selectedMilk, setSelectedMilk] = useState(MILK_OPTIONS[0]);
  const [level, setLevel] = useState<number>(LEVELS[3]);
  const [temperature, setTemperature] = useState<Temperature>('Hot');
  const [favorite, setFavorite] = useState(false);

  const categories = useMemo<(DrinkCategory | 'All')[]>(() => {
    const unique = Array.from(new Set(drinks.map((drink) => drink.category))) as DrinkCategory[];
    return ['All', ...unique];
  }, []);

  const filteredDrinks = useMemo(() => {
    if (selectedCategory === 'All') return drinks;
    return drinks.filter((drink) => drink.category === selectedCategory);
  }, [selectedCategory]);

  useEffect(() => {
    if (!filteredDrinks.length) return;
    const exists = filteredDrinks.some((drink) => drink.id === selectedDrinkId);
    if (!exists) {
      setSelectedDrinkId(filteredDrinks[0].id);
    }
  }, [filteredDrinks, selectedDrinkId]);

  const selectedDrink: Drink | undefined = useMemo(
    () => filteredDrinks.find((drink) => drink.id === selectedDrinkId) ?? filteredDrinks[0],
    [filteredDrinks, selectedDrinkId]
  );

  const availableTemperatures = useMemo(
    () => getAvailableTemperatures(selectedDrink),
    [selectedDrink]
  );

  useEffect(() => {
    if (!selectedDrink) return;
    setSelectedMilk(MILK_OPTIONS[0]);
    setLevel(LEVELS[3]);
    setFavorite(false);
  }, [selectedDrink]);

  useEffect(() => {
    if (!availableTemperatures.length) return;
    setTemperature((prev) =>
      availableTemperatures.includes(prev) ? prev : availableTemperatures[0]
    );
  }, [availableTemperatures]);

  const computedPrice = useMemo(() => {
    if (!selectedDrink) return 0;
    return selectedDrink.price + selectedMilk.delta;
  }, [selectedDrink, selectedMilk]);

  const intensityPercent = useMemo(() => Math.round(level * 100), [level]);
  const priceLabel = useMemo(() => `$${computedPrice.toFixed(2)}`, [computedPrice]);

  const intensityConfig = useMemo(() => {
    if (!selectedDrink) {
      return {
        label: 'Matcha Level',
        className: 'matcha',
        prefix: 'Matcha intensity',
      } as const;
    }

    const name = selectedDrink.name.toLowerCase();
    const ingredientsText = selectedDrink.ingredients.map((item) => item.toLowerCase()).join(' ');

    const hasMatcha = name.includes('matcha') || ingredientsText.includes('matcha');
    if (hasMatcha) {
      return {
        label: 'Matcha Level',
        className: 'matcha',
        prefix: 'Matcha intensity',
      } as const;
    }

    const teaKeywords = ['tea', 'oolong', 'jasmine', 'ceylon', 'sencha', 'assam', 'earl grey'];
    const hasTea = teaKeywords.some(
      (keyword) => name.includes(keyword) || ingredientsText.includes(keyword)
    );
    if (hasTea) {
      return {
        label: 'Tea Intensity',
        className: 'tea',
        prefix: 'Tea intensity',
      } as const;
    }

    const milkKeywords = ['milk', 'cream', 'latte', 'foam', 'cheese'];
    const hasMilk = milkKeywords.some(
      (keyword) => name.includes(keyword) || ingredientsText.includes(keyword)
    );
    if (!hasMilk) {
      return {
        label: 'Syrup Intensity',
        className: 'syrup',
        prefix: 'Syrup intensity',
      } as const;
    }

    return {
      label: 'Sweetness Intensity',
      className: 'sweet',
      prefix: 'Sweetness',
    } as const;
  }, [selectedDrink]);

  const showcaseClass = `matcha-showcase ${temperature === 'Hot' ? 'hot-mode' : 'cold-mode'}`;

  const handleAddToCart = () => {
    if (!selectedDrink) return;

    const cartItem: CartLineItem = {
      id: `${selectedDrink.id}-${Date.now()}`,
      drinkId: selectedDrink.id,
      name: selectedDrink.name,
      milk: selectedMilk.name,
      temperature,
      intensity: intensityPercent,
      price: Number(computedPrice.toFixed(2)),
    };

    onAddToCart(cartItem);
  };

  return (
    <div className={showcaseClass}>
      <aside className="order-category-column">
        <span className="order-column-title">Categories</span>
        <div className="order-category-list">
          {categories.map((category) => {
            const active = category === selectedCategory;
            return (
              <button
                key={category}
                type="button"
                className={`order-category-button ${active ? 'active' : ''}`}
                onClick={() => setSelectedCategory(category)}
              >
                {category}
              </button>
            );
          })}
        </div>
      </aside>

      <section className="order-menu-column">
        <header className="order-menu-header">
          <div>
            <span className="order-column-title">Menu</span>
            <h2>{selectedCategory === 'All' ? 'Select a signature pour' : selectedCategory}</h2>
          </div>
          <span className="order-menu-count">
            {filteredDrinks.length} item{filteredDrinks.length === 1 ? '' : 's'}
          </span>
        </header>

        <div className="order-menu-grid">
          {filteredDrinks.map((drink) => (
            <button
              key={drink.id}
              type="button"
              className={`order-menu-card ${drink.id === selectedDrinkId ? 'active' : ''}`}
              onClick={() => setSelectedDrinkId(drink.id)}
            >
              <div className="order-menu-card-body">
                <div className="order-menu-card-header">
                  <span className="order-menu-card-name">{drink.name}</span>
                  <span className="order-menu-card-price">${drink.price.toFixed(2)}</span>
                </div>
                <div className="order-menu-card-tags">
                  {drink.tags.map((tag) => (
                    <span key={tag}>{tag}</span>
                  ))}
                </div>
                <span className="order-menu-card-category">{drink.category}</span>
              </div>
            </button>
          ))}
        </div>
      </section>

      <aside className="order-detail-column">
        {selectedDrink ? (
          <>
            <div className="order-detail-image">
              <img
                src={selectedDrink.image || FALLBACK_IMAGE}
                alt={selectedDrink.name}
                onError={(event) => ((event.target as HTMLImageElement).src = FALLBACK_IMAGE)}
              />
            </div>

            <div className="order-detail-content">
              <div>
                <span className="order-detail-category">{selectedDrink.category}</span>
                <h2>{selectedDrink.name}</h2>
                <div className="order-detail-price">{priceLabel}</div>
              </div>

              <p className="order-detail-ingredients">{selectedDrink.ingredients.join(' · ')}</p>

              {availableTemperatures.length ? (
                <div className="order-detail-section">
                  <span className="label">Serve</span>
                  <div className="origin-pills">
                    {availableTemperatures.map((value) => (
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
              ) : null}

              <div className="order-detail-section">
                <span className="label">Milk Selection</span>
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

              <div className="order-detail-section">
                <span className="label">{intensityConfig.label}</span>
                <div className={`level-bars ${intensityConfig.className}`}>
                  {LEVELS.map((value) => (
                    <button
                      key={value}
                      type="button"
                      className={`level-bar ${value <= level ? 'filled' : ''}`}
                      onClick={() => setLevel(value)}
                      aria-label={`Select intensity ${Math.round(value * 100)}%`}
                    />
                  ))}
                </div>
                <p className={`level-text ${intensityConfig.className}`}>
                  {intensityConfig.prefix} {intensityPercent}%
                </p>
              </div>

              <footer className="product-actions">
                <button type="button" className="primary-cta" onClick={handleAddToCart}>
                  Add to Cart
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
          </>
        ) : (
          <div className="order-detail-empty">Select a drink to see more details.</div>
        )}
      </aside>

      {cartCount > 0 && (
        <button
          type="button"
          className="floating-cart"
          aria-label={`Open cart, ${cartCount} items`}
          onClick={onOpenCart}
        >
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

