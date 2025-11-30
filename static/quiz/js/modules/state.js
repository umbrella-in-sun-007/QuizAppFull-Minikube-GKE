export const State = {
    questionOrder: [],
    currentIndex: 0,
    answers: {},
    remainingSeconds: 0,
    lastServerSync: 0,
    focusWarningCount: 0,
    isProcessingWarning: false,
    isSubmitting: false,
    lastFocusTime: Date.now(),
    // used for deduplication
    lastWarningAt: 0,
    modalInstance: null
};
