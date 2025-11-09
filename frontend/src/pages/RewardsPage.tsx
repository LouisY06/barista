import { useState } from 'react';
import { StackedRewardCard } from '../components/StackedRewardCard';
import '../styles/rewards.css';

const GOAL = 1300;

const REWARDS = [
  {
    id: '5-off',
    title: '5% Off Your Next Cup',
    description: 'A small nod of appreciation for a steady ritual.',
    points: 120,
  },
  {
    id: 'premium-topping',
    title: 'Add a Premium Topping',
    description: 'Customize your calm — complimentary.',
    points: 250,
  },
  {
    id: 'size-upgrade',
    title: 'Free Size or Milk Upgrade',
    description: 'Precision in every pour, now a little more.',
    points: 400,
  },
  {
    id: 'signature-drink',
    title: '20% Off Signature Drink',
    description: 'A crafted reward for returning patrons.',
    points: 650,
  },
  {
    id: 'complimentary-latte',
    title: 'Complimentary Matcha Latte',
    description: 'A calm break — on the house.',
    points: 900,
  },
  {
    id: 'ceremonial-limited',
    title: 'Ceremonial Limited Drink',
    description: 'Celebrate balance and craft with something rare.',
    points: 1300,
  },
];

const TIERS = [
  { id: 'initiate', label: 'Initiate', range: '0 – 300 pts', description: 'New to the ritual.' },
  { id: 'practitioner', label: 'Practitioner', range: '301 – 700 pts', description: 'Steady hand, perfect pour.' },
  { id: 'ceremonial', label: 'Ceremonial Member', range: '701+ pts', description: 'Master of the matcha ritual.' },
];

type RewardsPageProps = {
  loyaltyBalance: number;
};

export function RewardsPage({ loyaltyBalance }: RewardsPageProps) {
  const progress = Math.min(loyaltyBalance / GOAL, 1);
  const [claimedRewards, setClaimedRewards] = useState<string[]>([]);

  const handleClaim = (id: string) => {
    setClaimedRewards((prev) => (prev.includes(id) ? prev : [...prev, id]));
  };

  return (
    <div className="rewards-page">
      <header className="rewards-hero">
        <div className="hero-text">
          <p className="hero-kicker">CAF-E Rewards</p>
          <h1>Every cup earns a moment.</h1>
          <p>
            Matcha-based rewards crafted for calm, ritual, and precision. Earn points with every pour — redeem them for
            rare, thoughtful experiences.
          </p>
        </div>
        <div className="balance-panel">
          <div className="balance-header">
            <span className="balance-label">Available Balance</span>
            <strong className="balance-value">{loyaltyBalance} Points</strong>
          </div>
          <div className="progress-track" aria-hidden>
            <div className="progress-fill" style={{ width: `${progress * 100}%` }} />
          </div>
          <span className="progress-caption">
            {loyaltyBalance} / {GOAL} toward Ceremonial Limited Drink
          </span>
        </div>
      </header>

      <section className="tiers-section">
        <h2>Journey through the ritual</h2>
        <div className="tiers-grid">
          {TIERS.map((tier) => (
            <article key={tier.id} className="tier-card">
              <div className="tier-body">
                <strong>{tier.label}</strong>
                <span>{tier.range}</span>
                <p>{tier.description}</p>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="rewards-section">
        <h2>Available rewards</h2>
        <div className="rewards-grid">
          {REWARDS.map((reward, index) => (
            <StackedRewardCard
              key={reward.id}
              title={reward.title}
              description={reward.description}
              points={reward.points}
              index={index}
              claimed={claimedRewards.includes(reward.id)}
              onClaim={() => handleClaim(reward.id)}
            />
          ))}
        </div>
      </section>

      <footer className="rewards-footer">Each cup brewed. Each moment rewarded.</footer>
    </div>
  );
}

