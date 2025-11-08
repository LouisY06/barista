import { motion } from 'framer-motion';
import '../styles/stacked-cards.css';

type RewardCardProps = {
  title: string;
  description: string;
  points: number;
  index: number;
  claimed?: boolean;
  onClaim?: () => void;
};

const palette = [
  {
    badge: 'Initiate',
    hues: {
      primary:
        'linear-gradient(180deg, rgba(255,255,255,0.94) 0%, rgba(223,243,207,0.96) 48%, rgba(202,229,185,0.95) 100%)',
      secondary: 'rgba(172, 214, 164, 0.52)',
      tertiary: 'rgba(148, 199, 146, 0.32)',
      accent: 'rgba(16, 124, 67, 0.65)',
    },
  },
  {
    badge: 'Practitioner',
    hues: {
      primary:
        'linear-gradient(180deg, rgba(255,255,255,0.94) 0%, rgba(212,238,227,0.96) 48%, rgba(188,226,214,0.95) 100%)',
      secondary: 'rgba(120, 202, 173, 0.52)',
      tertiary: 'rgba(93, 187, 158, 0.28)',
      accent: 'rgba(0, 120, 98, 0.7)',
    },
  },
  {
    badge: 'Ceremonial',
    hues: {
      primary:
        'linear-gradient(180deg, rgba(255,255,255,0.95) 0%, rgba(211,233,252,0.97) 48%, rgba(186,221,246,0.96) 100%)',
      secondary: 'rgba(120, 180, 226, 0.52)',
      tertiary: 'rgba(94, 156, 207, 0.28)',
      accent: 'rgba(47, 120, 201, 0.7)',
    },
  },
];

const layers = [
  { id: 'primary', rotate: -2.8, scale: 0.92, y: 36, z: -22, opacity: 0.7 },
  { id: 'secondary', rotate: 5, scale: 0.96, y: 18, z: -8, opacity: 0.85 },
  { id: 'foreground', rotate: -1.2, scale: 1, y: 0, z: 12, opacity: 1 },
];

export function StackedRewardCard({ title, description, points, index, claimed = false, onClaim }: RewardCardProps) {
  const paletteIndex = index % palette.length;
  const colors = palette[paletteIndex].hues;
  const badge = palette[paletteIndex].badge;

  return (
    <motion.div
      className={`stacked-reward-card${claimed ? ' claimed' : ''}`}
      animate={{
        opacity: claimed ? 0.55 : 1,
        filter: claimed ? 'grayscale(0.45)' : 'none',
        scale: 1,
      }}
      whileHover={claimed ? undefined : { y: -6 }}
      transition={{ type: 'spring', stiffness: 180, damping: 18 }}
    >
      {layers.map((layer, layerIndex) => {
        const isForeground = layer.id === 'foreground';
        const background =
          layerIndex === 0 ? colors.tertiary : layerIndex === 1 ? colors.secondary : colors.primary;

        return (
          <motion.article
            key={layer.id}
            className={`reward-stack-layer ${layer.id}`}
            initial={{ opacity: 0, scale: layer.scale * 0.9, y: layer.y + 12 }}
            animate={{
              opacity: layer.opacity,
              scale: layer.scale,
              rotate: layer.rotate,
              y: layer.y,
              z: layer.z,
            }}
            transition={{ type: 'spring', stiffness: 130, damping: 20, delay: layerIndex * 0.05 }}
            style={{ background }}
            whileHover={claimed || !isForeground ? undefined : { rotate: layer.rotate + 1.6, y: layer.y - 4 }}
          >
            <div className="reward-layer-frost" />
            {isForeground && (
              <div className="reward-layer-content">
                <span className="reward-badge">{claimed ? 'Redeemed' : badge}</span>
                <h3>{title}</h3>
                <p>{description}</p>
                <div className="reward-points-row">
                  <span className="reward-points-highlight">{points} pts</span>
                  <motion.button
                    type="button"
                    className="reward-cta"
                    whileTap={claimed ? undefined : { scale: 0.94 }}
                    onClick={() => {
                      if (claimed) return;
                      onClaim?.();
                    }}
                    disabled={claimed}
                    aria-pressed={claimed}
                  >
                    {claimed ? 'Claimed' : 'Claim'}
                  </motion.button>
                </div>
                <span className="reward-accent" style={{ background: colors.accent }} />
              </div>
            )}
          </motion.article>
        );
      })}
    </motion.div>
  );
}

