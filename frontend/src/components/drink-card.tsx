import { Drink } from '../types';
import { Badge } from './ui/badge';
import { Card } from './ui/card';
import { ImageWithFallback } from './figma/ImageWithFallback';
import { Flame, Snowflake, TrendingUp, Coffee } from 'lucide-react';

interface DrinkCardProps {
  drink: Drink;
  onClick: () => void;
}

export function DrinkCard({ drink, onClick }: DrinkCardProps) {
  const getTagIcon = (tag: string) => {
    switch (tag) {
      case 'hot':
        return <Flame className="w-3 h-3" />;
      case 'cold':
        return <Snowflake className="w-3 h-3" />;
      case 'popular':
        return <TrendingUp className="w-3 h-3" />;
      case 'caffeinated':
        return <Coffee className="w-3 h-3" />;
      default:
        return null;
    }
  };

  const getTagVariant = (tag: string) => {
    switch (tag) {
      case 'hot':
        return 'destructive';
      case 'cold':
        return 'default';
      case 'popular':
        return 'secondary';
      case 'caffeinated':
        return 'outline';
      default:
        return 'default';
    }
  };

  return (
    <Card
      className="overflow-hidden cursor-pointer hover:shadow-lg transition-shadow"
      onClick={onClick}
    >
      <div className="aspect-square relative">
        <ImageWithFallback
          src={`https://images.unsplash.com/photo-1670468642364-6cacadfb7bb0?w=400`}
          alt={drink.name}
          className="w-full h-full object-cover"
        />
      </div>
      <div className="p-4">
        <div className="flex justify-between items-start mb-2">
          <h3 className="flex-1">{drink.name}</h3>
          <span className="text-amber-600 ml-2">${drink.price.toFixed(2)}</span>
        </div>
        <div className="flex flex-wrap gap-1">
          {drink.tags.map((tag) => (
            <Badge
              key={tag}
              variant={getTagVariant(tag)}
              className="text-xs flex items-center gap-1"
            >
              {getTagIcon(tag)}
              {tag}
            </Badge>
          ))}
        </div>
      </div>
    </Card>
  );
}
