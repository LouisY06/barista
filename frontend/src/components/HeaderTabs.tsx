import { NavLink } from 'react-router-dom';
import '../styles/tabs.css';

export function HeaderTabs() {
  const tabs = [
    { to: '/', label: 'Home' },
    { to: '/order', label: 'Order' },
    { to: '/rewards', label: 'Rewards' },
    { to: '/profile', label: 'Account' },
  ];

  return (
    <div className="tabs-shell">
      <div className="tabs-track">
        {tabs.map((tab) => (
          <NavLink key={tab.to} to={tab.to} end={tab.to === '/'} className={({ isActive }) => `tab-pill ${isActive ? 'active' : ''}`}>
            <span>{tab.label}</span>
          </NavLink>
        ))}
      </div>
    </div>
  );
}
