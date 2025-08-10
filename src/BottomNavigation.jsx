import React, { useEffect, useRef } from 'react';
import { Home, Shirt, Sparkles, Heart, User } from 'lucide-react';

const BottomNavigation = ({ activePage, onPageChange }) => {
  const barRef = useRef(null);

  useEffect(() => {
    const root = document.documentElement;
    const el = barRef.current;
    if (!el) return;

    const recompute = () => {
      const h = Math.round(el.getBoundingClientRect().height) || 0;
      root.style.setProperty('--tabbar-h', `${h}px`);
      const styles = getComputedStyle(root);
      const safe = parseFloat(styles.getPropertyValue('--safe')) || 0;
      const vvBot = parseFloat(styles.getPropertyValue('--vv-bottom')) || 0;
      const gap = Math.max(h + safe, vvBot);
      root.style.setProperty('--bottom-gap', `${gap}px`);
    };

    const ro = new ResizeObserver(recompute);
    ro.observe(el);
    window.addEventListener('resize', recompute);
    // initial
    recompute();

    return () => {
      try { ro.disconnect(); } catch (_) {}
      window.removeEventListener('resize', recompute);
    };
  }, []);

  const navItems = [
    { id: 'home', icon: Home, label: 'Главная' },
    { id: 'wardrobe', icon: Shirt, label: 'Гардероб' },
    { id: 'capsules', icon: Sparkles, label: 'Капсулы' },
    { id: 'favorites', icon: Heart, label: 'Избранное' },
    { id: 'profile', icon: User, label: 'Профиль' }
  ];

  return (
    <div className="bottom-navigation" id="tabbar" ref={barRef}>
      {navItems.map((item) => {
        const IconComponent = item.icon;
        const isActive = activePage === item.id;
        
        return (
          <button
            key={item.id}
            className={`nav-item ${isActive ? 'active' : ''}`}
            onClick={() => onPageChange(item.id)}
          >
            <IconComponent 
              size={24} 
              className={`nav-icon ${isActive ? 'active' : ''}`}
            />
            <span className="nav-label">{item.label}</span>
          </button>
        );
      })}
    </div>
  );
};

export default BottomNavigation; 