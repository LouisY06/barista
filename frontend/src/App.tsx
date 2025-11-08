import { useState } from 'react';
import { Drink, CartItem, DrinkCategory } from './types';
import { drinks } from './data/drinks';
import { DrinkCard } from './components/drink-card';
import { DrinkDetailDialog } from './components/drink-detail-dialog';
import { CartSummary } from './components/cart-summary';
import { Button } from './components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { toast } from 'sonner@2.0.3';
import { Toaster } from './components/ui/sonner';

const categories: DrinkCategory[] = ['In Season', 'Milk Tea', 'Fruit Tea', 'Hot Drinks', 'Specialty'];

export default function App() {
  const [selectedDrink, setSelectedDrink] = useState<Drink | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [cart, setCart] = useState<CartItem[]>([]);

  const handleDrinkClick = (drink: Drink) => {
    setSelectedDrink(drink);
    setDialogOpen(true);
  };

  const handleAddToCart = (item: CartItem) => {
    setCart([...cart, item]);
    toast.success(`Added ${item.drink.name} to cart!`);
  };

  const handleRemoveItem = (index: number) => {
    const newCart = cart.filter((_, i) => i !== index);
    setCart(newCart);
    toast.info('Item removed from cart');
  };

  const handleCheckout = () => {
    toast.success('Order placed successfully! Thank you!');
    setCart([]);
  };

  const getDrinksByCategory = (category: DrinkCategory) => {
    return drinks.filter((drink) => drink.category === category);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-pink-50">
      <Toaster />
      
      {/* Header */}
      <header className="bg-white shadow-sm border-b sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-purple-600">Bubble Bliss POS</h1>
              <p className="text-gray-600">Select your favorite drinks</p>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Drinks Selection */}
          <div className="lg:col-span-2">
            <Tabs defaultValue="In Season" className="w-full">
              <TabsList className="grid w-full grid-cols-5 mb-6">
                {categories.map((category) => (
                  <TabsTrigger key={category} value={category}>
                    {category}
                  </TabsTrigger>
                ))}
              </TabsList>

              {categories.map((category) => (
                <TabsContent key={category} value={category}>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {getDrinksByCategory(category).map((drink) => (
                      <DrinkCard
                        key={drink.id}
                        drink={drink}
                        onClick={() => handleDrinkClick(drink)}
                      />
                    ))}
                  </div>
                </TabsContent>
              ))}
            </Tabs>
          </div>

          {/* Cart */}
          <div className="lg:col-span-1">
            <CartSummary
              items={cart}
              onRemoveItem={handleRemoveItem}
              onCheckout={handleCheckout}
            />
          </div>
        </div>
      </div>

      {/* Drink Detail Dialog */}
      <DrinkDetailDialog
        drink={selectedDrink}
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        onAddToCart={handleAddToCart}
      />
    </div>
  );
}
