<?php
// This file is part of MoodleBot — an LLM-driven RAG chatbot block for Moodle.

/**
 * Version metadata for block_moodlebot.
 *
 * @package    block_moodlebot
 * @copyright  2026 RGMCET CSE (AI&ML) final year project team
 * @license    http://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

defined('MOODLE_INTERNAL') || die();

$plugin->component = 'block_moodlebot';
$plugin->version   = 2026101100;
$plugin->requires  = 2022112800;   // Moodle 4.1 or later.
$plugin->maturity  = MATURITY_BETA;
$plugin->release   = '0.2.0';
