export interface Drink {
  id: string;
  name: string;
  price: number;
  category: string;
  tags: ('hot' | 'cold' | 'popular' | 'caffeinated')[];
  ingredients: string[];
  image: string;
}

export interface CartItem {
  drink: Drink;
  size: 'small' | 'medium' | 'large';
  sugar: number;
  ice: number;
  quantity: number;
  price: number;
}

export type DrinkCategory = 'In Season' | 'Milk Tea' | 'Fruit Tea' | 'Hot Drinks' | 'Specialty';

export type TemperaturePreference = 'Hot' | 'Cold';

export interface CartLineItem {
  id: string;
  drinkId: string;
  name: string;
  milk: string;
  temperature: TemperaturePreference;
  intensity: number;
  price: number;
  imageUrl?: string;
  notes?: string;
}

export interface KnotReceipt {
  id: string;
  sessionId: string;
  merchant: string;
  subtotal: number;
  items: CartLineItem[];
  createdAt: string;
  paymentStatus?: 'PENDING' | 'CONFIRMED' | 'FAILED' | 'CANCELLED';
  txId?: string;
  loyaltyDelta?: number;
  orderId?: string;
  currency?: string;
}

