<?php
// This file is part of MoodleBot — an LLM-driven RAG chatbot block for Moodle.

/**
 * MoodleBot block: renders the chat widget inside a course page.
 *
 * The block itself only outputs an empty container plus configuration in
 * data-* attributes. chat.js builds the interface and talks to ajax.php, which
 * authenticates the user and forwards the question to the backend.
 *
 * @package    block_moodlebot
 * @copyright  2026 RGMCET CSE (AI&ML) final year project team
 * @license    http://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

defined('MOODLE_INTERNAL') || die();

/**
 * Block class.
 */
class block_moodlebot extends block_base {

    /**
     * Sets the block title.
     */
    public function init() {
        $this->title = get_string('pluginname', 'block_moodlebot');
    }

    /**
     * Only offered on course pages.
     *
     * @return array
     */
    public function applicable_formats() {
        return ['course-view' => true, 'site' => false, 'my' => false];
    }

    /**
     * The block has admin settings (settings.php).
     *
     * @return bool
     */
    public function has_config() {
        return true;
    }

    /**
     * One chatbot per course is enough.
     *
     * @return bool
     */
    public function instance_allow_multiple() {
        return false;
    }

    /**
     * Builds the block content.
     *
     * @return stdClass
     */
    public function get_content() {
        global $COURSE, $USER, $PAGE;

        if ($this->content !== null) {
            return $this->content;
        }

        $this->content = new stdClass();
        $this->content->text = '';
        $this->content->footer = '';

        // Only people with a role in this course (FR-10).
        $context = context_course::instance($COURSE->id);
        if (!has_capability('block/moodlebot:use', $context)) {
            return $this->content;
        }

        if (empty(get_config('block_moodlebot', 'backendurl'))) {
            $this->content->text = html_writer::div(
                get_string('notconfigured', 'block_moodlebot'),
                'alert alert-warning'
            );
            return $this->content;
        }

        $keys = [
            'welcome', 'placeholder', 'send', 'thinking', 'sources', 'helpful', 'nothelpful',
            'thanks', 'disclaimer', 'newchat', 'error_generic', 'error_unavailable', 'error_ratelimit',
        ];
        $strings = [];
        foreach ($keys as $key) {
            $strings[$key] = get_string($key, 'block_moodlebot');
        }

        $this->content->text = html_writer::div('', 'block_moodlebot_chat', [
            'data-endpoint' => (new moodle_url('/blocks/moodlebot/ajax.php'))->out(false),
            'data-sesskey' => sesskey(),
            'data-courseid' => $COURSE->id,
            'data-userid' => $USER->id,
            'data-strings' => json_encode($strings),
        ]);

        $PAGE->requires->js(new moodle_url('/blocks/moodlebot/chat.js'));

        return $this->content;
    }
}
