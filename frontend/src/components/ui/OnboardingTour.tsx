import { useState, useEffect, useCallback } from 'react'
import { Joyride, STATUS } from 'react-joyride'
import type { Step, CallBackProps } from 'react-joyride'

const TOUR_STORAGE_KEY = 'codeguard_tour_completed'

interface OnboardingTourProps {
  steps?: Step[]
  onComplete?: () => void
}

const defaultSteps: Step[] = [
  {
    target: 'body',
    title: 'Welcome to CodeGuard AI',
    content: 'Let\'s take a quick tour of the key features. This will only take a minute!',
    placement: 'center',
    disableBeacon: true,
  },
  {
    target: '[data-tour="upload"]',
    title: 'Upload Your Code',
    content: 'Drag and drop your source files or upload a ZIP archive. We support Python, JavaScript, TypeScript, Java, Go, and more.',
    placement: 'bottom',
  },
  {
    target: '[data-tour="recent-scans"]',
    title: 'Recent Scans',
    content: 'View your recent scans here. Each scan shows a severity breakdown so you can quickly see what needs attention.',
    placement: 'bottom',
  },
  {
    target: '[data-tour="scan-report"]',
    title: 'Scan Report',
    content: 'When a scan completes, click it to view a detailed report with vulnerable code highlighted, severity ratings, and AI-generated fix suggestions.',
    placement: 'bottom',
  },
  {
    target: '[data-tour="fix-suggestion"]',
    title: 'Fix Suggestions',
    content: 'For each vulnerability, you can preview an AI-generated fix. Applied fixes can be verified by re-scanning your code.',
    placement: 'left',
  },
  {
    target: '[data-tour="sidebar"]',
    title: 'Navigation',
    content: 'Use the sidebar to access your dashboard, scan history, knowledge base, and admin tools (if applicable).',
    placement: 'right',
  },
]

export function OnboardingTour({ steps = defaultSteps, onComplete }: OnboardingTourProps) {
  const [runTour, setRunTour] = useState(false)

  useEffect(() => {
    const tourCompleted = localStorage.getItem(TOUR_STORAGE_KEY)
    if (!tourCompleted) {
      // Small delay to let the page render
      const timer = setTimeout(() => setRunTour(true), 800)
      return () => clearTimeout(timer)
    }
  }, [])

  const handleJoyrideCallback = useCallback((data: CallBackProps) => {
    const { status } = data
    if ([STATUS.FINISHED, STATUS.SKIPPED].includes(status)) {
      setRunTour(false)
      localStorage.setItem(TOUR_STORAGE_KEY, 'true')
      onComplete?.()
    }
  }, [onComplete])

  return (
    <Joyride
      steps={steps}
      run={runTour}
      callback={handleJoyrideCallback}
      continuous
      showProgress
      showSkipButton
      clickToClose
      disableOverlayClose
      styles={{
        options: {
          primaryColor: '#6366f1',
          backgroundColor: '#1e1e2e',
          textColor: '#e2e8f0',
          arrowColor: '#1e1e2e',
          overlayColor: 'rgba(0, 0, 0, 0.6)',
          spotlightShadow: '0 0 15px rgba(0, 0, 0, 0.5)',
          zIndex: 10000,
        },
        tooltipContainer: {
          textAlign: 'left',
        },
        buttonNext: {
          backgroundColor: '#6366f1',
          borderRadius: '0.5rem',
          fontSize: '0.875rem',
        },
        buttonBack: {
          color: '#94a3b8',
          fontSize: '0.875rem',
        },
        buttonSkip: {
          color: '#94a3b8',
          fontSize: '0.75rem',
        },
        tooltip: {
          borderRadius: '0.75rem',
          padding: '1.25rem',
        },
        tooltipTitle: {
          fontSize: '1rem',
          fontWeight: 600,
          marginBottom: '0.5rem',
        },
        tooltipContent: {
          fontSize: '0.875rem',
          lineHeight: 1.5,
        },
      }}
      locale={{
        back: 'Back',
        close: 'Close',
        last: 'Finish',
        next: 'Next',
        skip: 'Skip tour',
      }}
    />
  )
}

export function resetTour() {
  localStorage.removeItem(TOUR_STORAGE_KEY)
}