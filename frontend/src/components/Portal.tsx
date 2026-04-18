import { createPortal } from 'react-dom';
import React, { useEffect, useState } from 'react';

interface PortalProps {
  children: React.ReactNode;
  id?: string;
}

const Portal: React.FC<PortalProps> = ({ children, id = 'portal-root' }) => {
  const [mountNode, setMountNode] = useState<HTMLElement | null>(null);

  useEffect(() => {
    let root = document.getElementById(id);
    if (!root) {
      root = document.createElement('div');
      root.id = id;
      document.body.appendChild(root);
    }
    setMountNode(root);

    // Optional: Cleanup if this is the only thing using the root
    return () => {
      // Logic to remove root if empty could be added here
    };
  }, [id]);

  if (!mountNode) return null;

  return createPortal(children, mountNode);
};

export default Portal;
