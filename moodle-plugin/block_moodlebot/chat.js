/**
 * MoodleBot chat widget.
 *
 * Builds the chat interface inside every `.block_moodlebot_chat` container and
 * talks to blocks/moodlebot/ajax.php (same origin, Moodle session + sesskey).
 * The browser never contacts the AI backend directly.
 *
 * Security notes:
 *  - Answers come from an LLM and must be treated as untrusted. Everything is
 *    rendered with DOM nodes / textContent, never innerHTML, so a malicious
 *    document or prompt cannot inject markup or scripts.
 *  - The conversation id is kept in sessionStorage keyed by Moodle user id and
 *    course id, so a shared computer never shows one student's chat to another.
 *
 * @package    block_moodlebot
 * @license    http://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */
(function() {
    'use strict';

    var MAX_LENGTH = 1000;

    // ------------------------------------------------------------ helpers

    function el(tag, className, text) {
        var node = document.createElement(tag);
        if (className) {
            node.className = className;
        }
        if (text !== undefined && text !== null) {
            node.textContent = text;
        }
        return node;
    }

    /** Appends text with **bold** and `code` spans as safe DOM nodes. */
    function appendInline(parent, text) {
        var parts = text.split(/(\*\*[^*\n]+\*\*|`[^`\n]+`)/g);
        parts.forEach(function(part) {
            if (!part) {
                return;
            }
            if (part.length > 4 && part.slice(0, 2) === '**' && part.slice(-2) === '**') {
                parent.appendChild(el('strong', '', part.slice(2, -2)));
            } else if (part.length > 2 && part.charAt(0) === '`' && part.charAt(part.length - 1) === '`') {
                parent.appendChild(el('code', '', part.slice(1, -1)));
            } else {
                parent.appendChild(document.createTextNode(part));
            }
        });
    }

    /**
     * Minimal, safe formatting for LLM answers: paragraphs, bullet / numbered
     * lists, fenced code blocks (SQL!), **bold** and `inline code`.
     */
    function renderRich(container, text) {
        var lines = String(text).replace(/\r\n?/g, '\n').split('\n');
        var i = 0;
        var paragraph = [];
        var list = null;

        function flushParagraph() {
            if (paragraph.length) {
                var p = el('p');
                appendInline(p, paragraph.join(' '));
                container.appendChild(p);
                paragraph = [];
            }
        }
        function flushList() {
            list = null;
        }

        while (i < lines.length) {
            var line = lines[i];

            if (/^\s*```/.test(line)) {                       // fenced code block
                flushParagraph();
                flushList();
                var code = [];
                i++;
                while (i < lines.length && !/^\s*```/.test(lines[i])) {
                    code.push(lines[i]);
                    i++;
                }
                var pre = el('pre');
                pre.appendChild(el('code', '', code.join('\n')));
                container.appendChild(pre);
                i++;
                continue;
            }

            var bullet = /^\s*[-*•]\s+(.*)$/.exec(line);
            var numbered = /^\s*\d+[.)]\s+(.*)$/.exec(line);
            if (bullet || numbered) {
                flushParagraph();
                var wanted = bullet ? 'UL' : 'OL';
                if (!list || list.tagName !== wanted) {
                    list = el(wanted.toLowerCase());
                    container.appendChild(list);
                }
                var li = el('li');
                appendInline(li, (bullet || numbered)[1]);
                list.appendChild(li);
                i++;
                continue;
            }

            if (/^\s*$/.test(line)) {                          // blank line
                flushParagraph();
                flushList();
            } else {
                flushList();
                paragraph.push(line.trim());
            }
            i++;
        }
        flushParagraph();
    }

    function storageGet(key) {
        try {
            return window.sessionStorage.getItem(key);
        } catch (e) {
            return null;
        }
    }

    function storageSet(key, value) {
        try {
            if (value === null) {
                window.sessionStorage.removeItem(key);
            } else {
                window.sessionStorage.setItem(key, value);
            }
        } catch (e) {
            // Storage disabled (private mode): the chat still works, it just won't survive a reload.
        }
    }

    // ------------------------------------------------------------ widget

    function init(root) {
        if (root.getAttribute('data-ready')) {
            return;
        }
        root.setAttribute('data-ready', '1');

        var endpoint = root.getAttribute('data-endpoint');
        var sesskey = root.getAttribute('data-sesskey');
        var courseId = root.getAttribute('data-courseid');
        var userId = root.getAttribute('data-userid');
        var S = {};
        try {
            S = JSON.parse(root.getAttribute('data-strings') || '{}');
        } catch (e) {
            S = {};
        }
        var storageKey = 'moodlebot_session_' + userId + '_' + courseId;
        var sessionId = storageGet(storageKey);
        var busy = false;

        // ---- DOM
        var log = el('div', 'block_moodlebot_log');
        log.setAttribute('role', 'log');
        log.setAttribute('aria-live', 'polite');

        var input = el('textarea', 'block_moodlebot_input form-control');
        input.setAttribute('rows', '2');
        input.setAttribute('maxlength', String(MAX_LENGTH));
        input.setAttribute('placeholder', S.placeholder || '');
        input.setAttribute('aria-label', S.placeholder || 'Question');

        var sendBtn = el('button', 'block_moodlebot_send btn btn-primary', S.send || 'Send');
        sendBtn.setAttribute('type', 'button');

        var newBtn = el('button', 'block_moodlebot_new btn btn-link btn-sm', S.newchat || 'New chat');
        newBtn.setAttribute('type', 'button');

        var controls = el('div', 'block_moodlebot_controls');
        controls.appendChild(sendBtn);

        var composer = el('div', 'block_moodlebot_composer');
        composer.appendChild(input);
        composer.appendChild(controls);

        var footer = el('div', 'block_moodlebot_footer');
        footer.appendChild(el('small', 'block_moodlebot_disclaimer', S.disclaimer || ''));
        footer.appendChild(newBtn);

        root.appendChild(log);
        root.appendChild(composer);
        root.appendChild(footer);

        // ---- messages
        function scrollDown() {
            log.scrollTop = log.scrollHeight;
        }

        function addUser(text) {
            var row = el('div', 'block_moodlebot_msg block_moodlebot_user');
            row.appendChild(el('div', 'block_moodlebot_bubble', text));
            log.appendChild(row);
            scrollDown();
        }

        function addNotice(text, isError) {
            var row = el('div', 'block_moodlebot_msg block_moodlebot_bot');
            row.appendChild(el('div', 'block_moodlebot_bubble' + (isError ? ' block_moodlebot_error' : ''), text));
            log.appendChild(row);
            scrollDown();
            return row;
        }

        function addBot(data) {
            var row = el('div', 'block_moodlebot_msg block_moodlebot_bot');
            var bubble = el('div', 'block_moodlebot_bubble');
            renderRich(bubble, data.answer);
            row.appendChild(bubble);

            if (data.sources && data.sources.length) {
                var src = el('div', 'block_moodlebot_sources');
                src.appendChild(el('span', 'block_moodlebot_sources_label', (S.sources || 'Sources') + ': '));
                src.appendChild(document.createTextNode(data.sources.join(', ')));
                row.appendChild(src);
            }

            if (data.interaction_id) {
                row.appendChild(buildFeedback(data.interaction_id, data.rating));
            }
            log.appendChild(row);
            scrollDown();
        }

        function buildFeedback(interactionId, existing) {
            var bar = el('div', 'block_moodlebot_feedback');
            var up = el('button', 'btn btn-sm btn-outline-secondary', '\uD83D\uDC4D');
            var down = el('button', 'btn btn-sm btn-outline-secondary', '\uD83D\uDC4E');
            up.setAttribute('type', 'button');
            down.setAttribute('type', 'button');
            up.setAttribute('aria-label', S.helpful || 'Helpful');
            down.setAttribute('aria-label', S.nothelpful || 'Not helpful');
            up.title = S.helpful || '';
            down.title = S.nothelpful || '';
            var thanks = el('span', 'block_moodlebot_thanks');

            function lock(rating) {
                up.disabled = true;
                down.disabled = true;
                (rating === 1 ? up : down).classList.add('active');
                thanks.textContent = S.thanks || '';
            }
            function rate(rating) {
                lock(rating);
                post({action: 'feedback', interactionid: interactionId, rating: rating}).catch(function() {
                    // Feedback is best-effort; never disturb the student with an error here.
                });
            }
            up.addEventListener('click', function() {
                rate(1);
            });
            down.addEventListener('click', function() {
                rate(-1);
            });
            bar.appendChild(up);
            bar.appendChild(down);
            bar.appendChild(thanks);
            if (existing === 1 || existing === -1) {
                lock(existing);
            }
            return bar;
        }

        function showWelcome() {
            addNotice(S.welcome || '', false);
        }

        // ---- network
        function post(fields) {
            var body = new FormData();
            body.append('sesskey', sesskey);
            body.append('courseid', courseId);
            Object.keys(fields).forEach(function(key) {
                body.append(key, fields[key]);
            });
            return fetch(endpoint, {method: 'POST', body: body, credentials: 'same-origin'})
                .then(function(response) {
                    return response.json().catch(function() {
                        return {ok: false, code: 'unavailable'};
                    });
                });
        }

        function errorText(code) {
            if (code === 'ratelimit') {
                return S.error_ratelimit || S.error_generic || 'Error';
            }
            if (code === 'unavailable') {
                return S.error_unavailable || S.error_generic || 'Error';
            }
            return S.error_generic || 'Error';
        }

        function setBusy(state) {
            busy = state;
            sendBtn.disabled = state;
            input.disabled = state;
        }

        function send() {
            var question = input.value.trim();
            if (!question || busy) {
                return;
            }
            addUser(question);
            input.value = '';
            setBusy(true);
            var thinking = addNotice(S.thinking || '...', false);
            thinking.classList.add('block_moodlebot_thinking');

            var fields = {action: 'chat', question: question};
            if (sessionId) {
                fields.session = sessionId;
            }
            post(fields).then(function(data) {
                log.removeChild(thinking);
                if (data && data.ok && typeof data.answer === 'string') {
                    if (data.session_id) {
                        sessionId = data.session_id;
                        storageSet(storageKey, sessionId);
                    }
                    addBot(data);
                } else {
                    addNotice(errorText(data && data.code), true);
                }
            }).catch(function() {
                if (thinking.parentNode) {
                    log.removeChild(thinking);
                }
                addNotice(errorText('unavailable'), true);
            }).then(function() {
                setBusy(false);
                input.focus();
            });
        }

        function restoreHistory() {
            if (!sessionId) {
                showWelcome();
                return;
            }
            post({action: 'history', session: sessionId}).then(function(data) {
                var messages = (data && data.ok && data.messages) || [];
                if (!messages.length) {
                    storageSet(storageKey, null);
                    sessionId = null;
                    showWelcome();
                    return;
                }
                messages.forEach(function(m) {
                    addUser(m.question);
                    addBot({answer: m.answer, sources: m.sources, interaction_id: m.interaction_id, rating: m.rating});
                });
            }).catch(showWelcome);
        }

        // ---- events
        sendBtn.addEventListener('click', send);
        input.addEventListener('keydown', function(event) {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                send();
            }
        });
        newBtn.addEventListener('click', function() {
            if (busy) {
                return;
            }
            sessionId = null;
            storageSet(storageKey, null);
            while (log.firstChild) {
                log.removeChild(log.firstChild);
            }
            showWelcome();
            input.focus();
        });

        restoreHistory();
    }

    function initAll() {
        var roots = document.querySelectorAll('.block_moodlebot_chat');
        for (var i = 0; i < roots.length; i++) {
            init(roots[i]);
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initAll);
    } else {
        initAll();
    }
}());
