/**
 * WizardProgress component - Step indicator for the import wizard.
 * Shows current progress through the wizard steps with visual indicators.
 */

import type { WizardStep } from '../../types/importWizard'

interface Step {
  key: WizardStep
  label: string
  description: string
}

const STEPS: Step[] = [
  {
    key: 'upload',
    label: 'Upload',
    description: 'Select CSV file',
  },
  {
    key: 'mapping',
    label: 'Map Columns',
    description: 'Match columns to fields',
  },
  {
    key: 'date_format',
    label: 'Date Format',
    description: 'Configure date parsing',
  },
  {
    key: 'validation',
    label: 'Validate',
    description: 'Review data quality',
  },
  {
    key: 'preview',
    label: 'Confirm',
    description: 'Review and import',
  },
]

interface WizardProgressProps {
  currentStep: WizardStep
  onStepClick?: (step: WizardStep) => void
  allowNavigation?: boolean
}

export default function WizardProgress({
  currentStep,
  onStepClick,
  allowNavigation = false,
}: WizardProgressProps) {
  const currentIndex = STEPS.findIndex((s) => s.key === currentStep)

  const getStepStatus = (index: number): 'completed' | 'current' | 'upcoming' => {
    if (currentStep === 'completed') return 'completed'
    if (index < currentIndex) return 'completed'
    if (index === currentIndex) return 'current'
    return 'upcoming'
  }

  const handleStepClick = (step: Step, index: number) => {
    if (!allowNavigation || !onStepClick) return
    // Only allow navigating to completed steps
    if (index < currentIndex) {
      onStepClick(step.key)
    }
  }

  return (
    <nav aria-label="Progress" className="mb-8">
      <ol className="flex items-center">
        {STEPS.map((step, index) => {
          const status = getStepStatus(index)
          const isLast = index === STEPS.length - 1
          const isClickable = allowNavigation && index < currentIndex

          return (
            <li
              key={step.key}
              className={`relative ${isLast ? '' : 'flex-1'}`}
            >
              <div className="flex items-center">
                {/* Step circle */}
                <button
                  type="button"
                  onClick={() => handleStepClick(step, index)}
                  disabled={!isClickable}
                  className={`
                    relative z-10 flex h-10 w-10 items-center justify-center rounded-full
                    transition-colors duration-200
                    ${status === 'completed'
                      ? 'bg-blue-600 hover:bg-blue-700'
                      : status === 'current'
                        ? 'border-2 border-blue-600 bg-white'
                        : 'border-2 border-gray-300 bg-white'
                    }
                    ${isClickable ? 'cursor-pointer' : 'cursor-default'}
                  `}
                  aria-current={status === 'current' ? 'step' : undefined}
                >
                  {status === 'completed' ? (
                    <svg
                      className="h-5 w-5 text-white"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path
                        fillRule="evenodd"
                        d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                        clipRule="evenodd"
                      />
                    </svg>
                  ) : (
                    <span
                      className={`text-sm font-medium ${
                        status === 'current' ? 'text-blue-600' : 'text-gray-500'
                      }`}
                    >
                      {index + 1}
                    </span>
                  )}
                </button>

                {/* Connector line */}
                {!isLast && (
                  <div
                    className={`
                      hidden sm:flex flex-1 h-0.5 mx-2
                      ${index < currentIndex ? 'bg-blue-600' : 'bg-gray-300'}
                    `}
                  />
                )}
              </div>

              {/* Label (visible on larger screens) */}
              <div className="hidden sm:block mt-2">
                <span
                  className={`text-xs font-medium ${
                    status === 'current'
                      ? 'text-blue-600'
                      : status === 'completed'
                        ? 'text-gray-900'
                        : 'text-gray-500'
                  }`}
                >
                  {step.label}
                </span>
                <p className="text-xs text-gray-500 hidden lg:block">
                  {step.description}
                </p>
              </div>
            </li>
          )
        })}
      </ol>

      {/* Mobile: Current step label */}
      <div className="sm:hidden mt-4 text-center">
        <span className="text-sm font-medium text-blue-600">
          Step {currentIndex + 1}: {STEPS[currentIndex]?.label || 'Complete'}
        </span>
        <p className="text-xs text-gray-500 mt-1">
          {STEPS[currentIndex]?.description}
        </p>
      </div>
    </nav>
  )
}
