<?php
// This file is part of MoodleBot — an LLM-driven RAG chatbot block for Moodle.

/**
 * English language strings for block_moodlebot.
 *
 * @package    block_moodlebot
 */

defined('MOODLE_INTERNAL') || die();

$string['pluginname'] = 'MoodleBot';
$string['moodlebot:addinstance'] = 'Add a new MoodleBot block';
$string['moodlebot:myaddinstance'] = 'Add a new MoodleBot block to the Dashboard';
$string['moodlebot:use'] = 'Chat with MoodleBot';

// Admin settings.
$string['backendurl'] = 'Backend URL';
$string['backendurl_desc'] = 'Address of the MoodleBot API as seen from the Moodle server, e.g. http://moodlebot-api:8000 (Docker network) or http://host.docker.internal:8000 (API running on the host).';
$string['apikey'] = 'Backend API key';
$string['apikey_desc'] = 'Shared secret. Must equal MOODLEBOT_API_KEY in the backend .env file.';
$string['timeout'] = 'Request timeout (seconds)';
$string['timeout_desc'] = 'How long Moodle waits for an answer before giving up. LLM answers usually take 2-10 seconds.';

// Chat widget.
$string['welcome'] = 'Hi! Ask me anything about this course. I answer from the course materials.';
$string['placeholder'] = 'Type your question…';
$string['send'] = 'Send';
$string['thinking'] = 'MoodleBot is thinking…';
$string['sources'] = 'Sources';
$string['helpful'] = 'Helpful';
$string['nothelpful'] = 'Not helpful';
$string['thanks'] = 'Thanks for the feedback!';
$string['disclaimer'] = 'AI-generated from course materials. Check important details with your teacher.';
$string['newchat'] = 'New chat';
$string['error_generic'] = 'Sorry, something went wrong. Please try again.';
$string['error_unavailable'] = 'MoodleBot is not available right now. Please try again later.';
$string['error_ratelimit'] = 'You are asking too quickly. Please wait a moment and try again.';
$string['notconfigured'] = 'MoodleBot has not been configured yet. Ask your site administrator to set the backend URL.';

// Privacy.
$string['privacy:metadata:backend'] = 'MoodleBot sends each question to an external MoodleBot service that retrieves course material and generates an answer using a large language model.';
$string['privacy:metadata:backend:userid'] = 'The Moodle user id (stored there only as a salted hash).';
$string['privacy:metadata:backend:courseid'] = 'The id of the course the question was asked in.';
$string['privacy:metadata:backend:question'] = 'The text of the question the user typed.';
