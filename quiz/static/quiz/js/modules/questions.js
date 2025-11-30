import { State } from './state.js';
import { CONFIG } from './config.js';
import { Utils } from './utils.js';
import { UI } from './ui.js';
import { DOM } from './dom.js';

export const Questions = {
    load: function (index) {
        State.currentIndex = index;
        const qid = State.questionOrder[index].id;
        const url = CONFIG.endpoints.getQuestionUrl(qid);

        return Utils.fetchJSON(url).then(function (data) {
            if (!(qid in State.answers)) {
                State.answers[qid] = {
                    options: data.selected_option_ids || [],
                    text: data.text_answer || ''
                };
            }
            UI.renderQuestion(data.question);
            UI.updateNav();
        }).catch(function (err) {
            console.error('Error loading question:', err);
        });
    },

    saveCurrent: function () {
        const question = State.questionOrder[State.currentIndex];
        if (!question) return Promise.resolve();

        const formData = new FormData();

        if (['single', 'multiple', 'true_false'].includes(question.type)) {
            const inputs = DOM.panel.querySelectorAll('.answer-opt');
            const selected = [];
            inputs.forEach(function (inp) {
                if (inp.checked) selected.push(inp.value);
            });
            State.answers[question.id].options = selected.map(function (x) { return parseInt(x); });
            selected.forEach(function (v) { formData.append('option_ids[]', v); });
        } else if (question.type === 'short_answer') {
            const textarea = DOM.panel.querySelector('.answer-text');
            State.answers[question.id].text = textarea ? textarea.value : '';
            if (textarea) formData.append('text_answer', textarea.value);
        }

        const url = CONFIG.endpoints.getAnswerUrl(question.id);
        return Utils.fetchJSON(url, {
            method: 'POST',
            headers: { 'X-CSRFToken': Utils.csrf() },
            body: formData
        }).catch(function () { });
    },

    finalize: function () {
        if (!confirm('Are you sure you want to submit your quiz? You cannot change answers after submission.')) {
            return;
        }

        State.isSubmitting = true;
        Questions.saveCurrent().then(function () {
            Utils.fetchJSON(CONFIG.endpoints.finalize, {
                method: 'POST',
                headers: { 'X-CSRFToken': Utils.csrf() }
            }).then(function (result) {
                if (result.redirect_url) {
                    window.location = result.redirect_url;
                }
            });
        });
    }
};
