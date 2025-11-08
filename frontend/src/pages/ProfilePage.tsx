import '../styles/profile.css';

export function ProfilePage() {
  return (
    <div className="profile-root">
      <section className="profile-hero">
        <div className="profile-banner" />
        <div className="profile-top">
          <div>
            <h1>Hey, Alana Kwan</h1>
            <p>MatchaBot member since 2024 · Precision in Every Pour</p>
          </div>
          <button className="profile-qr" type="button" aria-label="Open membership QR">
            <span className="qr-dot" />
            <span className="qr-dot" />
            <span className="qr-dot" />
            <span className="qr-dot" />
          </button>
        </div>
        <div className="profile-stats">
          <div>
            <span className="stat-label">Coupons</span>
            <span className="stat-value">0</span>
          </div>
          <div>
            <span className="stat-label">Gift Cards</span>
            <span className="stat-value">0</span>
          </div>
          <div>
            <span className="stat-label">Sparks</span>
            <span className="stat-value">539</span>
          </div>
        </div>
      </section>

      <section className="profile-menu">
        <h2>Account</h2>
        <ul>
          <li>
            <button type="button">
              <span>My Orders</span>
              <span className="menu-meta">See all →</span>
            </button>
          </li>
          <li>
            <button type="button">
              <span>FAQ</span>
            </button>
          </li>
          <li>
            <button type="button">
              <span>Settings</span>
            </button>
          </li>
          <li>
            <button type="button">
              <span>Payment Methods</span>
            </button>
          </li>
          <li>
            <button type="button">
              <span>Feedback & Suggestions</span>
            </button>
          </li>
        </ul>
      </section>

      <section className="profile-menu">
        <h2>Membership</h2>
        <ul>
          <li>
            <button type="button">
              <span>Invite Friends</span>
              <span className="menu-meta">Earn Sparks</span>
            </button>
          </li>
          <li>
            <button type="button">
              <span>Redeem Rewards</span>
            </button>
          </li>
        </ul>
      </section>
    </div>
  );
}
