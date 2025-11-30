import { DOM } from './dom.js';
import { State } from './state.js';
import { Utils } from './utils.js';
import { CONFIG } from './config.js';

export const UI = {
    updateNav: function () {
        if (!DOM.navEl) return;
        Array.from(DOM.navEl.children).forEach(function (col, i) {
            const btn = col.querySelector('button');
            if (!btn) return;

            const qid = State.questionOrder[i].id;
            const hasAnswer = State.answers[qid] && (
                (State.answers[qid].options || []).length ||
                (State.answers[qid].text || '').trim().length
            );

            btn.classList.remove('btn-current', 'btn-answered', 'btn-unanswered');

            if (i === State.currentIndex) {
                btn.classList.add('btn-current');
            } else if (hasAnswer) {
                btn.classList.add('btn-answered');
            } else {
                btn.classList.add('btn-unanswered');
            }
        });

        if (DOM.prevBtn) DOM.prevBtn.disabled = State.currentIndex === 0;
        if (DOM.nextBtn) DOM.nextBtn.disabled = !State.questionOrder.length;
        if (DOM.clearBtn) DOM.clearBtn.disabled = !State.questionOrder.length;
        if (DOM.finalizeBtn) {
            if (State.questionOrder.length === 0) {
                DOM.finalizeBtn.classList.add('d-none');
            } else {
                DOM.finalizeBtn.classList.toggle('d-none', State.currentIndex < State.questionOrder.length - 1);
            }
        }
    },

    updateWarningDisplay: function () {
        if (!CONFIG.security.monitorTabSwitching || !DOM.warningCountEl || !DOM.warningBadge) return;

        DOM.warningCountEl.textContent = State.focusWarningCount;
        if (State.focusWarningCount > 0) {
            DOM.warningBadge.classList.remove('d-none');
            if (CONFIG.security.maxTabSwitches > 0 && State.focusWarningCount >= CONFIG.security.maxTabSwitches - 1) {
                DOM.warningBadge.classList.remove('bg-warning');
                DOM.warningBadge.classList.add('bg-danger', 'text-white');
            } else {
                DOM.warningBadge.classList.remove('bg-danger', 'text-white');
                DOM.warningBadge.classList.add('bg-warning');
            }
        } else {
            DOM.warningBadge.classList.add('d-none');
        }
    },

    displayTimer: function () {
        if (!DOM.timerEl) return;
        DOM.timerEl.textContent = Utils.formatTime(State.remainingSeconds);
        if (State.remainingSeconds <= 60) {
            if (DOM.timerEl.parentElement) DOM.timerEl.parentElement.classList.add('timer-warning');
        } else {
            if (DOM.timerEl.parentElement) DOM.timerEl.parentElement.classList.remove('timer-warning');
        }
    },

    renderQuestion: function (question) {
        if (!DOM.panel) return;
        let html = '<div class="card"><div class="card-body">';
        html += '<div class="d-flex justify-content-between align-items-start mb-3">';
        html += '<h5 class="mb-0">Question ' + (State.currentIndex + 1) + '</h5>';
        html += '<span class="badge bg-info">' + question.marks + ' marks</span>';
        html += '</div>';
        html += '<div class="mb-4">' + question.html + '</div>';

        if (['single', 'multiple', 'true_false'].includes(question.type)) {
            const selected = State.answers[question.id]?.options || [];
            question.options.forEach(function (opt) {
                const inputType = question.type === 'multiple' ? 'checkbox' : 'radio';
                const checked = selected.includes(opt.id) ? 'checked' : '';
                const inputName = 'q_' + question.id + (inputType === 'checkbox' ? '[]' : '');

                html += '<div class="option-card d-flex align-items-center mb-3 p-3 rounded">';
                html += '<input class="form-check-input answer-opt me-3 mt-0" data-q="' + question.id + '" ';
                html += 'type="' + inputType + '" value="' + opt.id + '" id="opt' + opt.id + '" ';
                html += checked + ' name="' + inputName + '">';
                html += '<label class="form-check-label flex-grow-1 stretched-link" for="opt' + opt.id + '">' + opt.text + '</label>';
                html += '</div>';
            });
        } else if (question.type === 'short_answer') {
            const text = State.answers[question.id]?.text || '';
            html += '<textarea class="form-control answer-text" data-q="' + question.id + '" ';
            html += 'rows="5" placeholder="Type your answer here...">' + text + '</textarea>';
        }

        html += '</div></div>';
        DOM.panel.innerHTML = html;
        UI.updateOptionStyles();
    },

    updateOptionStyles: function () {
        const cards = document.querySelectorAll('.option-card');
        cards.forEach(function (card) {
            const input = card.querySelector('input');
            if (input && input.checked) {
                card.classList.add('selected');
            } else {
                card.classList.remove('selected');
            }
        });
    },

    showInfo: function (message) {
        if (State.modalInstance) {
            DOM.warningMessage.textContent = message;
            DOM.warningFooter.classList.add('d-none');
            DOM.ackWarningBtn.classList.remove('d-none');
            State.modalInstance.show();
        } else {
            alert(message);
        }
    }
};
