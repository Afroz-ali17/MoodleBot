/**
 * Behavioural tests for blocks/moodlebot/chat.js, run in jsdom against a fake ajax.php.
 *
 *   cd moodle-plugin/tests && npm install && npm test
 */
const fs = require('fs');
const path = require('path');
const assert = require('assert');
const { JSDOM } = require('jsdom');

const SCRIPT = fs.readFileSync(path.join(__dirname, '..', 'block_moodlebot', 'chat.js'), 'utf8');
const STRINGS = {
  welcome: 'Hi! Ask me about the course.', placeholder: 'Ask a question', send: 'Send',
  thinking: 'Thinking', sources: 'Sources', helpful: 'Helpful', nothelpful: 'Not helpful',
  thanks: 'Thanks for the feedback', disclaimer: 'MoodleBot can make mistakes.', newchat: 'New chat',
  error_generic: 'GENERIC_ERR', error_unavailable: 'UNAVAILABLE_ERR', error_ratelimit: 'RATELIMIT_ERR',
};

/** Builds a page with the block container and a scripted fake backend. */
function setup(handler, sessionPreset) {
  const dom = new JSDOM(
    `<!DOCTYPE html><body><div class="block_moodlebot_chat"
       data-endpoint="/blocks/moodlebot/ajax.php" data-sesskey="KEY123" data-courseid="7" data-userid="42"
       data-strings='${JSON.stringify(STRINGS).replace(/'/g, '&#39;')}'></div></body>`,
    { runScripts: 'outside-only', url: 'http://moodle.test/course/view.php?id=7' });
  const w = dom.window;
  if (sessionPreset) w.sessionStorage.setItem('moodlebot_session_42_7', sessionPreset);
  const calls = [];
  w.fetch = (url, opts) => {
    const fields = {};
    for (const [k, v] of opts.body.entries()) fields[k] = v;
    calls.push({ url, fields, credentials: opts.credentials });
    const out = handler(fields);
    return Promise.resolve({ json: () => (out instanceof Error ? Promise.reject(out) : Promise.resolve(out)) });
  };
  w.eval(SCRIPT);
  return { w, doc: w.document, calls };
}

const tick = (ms = 10) => new Promise(r => setTimeout(r, ms));
const logText = doc => doc.querySelector('.block_moodlebot_log').textContent;
const type = (doc, text) => { doc.querySelector('textarea').value = text; };
const clickSend = doc => doc.querySelector('.block_moodlebot_send').click();

const tests = [];
const test = (name, fn) => tests.push([name, fn]);

test('shows welcome message and disclaimer on a fresh load', async () => {
  const { doc, calls } = setup(() => ({ ok: true }));
  await tick();
  assert.ok(logText(doc).includes(STRINGS.welcome));
  assert.ok(doc.body.textContent.includes(STRINGS.disclaimer));
  assert.strictEqual(calls.length, 0, 'no history call without a stored session');
});

test('send: posts sesskey/courseid/action, renders answer + sources, stores session', async () => {
  const { doc, calls, w } = setup(f => ({
    ok: true, answer: 'Third normal form removes **transitive** dependencies.',
    sources: ['normalization/notes.txt'], session_id: 'abc12345', interaction_id: 9 }));
  await tick();
  type(doc, 'What is 3NF?');
  clickSend(doc);
  await tick();
  const c = calls[0];
  assert.deepStrictEqual([c.fields.action, c.fields.sesskey, c.fields.courseid, c.fields.question],
    ['chat', 'KEY123', '7', 'What is 3NF?']);
  assert.strictEqual(c.credentials, 'same-origin');
  assert.ok(!('session' in c.fields), 'first message has no session yet');
  assert.ok(logText(doc).includes('What is 3NF?'));
  assert.strictEqual(doc.querySelector('.block_moodlebot_bot strong').textContent, 'transitive');
  assert.ok(logText(doc).includes('normalization/notes.txt'));
  assert.strictEqual(w.sessionStorage.getItem('moodlebot_session_42_7'), 'abc12345');
  assert.strictEqual(doc.querySelector('textarea').disabled, false, 're-enabled after reply');
});

test('follow-up question re-sends the stored session id', async () => {
  const { doc, calls } = setup(f => (f.action === 'history' ? { ok: true, messages: [{
      interaction_id: 1, question: 'old q', answer: 'old a', sources: [], rating: null }] }
    : { ok: true, answer: 'next', sources: [], session_id: 'sess9999', interaction_id: 2 }), 'sess9999');
  await tick();
  type(doc, 'why?'); clickSend(doc); await tick();
  const chat = calls.find(c => c.fields.action === 'chat');
  assert.strictEqual(chat.fields.session, 'sess9999');
});

test('XSS: HTML in an LLM answer is shown as text, never parsed', async () => {
  const evil = '<img src=x onerror="window.pwned=1"><script>window.pwned=2</script> **ok**';
  const { doc, w } = setup(() => ({ ok: true, answer: evil, sources: ['<b>x</b>'], session_id: 's1234567', interaction_id: 1 }));
  await tick();
  type(doc, 'hi'); clickSend(doc); await tick();
  assert.strictEqual(doc.querySelectorAll('.block_moodlebot_log img, .block_moodlebot_log script').length, 0);
  assert.strictEqual(doc.querySelectorAll('.block_moodlebot_sources b').length, 0);
  assert.ok(logText(doc).includes('<img src=x'), 'markup is displayed literally');
  assert.strictEqual(w.pwned, undefined);
});

test('renders lists and fenced SQL code blocks', async () => {
  const answer = 'Steps:\n- first\n- second\n\n1. one\n2. two\n\n```sql\nSELECT * FROM t;\n```';
  const { doc } = setup(() => ({ ok: true, answer, sources: [], session_id: 's1234567', interaction_id: 1 }));
  await tick(); type(doc, 'q'); clickSend(doc); await tick();
  assert.strictEqual(doc.querySelectorAll('.block_moodlebot_bot ul li').length, 2);
  assert.strictEqual(doc.querySelectorAll('.block_moodlebot_bot ol li').length, 2);
  assert.strictEqual(doc.querySelector('.block_moodlebot_bot pre code').textContent, 'SELECT * FROM t;');
});

test('error codes map to the right translated message', async () => {
  for (const [code, expected] of [['ratelimit', 'RATELIMIT_ERR'], ['unavailable', 'UNAVAILABLE_ERR'], ['error', 'GENERIC_ERR']]) {
    const { doc } = setup(() => ({ ok: false, code }));
    await tick(); type(doc, 'q'); clickSend(doc); await tick();
    assert.ok(logText(doc).includes(expected), code);
    assert.ok(doc.querySelector('.block_moodlebot_error'), 'error styling applied');
    assert.strictEqual(doc.querySelector('textarea').disabled, false);
  }
});

test('network failure / invalid JSON shows the "unavailable" message and recovers', async () => {
  const { doc } = setup(() => new Error('boom'));
  await tick(); type(doc, 'q'); clickSend(doc); await tick();
  assert.ok(logText(doc).includes('UNAVAILABLE_ERR'));
  assert.strictEqual(doc.querySelector('.block_moodlebot_send').disabled, false);
});

test('feedback: thumbs-up posts rating=1 once and locks both buttons', async () => {
  const { doc, calls } = setup(f => (f.action === 'chat'
    ? { ok: true, answer: 'a', sources: [], session_id: 's1234567', interaction_id: 77 } : { ok: true }));
  await tick(); type(doc, 'q'); clickSend(doc); await tick();
  const [up, down] = doc.querySelectorAll('.block_moodlebot_feedback button');
  up.click(); await tick();
  const fb = calls.filter(c => c.fields.action === 'feedback');
  assert.strictEqual(fb.length, 1);
  assert.deepStrictEqual([fb[0].fields.interactionid, fb[0].fields.rating], ['77', '1']);
  assert.ok(up.disabled && down.disabled);
  assert.ok(doc.querySelector('.block_moodlebot_thanks').textContent.includes('Thanks'));
});

test('history is restored after a page reload, including a previous rating', async () => {
  const { doc } = setup(f => ({ ok: true, messages: [
    { interaction_id: 1, question: 'Q one', answer: 'A one', sources: ['x/y.txt'], rating: 1 },
    { interaction_id: 2, question: 'Q two', answer: 'A two', sources: [], rating: null }] }), 'sess9999');
  await tick();
  const t = logText(doc);
  ['Q one', 'A one', 'Q two', 'A two', 'x/y.txt'].forEach(s => assert.ok(t.includes(s), s));
  const first = doc.querySelectorAll('.block_moodlebot_feedback')[0].querySelectorAll('button');
  assert.ok(first[0].disabled, 'earlier rating is shown as locked');
});

test('unknown/expired stored session falls back to a clean welcome', async () => {
  const { doc, w } = setup(() => ({ ok: true, messages: [] }), 'stale1234');
  await tick();
  assert.ok(logText(doc).includes(STRINGS.welcome));
  assert.strictEqual(w.sessionStorage.getItem('moodlebot_session_42_7'), null);
});

test('New chat clears the log and the stored session', async () => {
  const { doc, w } = setup(() => ({ ok: true, answer: 'a', sources: [], session_id: 's1234567', interaction_id: 1 }));
  await tick(); type(doc, 'q'); clickSend(doc); await tick();
  doc.querySelector('.block_moodlebot_new').click();
  assert.strictEqual(w.sessionStorage.getItem('moodlebot_session_42_7'), null);
  assert.ok(!logText(doc).includes('q'.repeat(1) + '\n') && logText(doc).trim() === STRINGS.welcome);
});

test('Enter sends, Shift+Enter does not; empty input and double-submit are ignored', async () => {
  let n = 0;
  const { doc, w } = setup(() => { n++; return { ok: true, answer: 'a', sources: [], session_id: 's1234567', interaction_id: n }; });
  await tick();
  clickSend(doc); await tick();
  assert.strictEqual(n, 0, 'empty input not sent');
  const ta = doc.querySelector('textarea');
  type(doc, 'one');
  ta.dispatchEvent(new w.KeyboardEvent('keydown', { key: 'Enter', shiftKey: true, bubbles: true }));
  await tick(); assert.strictEqual(n, 0, 'Shift+Enter does not send');
  ta.dispatchEvent(new w.KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
  clickSend(doc); // second submit while busy
  await tick(); assert.strictEqual(n, 1, 'only one request while busy');
});

test('initialising twice does not duplicate the UI', async () => {
  const { doc, w } = setup(() => ({ ok: true }));
  await tick(); w.eval(SCRIPT); await tick();
  assert.strictEqual(doc.querySelectorAll('textarea').length, 1);
});

(async () => {
  let failed = 0;
  for (const [name, fn] of tests) {
    try { await fn(); console.log('  ok   ' + name); }
    catch (e) { failed++; console.log('  FAIL ' + name + '\n       ' + (e.message || e)); }
  }
  console.log(`\n${tests.length - failed}/${tests.length} passed`);
  process.exit(failed ? 1 : 0);
})();
