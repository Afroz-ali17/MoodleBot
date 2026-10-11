<?php
// This file is part of MoodleBot — an LLM-driven RAG chatbot block for Moodle.

/**
 * Admin settings: where the MoodleBot backend lives and the shared secret.
 *
 * @package    block_moodlebot
 */

defined('MOODLE_INTERNAL') || die();

if ($ADMIN->fulltree) {
    // PARAM_RAW_TRIMMED rather than PARAM_URL: Docker hostnames such as
    // "host.docker.internal" or "moodlebot-api" can be rejected by PARAM_URL. The URL is
    // validated in locallib.php before use.
    $settings->add(new admin_setting_configtext(
        'block_moodlebot/backendurl',
        get_string('backendurl', 'block_moodlebot'),
        get_string('backendurl_desc', 'block_moodlebot'),
        'http://host.docker.internal:8000',
        PARAM_RAW_TRIMMED
    ));

    $settings->add(new admin_setting_configpasswordunmask(
        'block_moodlebot/apikey',
        get_string('apikey', 'block_moodlebot'),
        get_string('apikey_desc', 'block_moodlebot'),
        ''
    ));

    $settings->add(new admin_setting_configtext(
        'block_moodlebot/timeout',
        get_string('timeout', 'block_moodlebot'),
        get_string('timeout_desc', 'block_moodlebot'),
        45,
        PARAM_INT
    ));
}
