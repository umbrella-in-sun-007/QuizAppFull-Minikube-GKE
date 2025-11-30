import { State } from './state.js';
import { UI } from './ui.js';
import { Utils } from './utils.js';
import { CONFIG } from './config.js';
import { DOM } from './dom.js';
import { Questions } from './questions.js';

export const Timer = {
    updateFromServer: function (status) {
        State.remainingSeconds = status.remaining_seconds;
        State.lastServerSync = Date.now();
        UI.displayTimer();

        if (status.remaining_seconds <= 0) {
            Timer.handleExpiration();
        }

        if (status.completed) {
            if (DOM.nextBtn) DOM.nextBtn.disabled = true;
            if (DOM.prevBtn) DOM.prevBtn.disabled = true;
            if (DOM.finalizeBtn) DOM.finalizeBtn.disabled = true;
            if (DOM.clearBtn) DOM.clearBtn.disabled = true;
        }
    },

    handleExpiration: function () {
        if (State.isSubmitting) return;
        State.isSubmitting = true;

        Questions.saveCurrent().then(function () {
            Utils.fetchJSON(CONFIG.endpoints.finalize, {
                method: 'POST',
                headers: { 'X-CSRFToken': Utils.csrf() }
            }).then(function (result) {
                if (result && result.redirect_url) {
                    if (State.modalInstance) {
                        DOM.warningMessage.textContent = 'Time has expired! Your quiz has been automatically submitted.';
                        DOM.warningFooter.classList.add('d-none');
                        DOM.ackWarningBtn.classList.add('d-none');
                        State.modalInstance.show();
                    }
                    setTimeout(function () {
                        window.location = result.redirect_url;
                    }, 2000);
                }
            });
        });
    },

    tick: function () {
        if (State.remainingSeconds > 0) {
            State.remainingSeconds--;
            UI.displayTimer();

            if (State.remainingSeconds <= 0) {
                Timer.handleExpiration();
            }
        }
    },

    startSync: function () {
        Utils.fetchJSON(CONFIG.endpoints.status).then(Timer.updateFromServer).catch(function () { });
        setInterval(function () {
            Utils.fetchJSON(CONFIG.endpoints.status).then(Timer.updateFromServer).catch(function () { });
        }, 10000);
        setInterval(Timer.tick, 1000);
    }
};
