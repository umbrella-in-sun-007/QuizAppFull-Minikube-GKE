import { CONFIG } from './config.js';
import { State } from './state.js';
import { UI } from './ui.js';

export const Storage = {
    warningKey: 'quiz_warnings_' + CONFIG.attemptId,

    loadWarnings: function () {
        if (CONFIG.security.monitorTabSwitching) {
            const stored = sessionStorage.getItem(Storage.warningKey);
            if (stored) {
                State.focusWarningCount = parseInt(stored) || 0;
                if (State.focusWarningCount > 0) {
                    UI.updateWarningDisplay();
                }
            }
        }
    },

    saveWarnings: function () {
        sessionStorage.setItem(Storage.warningKey, State.focusWarningCount.toString());
    },

    clearWarnings: function () {
        sessionStorage.removeItem(Storage.warningKey);
    }
};
