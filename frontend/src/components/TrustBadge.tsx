import React from 'react';
import { Chip } from '@mui/material';
import { Verified, PendingActions, Cancel } from '@mui/icons-material';

interface Props {
  status: string; // 'verified', 'pending', 'rejected', 'not_submitted', etc
}

const TrustBadge: React.FC<Props> = ({ status }) => {
  if (status === 'verified') {
    return (
      <Chip 
        icon={<Verified />} 
        label="Verified Host" 
        color="success" 
        size="small" 
        variant="outlined" 
      />
    );
  }
  
  if (status === 'pending_review' || status === 'pending') {
    return (
      <Chip 
        icon={<PendingActions />} 
        label="KYC Pending" 
        color="warning" 
        size="small" 
        variant="outlined" 
      />
    );
  }

  return (
    <Chip 
      icon={<Cancel />} 
      label="Unverified" 
      color="error" 
      size="small" 
      variant="outlined" 
    />
  );
};

export default TrustBadge;
