import React from 'react';
import { Home, Shirt, Sparkles, Heart, User } from 'lucide-react';

const BottomNavigation = ({ activePage, onPageChange }) => {
  const navItems = [
    { id: 'home', icon: Home, label: 'Главная' },
    { id: 'wardrobe', icon: Shirt, label: 'Гардероб' },
    { id: 'capsules', icon: Sparkles, label: 'Капсулы' },
    { id: 'favorites', icon: Heart, label: 'Избранное' },
    { id: 'profile', icon: User, label: 'Профиль' }
  ];

  return (
    <div className="bottom-navigation">
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