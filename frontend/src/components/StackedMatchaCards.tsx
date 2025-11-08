import { motion } from 'framer-motion';
import { useMemo } from 'react';
import '../styles/stacked-cards.css';

type Temperature = 'Hot' | 'Cold';

type CardLayer = {
  id: string;
  title: string;
  caption: string;
  accent: string;
  background: string;
  blurBackground: string;
  y: number;
  rotate: number;
  scale: number;
  z: number;
};

const stacks: Record<Temperature, CardLayer[]> = {
  Hot: [
    {
      id: 'steam',
      title: 'Ceremonial Steam',
      caption: 'microfoam 138°F',
      accent: 'rgba(173, 214, 146, 0.75)',
      background:
        'linear-gradient(180deg, rgba(255,255,255,0.94) 0%, rgba(223,243,207,0.96) 48%, rgba(202,229,185,0.95) 100%)',
      blurBackground: 'rgba(197, 226, 181, 0.6)',
      y: -4,
      rotate: -2.4,
      scale: 1,
      z: 40,
    },
    {
      id: 'whisk',
      title: 'Precise Whisk',
      caption: '3.2s bamboo cycle',
      accent: 'rgba(148, 199, 116, 0.55)',
      background:
        'linear-gradient(180deg, rgba(240,255,230,0.9) 0%, rgba(214,239,196,0.9) 100%)',
      blurBackground: 'rgba(186, 215, 160, 0.48)',
      y: 18,
      rotate: 4,
      scale: 0.96,
      z: 10,
    },
    {
      id: 'grind',
      title: 'Stone-Ground',
      caption: 'tencha grade A3',
      accent: 'rgba(118, 168, 92, 0.45)',
      background:
        'linear-gradient(180deg, rgba(230,242,222,0.85) 0%, rgba(205,227,197,0.85) 100%)',
      blurBackground: 'rgba(157, 204, 132, 0.42)',
      y: 38,
      rotate: -3.2,
      scale: 0.9,
      z: -20,
    },
  ],
  Cold: [
    {
      id: 'chill',
      title: 'Arctic Chill',
      caption: 'shaken over crystal ice',
      accent: 'rgba(162, 218, 205, 0.75)',
      background:
        'linear-gradient(180deg, rgba(255,255,255,0.92) 0%, rgba(206,239,230,0.95) 48%, rgba(188,229,222,0.96) 100%)',
      blurBackground: 'rgba(159, 214, 202, 0.62)',
      y: -2,
      rotate: 3.2,
      scale: 1,
      z: 40,
    },
    {
      id: 'cold-whisk',
      title: 'Cold Emulsion',
      caption: 'nitro-infused pour',
      accent: 'rgba(129, 196, 183, 0.52)',
      background:
        'linear-gradient(180deg, rgba(232, 251, 247, 0.92) 0%, rgba(198, 234, 226, 0.92) 100%)',
      blurBackground: 'rgba(143, 206, 194, 0.48)',
      y: 20,
      rotate: -4.8,
      scale: 0.95,
      z: 8,
    },
    {
      id: 'cascade',
      title: 'Cascade Finish',
      caption: 'matcha microfoam',
      accent: 'rgba(105, 177, 165, 0.44)',
      background:
        'linear-gradient(180deg, rgba(222, 242, 237, 0.85) 0%, rgba(187, 225, 219, 0.88) 100%)',
      blurBackground: 'rgba(118, 191, 179, 0.4)',
      y: 40,
      rotate: 2.6,
      scale: 0.88,
      z: -18,
    },
  ],
};

const transition = { type: 'spring', stiffness: 120, damping: 18 };

export function StackedMatchaCards({ temperature }: { temperature: Temperature }) {
  const layers = useMemo(() => stacks[temperature], [temperature]);

  return (
    <div className={`stacked-matcha-cards ${temperature.toLowerCase()}-mode`}>
      {layers.map((card, index) => (
        <motion.article
          key={card.id}
          className="stack-card"
          layout
          initial={{ opacity: 0, y: card.y + 12, scale: card.scale * 0.92 }}
          animate={{
            opacity: 1,
            y: card.y,
            rotate: card.rotate,
            scale: card.scale,
            z: card.z,
            boxShadow: `0 32px 80px rgba(16, 24, 40, ${0.08 + index * 0.04})`,
          }}
          transition={{ ...transition, delay: index * 0.05 }}
          style={{ background: card.background }}
        >
          <div className="stack-card__blur" style={{ background: card.blurBackground }} />
          <div className="stack-card__content">
            <span className="stack-card__tag">{temperature === 'Hot' ? 'Hot Ritual' : 'Iced Ritual'}</span>
            <h3>{card.title}</h3>
            <p>{card.caption}</p>
            <span className="stack-card__accent" style={{ background: card.accent }} />
          </div>
        </motion.article>
      ))}
    </div>
  );
}

