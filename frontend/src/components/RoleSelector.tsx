import React from 'react';
import { Home, Key } from 'lucide-react';

interface Props {
  role: 'tenant' | 'owner';
  setRole: (role: 'tenant' | 'owner') => void;
}

const RoleSelector: React.FC<Props> = ({ role, setRole }) => {
  return (
    <div className="role-selector">
      <div 
        className={`role-card ${role === 'tenant' ? 'selected' : ''}`}
        onClick={() => setRole('tenant')}
      >
        <Key className="role-icon" size={24} />
        <div className="role-title">Tenant</div>
      </div>
      <div 
        className={`role-card ${role === 'owner' ? 'selected' : ''}`}
        onClick={() => setRole('owner')}
      >
        <Home className="role-icon" size={24} />
        <div className="role-title">Owner</div>
      </div>
    </div>
  );
};

export default RoleSelector;
