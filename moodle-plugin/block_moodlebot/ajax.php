<?php
// This file is part of MoodleBot — an LLM-driven RAG chatbot block for Moodle.

/**
 * AJAX endpoint used by chat.js.
 *
 * Flow:  browser  ->  this script (Moodle login + sesskey + capability checked)
 *                 ->  MoodleBot backend (shared secret in X-API-Key)
 *
 * The browser therefore never sees the backend address or API key, and the
 * student id sent to the backend always comes from the logged-in Moodle session,
 * never from the request.
 *
 * Supported actions: chat, feedback, history.
 *
 * @package    block_moodlebot
 * @copyright  2026 RGMCET CSE (AI&ML) final year project team
 * @license    http://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

define('AJAX_SCRIPT', true);

require_once(__DIR__ . '/../../config.php');
require_once(__DIR__ . '/locallib.php');

$courseid = required_param('courseid', PARAM_INT);
$action = required_param('action', PARAM_ALPHA);

$course = get_course($courseid);
require_login($course, false);
require_sesskey();
require_capability('block/moodlebot:use', context_course::instance($course->id));

// The LLM can take several seconds. Release the Moodle session lock so the
// student's other page loads are not blocked while we wait.
\core\session\manager::write_close();

$studentid = (string) $USER->id;
$session = optional_param('session', '', PARAM_ALPHANUMEXT);

switch ($action) {
    case 'chat':
        $question = trim(optional_param('question', '', PARAM_TEXT));
        $question = core_text::substr($question, 0, 1000);
        if ($question === '') {
            block_moodlebot_respond(400, ['ok' => false, 'code' => 'error', 'status' => 400]);
        }
        $payload = [
            'student_id' => $studentid,
            'question' => $question,
            'course_id' => (string) $course->id,
        ];
        if ($session !== '') {
            $payload['session_id'] = $session;
        }
        [$status, $data] = block_moodlebot_backend_request('POST', '/chat', $payload);
        break;

    case 'feedback':
        $payload = [
            'student_id' => $studentid,
            'interaction_id' => required_param('interactionid', PARAM_INT),
            'rating' => required_param('rating', PARAM_INT),
        ];
        [$status, $data] = block_moodlebot_backend_request('POST', '/feedback', $payload);
        break;

    case 'history':
        if ($session === '') {
            block_moodlebot_respond(200, ['ok' => true, 'messages' => []]);
        }
        $path = '/history/' . rawurlencode($session) . '?student_id=' . rawurlencode($studentid);
        [$status, $data] = block_moodlebot_backend_request('GET', $path);
        break;

    default:
        block_moodlebot_respond(400, ['ok' => false, 'code' => 'error', 'status' => 400]);
}

if ($status >= 200 && $status < 300) {
    block_moodlebot_respond(200, ['ok' => true] + $data);
}

// Never show backend internals (stack traces, provider errors) to students;
// log them for the administrator and return a short code the widget translates.
debugging('block_moodlebot backend error ' . $status . ': ' . json_encode($data), DEBUG_DEVELOPER);
error_log('block_moodlebot: backend returned ' . $status . ' ' . json_encode($data));

$code = 'error';
if ($status === 429) {
    $code = 'ratelimit';
} else if ($status === 0 || $status >= 500) {
    $code = 'unavailable';
}
block_moodlebot_respond($status >= 400 ? $status : 502, ['ok' => false, 'code' => $code, 'status' => $status]);
