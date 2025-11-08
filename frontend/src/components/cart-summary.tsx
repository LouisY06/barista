import { CartItem } from '../types';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Separator } from './ui/separator';
import { ScrollArea } from './ui/scroll-area';
import { ShoppingCart, Trash2 } from 'lucide-react';

interface CartSummaryProps {
  items: CartItem[];
  onRemoveItem: (index: number) => void;
  onCheckout: () => void;
}

export function CartSummary({ items, onRemoveItem, onCheckout }: CartSummaryProps) {
  const subtotal = items.reduce((sum, item) => sum + item.price, 0);
  const tax = subtotal * 0.08; // 8% tax
  const total = subtotal + tax;

  return (
    <Card className="p-6 sticky top-6">
      <div className="flex items-center gap-2 mb-4">
        <ShoppingCart className="w-5 h-5" />
        <h2>Cart ({items.length})</h2>
      </div>

      {items.length === 0 ? (
        <p className="text-gray-500 text-center py-8">Your cart is empty</p>
      ) : (
        <>
          <ScrollArea className="h-[400px] pr-4">
            <div className="space-y-4">
              {items.map((item, index) => (
                <div key={index} className="space-y-2">
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <p>{item.drink.name}</p>
                      <p className="text-sm text-gray-500">
                        {item.size} · {item.sugar}% sugar · {item.ice}% ice
                      </p>
                      <p className="text-sm text-gray-500">Qty: {item.quantity}</p>
                    </div>
                    <div className="flex items-start gap-2">
                      <span>${item.price.toFixed(2)}</span>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-6 w-6"
                        onClick={() => onRemoveItem(index)}
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                  {index < items.length - 1 && <Separator />}
                </div>
              ))}
            </div>
          </ScrollArea>

          <Separator className="my-4" />

          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span>Subtotal</span>
              <span>${subtotal.toFixed(2)}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span>Tax (8%)</span>
              <span>${tax.toFixed(2)}</span>
            </div>
            <Separator />
            <div className="flex justify-between">
              <span>Total</span>
              <span>${total.toFixed(2)}</span>
            </div>
          </div>

          <Button className="w-full mt-4" size="lg" onClick={onCheckout}>
            Checkout
          </Button>
        </>
      )}
    </Card>
  );
}
