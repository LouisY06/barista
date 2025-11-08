import { useNavigate } from 'react-router-dom';
import { GlassButton } from '../components/GlassButton';
import { InteractiveWave } from '../components/InteractiveWave';
import { TextWave } from '../components/TextWave';
import '../styles/landing.css';

export function LandingPage() {
  const navigate = useNavigate();

  return (
    <div className="landing-root">
      <div className="wave-wrapper">
        <InteractiveWave />
      </div>

      <section className="hero-section">
        <span className="hero-pill">Precision in Every Pour</span>
        <TextWave text="Matcha crafted with robotic exactness." />
        <p>
          MatchaBot blends ceremonial tradition with computer vision and robotics to deliver perfect matcha lattes—hot or
          cold—every single time.
        </p>
        <div className="hero-actions">
          <GlassButton onClick={() => navigate('/order')} icon={<span>→</span>}>
            Start Order
          </GlassButton>
          <button type="button" className="secondary-cta" onClick={() => navigate('/rewards')}>
            View Rewards
          </button>
        </div>
      </section>

      <section className="feature-section">
        <div>
          <h2>Robotic Precision</h2>
          <p>Every pour is calibrated by sensors, ensuring temperature, whisk speed, and sweetness are tuned to your profile.</p>
        </div>
        <div>
          <h2>Custom MIlks</h2>
          <p>Swap effortlessly between whole, skim, oat, or almond—each optimized for perfect emulsification.</p>
        </div>
        <div>
          <h2>Rewards That Spark</h2>
          <p>Earn sparks every visit and redeem for matcha upgrades, complimentary pours, and seasonal releases.</p>
        </div>
      </section>
    </div>
  );
}
