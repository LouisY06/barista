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
