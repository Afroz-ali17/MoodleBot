<?php
// This file is part of MoodleBot — an LLM-driven RAG chatbot block for Moodle.

namespace block_moodlebot\privacy;

use core_privacy\local\metadata\collection;

/**
 * Privacy provider. MoodleBot stores nothing in Moodle's database, but it does
 * send the student's question to an external backend (and from there to an LLM
 * provider), which must be declared.
 *
 * @package    block_moodlebot
 */
class provider implements \core_privacy\local\metadata\provider {

    /**
     * Describe the data sent to the external MoodleBot backend.
     *
     * @param collection $collection The collection to add metadata to.
     * @return collection The updated collection.
     */
    public static function get_metadata(collection $collection): collection {
        $collection->add_external_location_link('moodlebot_backend', [
            'userid' => 'privacy:metadata:backend:userid',
            'courseid' => 'privacy:metadata:backend:courseid',
            'question' => 'privacy:metadata:backend:question',
        ], 'privacy:metadata:backend');
        return $collection;
    }
}
