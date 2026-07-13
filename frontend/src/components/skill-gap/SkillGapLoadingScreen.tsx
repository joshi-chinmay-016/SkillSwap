import React, { useEffect, useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { DotLottieReact } from '@lottiefiles/dotlottie-react';
import Modal from '../common/Modal';
import { useReducedMotion } from 'framer-motion';

// Mapping of stages to user-facing copy
const STAGE_TEXT: Record<string, string> = {
  parsing: 'Reading your profile…',
  analyzing: 'Mapping your skill gaps…',
  roadmapping: 'Building your roadmap…',
  finalizing: 'Almost there…',
};

// Ordered list for timer fallback
const STAGE_ORDER: Array<keyof typeof STAGE_TEXT> = [
  'parsing',
  'analyzing',
  'roadmapping',
  'finalizing',
];

interface SkillGapLoadingScreenProps {
  /** Controls visibility of the modal */
  isOpen: boolean;
  /** Optional explicit stage coming from backend events */
  stage?: keyof typeof STAGE_TEXT;
  /** Optional cancel callback */
  onCancel?: () => void;
}

/**
 * Full‑screen loading modal used while the backend analyses the skill gap.
 * It gracefully degrades when no real‑time stage information is available
 * by cycling through the four stages every ~3.5 seconds.
 */
const SkillGapLoadingScreen: React.FC<SkillGapLoadingScreenProps> = ({
  isOpen,
  stage,
  onCancel,
}) => {
  const prefersReducedMotion = useReducedMotion();
  const [displayStage, setDisplayStage] = useState<keyof typeof STAGE_TEXT>(
    STAGE_ORDER[0]
  );
  const [elapsed, setElapsed] = useState(0);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Timer that tracks elapsed time for secondary messages
  useEffect(() => {
    if (!isOpen) return;
    const start = Date.now();
    const tick = () => {
      setElapsed(Date.now() - start);
    };
    timeoutRef.current = setInterval(tick, 1000);
    return () => {
      if (timeoutRef.current) clearInterval(timeoutRef.current);
    };
  }, [isOpen]);

  // Auto‑cycle stages when no explicit stage prop is supplied
  useEffect(() => {
    // If we receive a real stage, we don't need the fallback timer
    if (stage) {
      setDisplayStage(stage);
      return;
    }
    // Only start the cycle when the modal is open
    if (!isOpen) return;
    let idx = 0;
    setDisplayStage(STAGE_ORDER[idx]);
    intervalRef.current = setInterval(() => {
      idx = (idx + 1) % STAGE_ORDER.length;
      setDisplayStage(STAGE_ORDER[idx]);
    }, 3500);
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [isOpen, stage]);

  // Clean up timers when modal closes
  useEffect(() => {
    if (!isOpen) {
      if (intervalRef.current) clearInterval(intervalRef.current);
      if (timeoutRef.current) clearInterval(timeoutRef.current);
      setElapsed(0);
    }
  }, [isOpen]);

  // Determine when to show secondary messages
  const showLongerMessage = elapsed >= 15000; // 15 s
  const showCancel = elapsed >= 30000 && !!onCancel; // 30 s

  // Accessible live region text
  const liveText = STAGE_TEXT[displayStage];

  // Motion variants for fade/scale
  const containerVariants = {
    hidden: { opacity: 0, scale: 0.95 },
    visible: { opacity: 1, scale: 1, transition: { duration: 0.2 } },
    exit: { opacity: 0, scale: 0.95, transition: { duration: 0.2 } },
  };

  // Lottie autoplay handling for reduced‑motion users
  const lottieProps = prefersReducedMotion
    ? { autoplay: false, loop: false }
    : { autoplay: true, loop: true };

  return (
    <AnimatePresence>
      {isOpen && (
        <Modal isOpen={isOpen} onClose={onCancel ?? (() => {})} title={''}>
          <motion.div
            variants={containerVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
            className="flex flex-col items-center justify-center p-6"
          >
            <DotLottieReact
              src="https://lottie.host/f82a3fa7-d9cc-45d4-9ad1-2bea907cd0cf/Yj8wS2C8KB.lottie"
              style={{ width: 220, height: 220 }}
              {...lottieProps}
            />
            <motion.p
              aria-live="polite"
              key={displayStage}
              className="mt-4 text-xl font-medium text-text-primary"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1, transition: { duration: 0.15 } }}
            >
              {liveText}
            </motion.p>
            {showLongerMessage && (
              <p className="mt-2 text-sm text-text-secondary">
                This is taking a little longer than usual.
              </p>
            )}
            {showCancel && (
              <button
                type="button"
                onClick={onCancel}
                className="mt-4 text-sm underline text-primary hover:text-primary-dark"
              >
                Cancel and go back
              </button>
            )}
          </motion.div>
        </Modal>
      )}
    </AnimatePresence>
  );
};

export default SkillGapLoadingScreen;
