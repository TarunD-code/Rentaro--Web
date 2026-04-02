import React from 'react';
import { ShieldCheck, Clock, XCircle } from 'lucide-react';

interface Props {
  status: string; // 'verified', 'pending', 'rejected'
}

const TrustBadge: React.FC<Props> = ({ status }) => {
  if (status === 'verified') {
    return (
      <span className="badge badge-success">
        <ShieldCheck size={16} /> Verified User
      </span>
    );
  }
  
  if (status === 'pending') {
    return (
      <span className="badge badge-warning">
        <Clock size={16} /> KYC Pending
      </span>
    );
  }

  return (
    <span className="badge badge-error">
      <XCircle size={16} /> Verification Failed
    </span>
  );
};

export default TrustBadge;
