export interface Clause {
  id: string;
  category: 'Standard' | 'Financial' | 'Restrictions' | 'Maintenance' | 'Legal';
  text: string;
  isMandatory: boolean;
  defaultChecked: boolean;
}

export const DEFAULT_CLAUSES: Clause[] = [
  {
    id: 'standard_term',
    category: 'Standard',
    text: 'The lease term shall be for 11 months unless terminated earlier by mutual consent or notice.',
    isMandatory: true,
    defaultChecked: true
  },
  {
    id: 'security_deposit',
    category: 'Financial',
    text: 'The tenant agrees to pay a security deposit equivalent to 2 months of rent, refundable upon termination.',
    isMandatory: true,
    defaultChecked: true
  },
  {
    id: 'maintenance_fees',
    category: 'Financial',
    text: 'Monthly maintenance charges as levied by the society shall be paid directly by the tenant.',
    isMandatory: false,
    defaultChecked: true
  },
  {
    id: 'no_pets',
    category: 'Restrictions',
    text: 'No pets are allowed inside the premises without written consent from the owner.',
    isMandatory: false,
    defaultChecked: false
  },
  {
    id: 'painting_clause',
    category: 'Maintenance',
    text: 'The premises shall be painted at the time of move-out at the expense of the tenant.',
    isMandatory: false,
    defaultChecked: true
  },
  {
    id: 'subletting',
    category: 'Restrictions',
    text: 'Subletting the premises or any part thereof is strictly prohibited.',
    isMandatory: true,
    defaultChecked: true
  },
  {
    id: 'lock_in_period',
    category: 'Standard',
    text: 'There shall be a mandatory lock-in period of 6 months for both parties.',
    isMandatory: false,
    defaultChecked: false
  }
];

export interface Template {
  id: string;
  name: string;
  description: string;
  baseClauses: string[]; // IDs of default clauses
}

export const AGREEMENT_TEMPLATES: Template[] = [
  {
    id: 'residential_standard',
    name: 'Standard Residential Lease',
    description: 'Best for apartments and independent houses.',
    baseClauses: ['standard_term', 'security_deposit', 'maintenance_fees', 'subletting']
  },
  {
    id: 'commercial_light',
    name: 'Light Commercial / Office',
    description: 'Simplified agreement for small office spaces.',
    baseClauses: ['standard_term', 'security_deposit', 'subletting']
  }
];
