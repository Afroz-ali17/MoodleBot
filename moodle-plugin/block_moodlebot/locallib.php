<?php
// This file is part of MoodleBot — an LLM-driven RAG chatbot block for Moodle.

/**
 * Helper functions for block_moodlebot.
 *
 * Plain PHP cURL is used on purpose instead of Moodle's \curl wrapper: Moodle
 * blocks requests to private/internal addresses by default (curlsecurityblockedhosts),
 * which includes the Docker network and localhost where the backend normally lives.
 * The URL is set by a site administrator, never by a user, so this is safe.
 *
 * @package    block_moodlebot
 */

defined('MOODLE_INTERNAL') || die();

/**
 * Calls the MoodleBot backend.
 *
 * @param string $method GET or POST.
 * @param string $path Path starting with "/", e.g. "/chat".
 * @param array|null $payload JSON body for POST requests.
 * @return array [int http status, array decoded JSON body]. Status 0 means the
 *               backend could not be reached at all.
 */
function block_moodlebot_backend_request(string $method, string $path, ?array $payload = null): array {
    $base = rtrim((string) get_config('block_moodlebot', 'backendurl'), '/');
    $scheme = parse_url($base, PHP_URL_SCHEME);
    if (!filter_var($base, FILTER_VALIDATE_URL) || !in_array($scheme, ['http', 'https'], true)) {
        return [0, ['detail' => 'Backend URL is not configured correctly']];
    }

    $timeout = (int) get_config('block_moodlebot', 'timeout');
    if ($timeout < 5) {
        $timeout = 45;
    }

    $headers = ['Accept: application/json'];
    $apikey = (string) get_config('block_moodlebot', 'apikey');
    if ($apikey !== '') {
        $headers[] = 'X-API-Key: ' . $apikey;
    }

    $ch = curl_init($base . $path);
    $options = [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_CONNECTTIMEOUT => 5,
        CURLOPT_TIMEOUT => $timeout,
    ];
    if ($method === 'POST') {
        $headers[] = 'Content-Type: application/json';
        $options[CURLOPT_POST] = true;
        $options[CURLOPT_POSTFIELDS] = json_encode($payload ?? []);
    }
    $options[CURLOPT_HTTPHEADER] = $headers;
    curl_setopt_array($ch, $options);

    $raw = curl_exec($ch);
    $status = (int) curl_getinfo($ch, CURLINFO_RESPONSE_CODE);
    $error = curl_errno($ch) ? curl_error($ch) : '';
    curl_close($ch);

    if ($raw === false) {
        return [0, ['detail' => 'Backend unreachable: ' . $error]];
    }
    $decoded = json_decode($raw, true);
    if (!is_array($decoded)) {
        return [$status ?: 502, ['detail' => 'Backend returned a non-JSON response']];
    }
    return [$status, $decoded];
}

/**
 * Sends a JSON response and stops.
 *
 * @param int $status HTTP status code.
 * @param array $data Response body.
 */
function block_moodlebot_respond(int $status, array $data): void {
    http_response_code($status);
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode($data);
    die();
}
