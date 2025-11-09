import { useNavigate } from 'react-router-dom';
import { GlassButton } from '../components/GlassButton';
import { InteractiveWave } from '../components/InteractiveWave';
import { TextWave } from '../components/TextWave';
import { RoboticArm } from '../components/RoboticArm';
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
        <TextWave text="Drinks crafted with robotic exactness." />
        <p>
          CAF-E blends ceremonial tradition with computer vision and robotics to deliver precision-crafted beverages—hot or cold—
          every single time.
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

      <section className="arm-showcase">
        <div className="arm-copy">
          <span className="arm-kicker">Autonomous Arm</span>
          <h2>Calibrated by Sensors, Guided by Ritual</h2>
          <GlassButton onClick={() => navigate('/order')} icon={<span>▶</span>}>
            Watch the sequence
          </GlassButton>
        </div>
        <div className="arm-visual">
          <RoboticArm />
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
          <h2>Rewards That Earn Points</h2>
          <p>Earn points every visit and redeem for matcha upgrades, complimentary pours, and seasonal releases.</p>
        </div>
      </section>
    </div>
  );
}
