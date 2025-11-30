import { DOM } from './dom.js';

const quizApp = DOM.quizApp;

export const CONFIG = {
    attemptId: quizApp ? quizApp.dataset.attempt : null,
    security: {
        monitorTabSwitching: quizApp ? quizApp.dataset.monitorTabSwitching === 'true' : false,
        maxTabSwitches: quizApp ? (parseInt(quizApp.dataset.maxTabSwitches) || 0) : 0,
        autoSubmitOnViolations: quizApp ? quizApp.dataset.autoSubmitOnViolations === 'true' : false,
        enableFullscreen: true, // forced to ALWAYS be true (per prior change)
        disableRightClick: quizApp ? quizApp.dataset.disableRightClick === 'true' : false,
        disableCopyPaste: quizApp ? quizApp.dataset.disableCopyPaste === 'true' : false,
        preventBrowserBack: quizApp ? quizApp.dataset.preventBrowserBack === 'true' : false
    },
    endpoints: {
        questions: quizApp ? quizApp.dataset.questionsUrl : '',
        status: quizApp ? quizApp.dataset.statusUrl : '',
        questionBase: quizApp ? quizApp.dataset.questionBaseUrl : '',
        answerBase: quizApp ? quizApp.dataset.answerBaseUrl : '',
        finalize: quizApp ? quizApp.dataset.finalizeUrl : '',
        getQuestionUrl: function (qid) {
            return this.questionBase.replace('/0/', '/' + qid + '/');
        },
        getAnswerUrl: function (qid) {
            return this.answerBase.replace('/0/', '/' + qid + '/');
        }
    }
};
