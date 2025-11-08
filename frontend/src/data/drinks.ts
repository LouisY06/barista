import { Drink } from '../types';

export const drinks: Drink[] = [
  // In Season
  {
    id: '1',
    name: 'Strawberry Matcha Latte',
    price: 6.50,
    category: 'In Season',
    tags: ['cold', 'popular'],
    ingredients: ['Matcha powder', 'Fresh strawberries', 'Milk', 'Honey', 'Ice'],
    image: 'matcha drink'
  },
  {
    id: '2',
    name: 'Peach Oolong Tea',
    price: 5.75,
    category: 'In Season',
    tags: ['cold', 'hot', 'caffeinated'],
    ingredients: ['Oolong tea', 'Fresh peaches', 'Honey', 'Ice'],
    image: 'peach tea'
  },
  {
    id: '3',
    name: 'Mango Coconut Smoothie',
    price: 6.25,
    category: 'In Season',
    tags: ['cold', 'popular'],
    ingredients: ['Fresh mango', 'Coconut milk', 'Honey', 'Ice', 'Tapioca pearls'],
    image: 'mango smoothie'
  },
  
  // Milk Tea
  {
    id: '4',
    name: 'Classic Bubble Milk Tea',
    price: 5.50,
    category: 'Milk Tea',
    tags: ['cold', 'hot', 'popular', 'caffeinated'],
    ingredients: ['Black tea', 'Milk', 'Tapioca pearls', 'Sugar syrup'],
    image: 'bubble tea'
  },
  {
    id: '5',
    name: 'Brown Sugar Milk Tea',
    price: 6.00,
    category: 'Milk Tea',
    tags: ['cold', 'popular'],
    ingredients: ['Black tea', 'Fresh milk', 'Brown sugar syrup', 'Tapioca pearls'],
    image: 'brown sugar tea'
  },
  {
    id: '6',
    name: 'Taro Milk Tea',
    price: 5.75,
    category: 'Milk Tea',
    tags: ['cold', 'hot'],
    ingredients: ['Taro powder', 'Milk', 'Tapioca pearls', 'Sugar'],
    image: 'taro tea'
  },
  {
    id: '7',
    name: 'Matcha Milk Tea',
    price: 6.25,
    category: 'Milk Tea',
    tags: ['cold', 'hot', 'caffeinated'],
    ingredients: ['Matcha powder', 'Milk', 'Honey', 'Tapioca pearls'],
    image: 'matcha milk tea'
  },
  
  // Fruit Tea
  {
    id: '8',
    name: 'Passion Fruit Green Tea',
    price: 5.50,
    category: 'Fruit Tea',
    tags: ['cold', 'caffeinated'],
    ingredients: ['Green tea', 'Passion fruit', 'Honey', 'Ice'],
    image: 'passion fruit tea'
  },
  {
    id: '9',
    name: 'Lychee Rose Tea',
    price: 5.75,
    category: 'Fruit Tea',
    tags: ['cold', 'popular'],
    ingredients: ['Black tea', 'Lychee', 'Rose syrup', 'Ice'],
    image: 'lychee tea'
  },
  {
    id: '10',
    name: 'Grapefruit Jasmine Tea',
    price: 6.00,
    category: 'Fruit Tea',
    tags: ['cold', 'caffeinated'],
    ingredients: ['Jasmine tea', 'Fresh grapefruit', 'Honey', 'Ice'],
    image: 'grapefruit tea'
  },
  
  // Hot Drinks
  {
    id: '11',
    name: 'Hong Kong Milk Tea',
    price: 5.00,
    category: 'Hot Drinks',
    tags: ['hot', 'popular', 'caffeinated'],
    ingredients: ['Ceylon tea', 'Evaporated milk', 'Condensed milk'],
    image: 'hong kong tea'
  },
  {
    id: '12',
    name: 'Honey Ginger Tea',
    price: 4.75,
    category: 'Hot Drinks',
    tags: ['hot'],
    ingredients: ['Fresh ginger', 'Honey', 'Lemon', 'Hot water'],
    image: 'ginger tea'
  },
  {
    id: '13',
    name: 'Caramel Latte',
    price: 5.50,
    category: 'Hot Drinks',
    tags: ['hot', 'caffeinated'],
    ingredients: ['Espresso', 'Milk', 'Caramel syrup'],
    image: 'caramel latte'
  },
  
  // Specialty
  {
    id: '14',
    name: 'Cheese Foam Oolong',
    price: 6.50,
    category: 'Specialty',
    tags: ['cold', 'popular', 'caffeinated'],
    ingredients: ['Oolong tea', 'Cream cheese foam', 'Sea salt', 'Ice'],
    image: 'cheese foam tea'
  },
  {
    id: '15',
    name: 'Boba Smoothie Bowl',
    price: 7.50,
    category: 'Specialty',
    tags: ['cold'],
    ingredients: ['Açai', 'Banana', 'Mango', 'Tapioca pearls', 'Granola', 'Fresh berries'],
    image: 'smoothie bowl'
  },
];
