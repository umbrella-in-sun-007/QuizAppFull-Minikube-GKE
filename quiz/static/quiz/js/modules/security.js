import { CONFIG } from './config.js';
import { State } from './state.js';
import { UI } from './ui.js';
import { Storage } from './storage.js';
import { DOM } from './dom.js';
import { Questions } from './questions.js';
import { Utils } from './utils.js';

const WARNING_DEBOUNCE_MS = 2000;

export const Security = {
    enterFullscreen: function () {
        const elem = document.documentElement;
        if (document.fullscreenElement) return;

        if (elem.requestFullscreen) {
            elem.requestFullscreen().catch(function (err) {
                console.log("Fullscreen request failed:", err);
            });
        } else if (elem.webkitRequestFullscreen) {
            elem.webkitRequestFullscreen();
        } else if (elem.msRequestFullscreen) {
            elem.msRequestFullscreen();
        }
    },

    handleViolationLimit: function () {
        const message = 'You have reached the maximum number of warnings.';

        if (CONFIG.security.autoSubmitOnViolations) {
            State.isSubmitting = true;

            if (State.modalInstance) {
                DOM.warningMessage.textContent = message + " Your quiz is being submitted automatically.";
                DOM.warningFooter.classList.add('d-none');
                DOM.ackWarningBtn.classList.add('d-none');
                State.modalInstance.show();
            }

            return Questions.saveCurrent().then(function () {
                return Utils.fetchJSON(CONFIG.endpoints.finalize, {
                    method: 'POST',
                    headers: { 'X-CSRFToken': Utils.csrf() }
                }).then(function (result) {
                    Storage.clearWarnings();
                    if (result.redirect_url) {
                        window.location = result.redirect_url;
                    }
                }).catch(function (err) {
                    console.error('Finalize error:', err);
                });
            });
        } else {
            if (State.modalInstance) {
                DOM.warningMessage.textContent = message + " No automatic submission is configured.";
                DOM.remainingWarnings.textContent = "0";
                DOM.warningFooter.classList.remove('d-none');
                DOM.ackWarningBtn.classList.remove('d-none');
                State.modalInstance.show();
            }
            return Promise.resolve();
        }
    },

    recordWarning: function (reason) {
        if (State.isSubmitting) return Promise.resolve();

        if (!CONFIG.security.monitorTabSwitching && !CONFIG.security.enableFullscreen) {
            return Promise.resolve();
        }

        const now = Date.now();

        if ((now - State.lastWarningAt) < WARNING_DEBOUNCE_MS) {
            console.log("Ignored duplicate warning (debounce):", reason);
            return Promise.resolve();
        }

        State.lastWarningAt = now;

        State.focusWarningCount++;
        Storage.saveWarnings();
        UI.updateWarningDisplay();

        console.log("Recorded warning #" + State.focusWarningCount + " — " + reason);

        if (CONFIG.security.maxTabSwitches > 0 && State.focusWarningCount >= CONFIG.security.maxTabSwitches) {
            return Security.handleViolationLimit();
        } else {
            const remaining = CONFIG.security.maxTabSwitches > 0 ? (CONFIG.security.maxTabSwitches - State.focusWarningCount) : '∞';

            if (State.modalInstance) {
                DOM.warningMessage.textContent = reason;
                DOM.remainingWarnings.textContent = remaining;
                DOM.warningFooter.classList.remove('d-none');
                DOM.ackWarningBtn.classList.remove('d-none');
                State.modalInstance.show();
            }

            return Promise.resolve();
        }
    },

    setupEventListeners: function () {
        console.log("=== SECURITY SETUP START ===");
        console.log("Security Configuration:", CONFIG.security);

        if (CONFIG.security.enableFullscreen) {
            Security.enterFullscreen();

            const enforceFullscreen = function () {
                if (!document.fullscreenElement) {
                    Security.recordWarning('You exited fullscreen mode.');
                    Security.enterFullscreen();
                }
            };

            document.addEventListener('fullscreenchange', function () {
                if (!document.fullscreenElement) {
                    enforceFullscreen();
                } else {
                    State.lastFocusTime = Date.now();
                }
            });
            document.addEventListener('webkitfullscreenchange', function () {
                if (!document.webkitFullscreenElement) enforceFullscreen();
            });
            document.addEventListener('mozfullscreenchange', function () {
                if (!document.mozFullScreen) enforceFullscreen();
            });
            document.addEventListener('MSFullscreenChange', function () {
                if (!document.msFullscreenElement) enforceFullscreen();
            });

            setInterval(function () {
                if (!document.fullscreenElement) {
                    Security.enterFullscreen();
                }
            }, 1000);
        }

        if (CONFIG.security.monitorTabSwitching) {
            document.addEventListener('visibilitychange', function () {
                if (document.hidden) {
                    const t = Date.now();
                    State.lastFocusTime = t;
                    setTimeout(function () {
                        if (document.hidden) {
                            Security.recordWarning('You switched to another tab or minimized the browser.');
                        }
                    }, 800);
                } else {
                    State.lastFocusTime = Date.now();
                }
            });

            window.addEventListener('blur', function () {
                const t = Date.now();
                State.lastFocusTime = t;
                setTimeout(function () {
                    const hasFocus = document.hasFocus && document.hasFocus();
                    if (!hasFocus || document.hidden) {
                        Security.recordWarning('You clicked outside the quiz window or switched applications.');
                    }
                }, 800);
            });

            window.addEventListener('focus', function () {
                State.lastFocusTime = Date.now();
                State.isProcessingWarning = false;
            });
        }

        if (CONFIG.security.disableRightClick) {
            document.addEventListener('contextmenu', function (e) {
                e.preventDefault();
                UI.showInfo('Right-click is disabled during the quiz.');
                return false;
            });
        }

        if (CONFIG.security.disableCopyPaste) {
            document.addEventListener('copy', function (e) {
                e.preventDefault();
                UI.showInfo('Copying is disabled during the quiz.');
            });
            document.addEventListener('paste', function (e) {
                e.preventDefault();
                UI.showInfo('Pasting is disabled during the quiz.');
            });
            document.addEventListener('cut', function (e) {
                e.preventDefault();
                UI.showInfo('Cutting is disabled during the quiz.');
            });
        }

        window.addEventListener('beforeunload', function () {
            if (!State.isSubmitting) {
                Security.recordWarning('You refreshed the page or navigated away.');
            }
        });

        if (CONFIG.security.preventBrowserBack) {
            window.addEventListener('beforeunload', function (e) {
                if (State.isSubmitting) return;
                e.preventDefault();
                e.returnValue = 'Are you sure you want to leave?';
                return 'Are you sure you want to leave?';
            });
        }

        document.addEventListener('keydown', function (e) {
            if (e.keyCode === 123 ||
                (e.ctrlKey && e.shiftKey && (e.keyCode === 73 || e.keyCode === 74)) ||
                (e.ctrlKey && e.keyCode === 85)) {
                e.preventDefault();
                UI.showInfo('This action is not allowed during the quiz.');
            }
        });
    }
};
