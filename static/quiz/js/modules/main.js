import { CONFIG } from './config.js';
import { State } from './state.js';
import { DOM } from './dom.js';
import { Utils } from './utils.js';
import { UI } from './ui.js';
import { Questions } from './questions.js';
import { Timer } from './timer.js';
import { Security } from './security.js';
import { Storage } from './storage.js';

const App = {
    setupQuestionNav: function () {
        Utils.fetchJSON(CONFIG.endpoints.questions).then(function (data) {
            State.questionOrder = data.questions;
            if (DOM.navEl) DOM.navEl.innerHTML = '';

            State.questionOrder.forEach(function (q, i) {
                State.answers[q.id] = { options: [], text: '' };

                const col = document.createElement('div');
                col.className = 'col';

                const btn = document.createElement('button');
                btn.type = 'button';
                btn.className = 'btn question-btn btn-unanswered w-100';
                btn.textContent = i + 1;
                btn.addEventListener('click', function () {
                    Questions.saveCurrent().then(function () { Questions.load(i); });
                });

                col.appendChild(btn);
                if (DOM.navEl) DOM.navEl.appendChild(col);
            });

            if (State.questionOrder.length) {
                Questions.load(0);
            }
        }).catch(function (err) {
            console.error('Error loading questions:', err);
        });
    },

    setupButtons: function () {
        if (DOM.nextBtn) {
            DOM.nextBtn.addEventListener('click', function () {
                if (State.currentIndex < State.questionOrder.length - 1) {
                    Questions.saveCurrent().then(function () { Questions.load(State.currentIndex + 1); });
                }
            });
        }

        if (DOM.prevBtn) {
            DOM.prevBtn.addEventListener('click', function () {
                if (State.currentIndex > 0) {
                    Questions.saveCurrent().then(function () { Questions.load(State.currentIndex - 1); });
                }
            });
        }

        if (DOM.clearBtn) {
            DOM.clearBtn.addEventListener('click', function () {
                const q = State.questionOrder[State.currentIndex];
                if (!q) return;

                // Clear DOM inputs directly instead of re-rendering (which requires full question data)
                if (['single', 'multiple', 'true_false'].includes(q.type)) {
                    const inputs = DOM.panel.querySelectorAll('.answer-opt');
                    inputs.forEach(function (inp) {
                        inp.checked = false;
                    });
                    UI.updateOptionStyles();
                } else if (q.type === 'short_answer') {
                    const textarea = DOM.panel.querySelector('.answer-text');
                    if (textarea) textarea.value = '';
                }

                // Save empty state to server and update nav
                Questions.saveCurrent().then(UI.updateNav);
            });
        }

        if (DOM.finalizeBtn) {
            DOM.finalizeBtn.addEventListener('click', Questions.finalize);
        }

        if (DOM.ackWarningBtn) {
            DOM.ackWarningBtn.addEventListener('click', function () {
                if (State.modalInstance) {
                    State.modalInstance.hide();
                }
                if (CONFIG.security.enableFullscreen) {
                    Security.enterFullscreen();
                }
            });
        }

        document.addEventListener('change', function (e) {
            if (e.target && e.target.classList && e.target.classList.contains('answer-opt')) {
                UI.updateNav();
                UI.updateOptionStyles();
            }
        });
    },

    init: function () {
        console.log("Initializing quiz app...");

        if (DOM.warningModalEl && window.bootstrap) {
            State.modalInstance = new bootstrap.Modal(DOM.warningModalEl);
        }

        Storage.loadWarnings();

        // Setup start button handler
        if (DOM.startQuizBtn) {
            DOM.startQuizBtn.addEventListener('click', function () {
                // 1. Enter Fullscreen
                Security.enterFullscreen();

                // 2. Hide Overlay, Show App
                if (DOM.startOverlay) DOM.startOverlay.classList.add('d-none');
                if (DOM.quizApp) DOM.quizApp.classList.remove('d-none');

                // 3. Start Quiz Logic
                App.startQuiz();
            });
        } else {
            // Fallback if no start button (shouldn't happen with new template)
            App.startQuiz();
        }
    },

    startQuiz: function () {
        if (CONFIG.security.maxTabSwitches > 0 && State.focusWarningCount >= CONFIG.security.maxTabSwitches) {
            Security.handleViolationLimit();
        }
        Timer.startSync();
        App.setupQuestionNav();
        App.setupButtons();
        Security.setupEventListeners();

        console.log("Quiz started!");
    }
};

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', App.init);
} else {
    App.init();
}
