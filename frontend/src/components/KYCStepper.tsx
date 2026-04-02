import React from 'react';

interface Props {
  currentStep: number;
}

const KYCStepper: React.FC<Props> = ({ currentStep }) => {
  const steps = [
    "Personal Info",
    "Document Upload",
    "Verification"
  ];

  return (
    <div className="stepper-container">
      {steps.map((label, index) => {
        const isActive = index === currentStep;
        const isCompleted = index < currentStep;

        return (
          <div key={label} className={`stepper-item ${isActive ? 'active' : ''} ${isCompleted ? 'completed' : ''}`}>
            <div className="stepper-circle">
              {isCompleted ? "✓" : index + 1}
            </div>
            <div className="stepper-label">{label}</div>
            {index < steps.length - 1 && <div className="stepper-line" />}
          </div>
        );
      })}
    </div>
  );
};

export default KYCStepper;
