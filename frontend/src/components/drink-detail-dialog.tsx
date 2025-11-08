import { useState } from 'react';
import { Drink, CartItem } from '../types';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from './ui/dialog';
import { Button } from './ui/button';
import { Label } from './ui/label';
import { RadioGroup, RadioGroupItem } from './ui/radio-group';
import { ImageWithFallback } from './figma/ImageWithFallback';
import { Minus, Plus } from 'lucide-react';

interface DrinkDetailDialogProps {
  drink: Drink | null;
  open: boolean;
  onClose: () => void;
  onAddToCart: (item: CartItem) => void;
}

export function DrinkDetailDialog({
  drink,
  open,
  onClose,
  onAddToCart,
}: DrinkDetailDialogProps) {
  const [size, setSize] = useState<'small' | 'medium' | 'large'>('medium');
  const [sugar, setSugar] = useState(100);
  const [ice, setIce] = useState(100);
  const [quantity, setQuantity] = useState(1);

  const sizeMultipliers = {
    small: 1,
    medium: 1.2,
    large: 1.4,
  };

  const calculatePrice = () => {
    if (!drink) return 0;
    return drink.price * sizeMultipliers[size] * quantity;
  };

  const handleAddToCart = () => {
    if (!drink) return;
    
    const cartItem: CartItem = {
      drink,
      size,
      sugar,
      ice,
      quantity,
      price: calculatePrice(),
    };
    
    onAddToCart(cartItem);
    handleClose();
  };

  const handleClose = () => {
    // Reset to defaults
    setSize('medium');
    setSugar(100);
    setIce(100);
    setQuantity(1);
    onClose();
  };

  if (!drink) return null;

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{drink.name}</DialogTitle>
          <DialogDescription>${drink.price.toFixed(2)}</DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* Image */}
          <div className="aspect-video relative rounded-lg overflow-hidden">
            <ImageWithFallback
              src={`https://images.unsplash.com/photo-1670468642364-6cacadfb7bb0?w=800`}
              alt={drink.name}
              className="w-full h-full object-cover"
            />
          </div>

          {/* Ingredients */}
          <div>
            <h4 className="mb-2">Ingredients</h4>
            <ul className="list-disc list-inside text-gray-600 space-y-1">
              {drink.ingredients.map((ingredient, index) => (
                <li key={index}>{ingredient}</li>
              ))}
            </ul>
          </div>

          {/* Cup Size */}
          <div>
            <Label className="mb-3 block">Cup Size</Label>
            <RadioGroup value={size} onValueChange={(v) => setSize(v as any)}>
              <div className="flex gap-4">
                <div className="flex items-center space-x-2">
                  <RadioGroupItem value="small" id="small" />
                  <Label htmlFor="small" className="cursor-pointer">
                    Small (+$0.00)
                  </Label>
                </div>
                <div className="flex items-center space-x-2">
                  <RadioGroupItem value="medium" id="medium" />
                  <Label htmlFor="medium" className="cursor-pointer">
                    Medium (+${((sizeMultipliers.medium - 1) * drink.price).toFixed(2)})
                  </Label>
                </div>
                <div className="flex items-center space-x-2">
                  <RadioGroupItem value="large" id="large" />
                  <Label htmlFor="large" className="cursor-pointer">
                    Large (+${((sizeMultipliers.large - 1) * drink.price).toFixed(2)})
                  </Label>
                </div>
              </div>
            </RadioGroup>
          </div>

          {/* Sugar Level */}
          <div>
            <Label className="mb-3 block">Sugar Level ({sugar}%)</Label>
            <div className="flex gap-2">
              {[0, 25, 50, 75, 100].map((level) => (
                <Button
                  key={level}
                  variant={sugar === level ? 'default' : 'outline'}
                  onClick={() => setSugar(level)}
                  className="flex-1"
                >
                  {level}%
                </Button>
              ))}
            </div>
          </div>

          {/* Ice Level */}
          <div>
            <Label className="mb-3 block">Ice Level ({ice}%)</Label>
            <div className="flex gap-2">
              {[0, 25, 50, 75, 100].map((level) => (
                <Button
                  key={level}
                  variant={ice === level ? 'default' : 'outline'}
                  onClick={() => setIce(level)}
                  className="flex-1"
                >
                  {level}%
                </Button>
              ))}
            </div>
          </div>

          {/* Quantity */}
          <div>
            <Label className="mb-3 block">Quantity</Label>
            <div className="flex items-center gap-4">
              <Button
                variant="outline"
                size="icon"
                onClick={() => setQuantity(Math.max(1, quantity - 1))}
                disabled={quantity <= 1}
              >
                <Minus className="w-4 h-4" />
              </Button>
              <span className="w-12 text-center">{quantity}</span>
              <Button
                variant="outline"
                size="icon"
                onClick={() => setQuantity(quantity + 1)}
              >
                <Plus className="w-4 h-4" />
              </Button>
            </div>
          </div>

          {/* Add to Cart Button */}
          <Button
            className="w-full"
            size="lg"
            onClick={handleAddToCart}
          >
            Add to Cart - ${calculatePrice().toFixed(2)}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
