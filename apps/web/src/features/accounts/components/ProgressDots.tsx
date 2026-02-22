/**
 * Progress indicator for multi-step wizard.
 * Shows current step, completed steps, and remaining steps with colored dots.
 */

interface ProgressDotsProps {
  currentStep: number;
  totalSteps: number;
}

export function ProgressDots({ currentStep, totalSteps }: ProgressDotsProps) {
  return (
    <div
      className="flex items-center justify-center gap-2"
      role="progressbar"
      aria-valuenow={currentStep + 1}
      aria-valuemin={1}
      aria-valuemax={totalSteps}
    >
      {Array.from({ length: totalSteps }).map((_, index) => (
        <div
          key={index}
          className={`h-2 w-2 rounded-full transition-colors ${
            index === currentStep
              ? 'bg-primary'
              : index < currentStep
                ? 'bg-primary/50'
                : 'bg-muted'
          }`}
          aria-label={`Step ${index + 1}${
            index === currentStep ? ' (current)' : index < currentStep ? ' (completed)' : ''
          }`}
        />
      ))}
    </div>
  );
}
