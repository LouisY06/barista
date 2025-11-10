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

export interface CartLineItem {
  id: string;
  drinkId: string;
  name: string;
  milk: string;
  temperature: 'Hot' | 'Cold';
  intensity: number;
  price: number;
}

export interface KnotReceipt {
  id: string;
  sessionId: string;
  orderId?: string;
  merchant: string;
  subtotal: number;
  items: CartLineItem[];
  createdAt: string;
  currency?: string;
  txId?: string;
  paymentStatus?: 'PENDING' | 'CONFIRMED' | 'FAILED';
  loyaltyDelta?: number;
}