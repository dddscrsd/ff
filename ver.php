<?php
// ver.php
header('Content-Type: application/json');

// --- НАСТРОЙКИ (замени на свои значения) ---
$version = '1.69.1'; // то, что было в переменной version
$loginDomain = '';   // если пустой — считаем, что не используем домен
$localIp = '';       // тут нужно подставить реальный локальный IP сервера
$loginServerUrlBase = 'http://127.0.0.1:3000'; // пример; адаптируй под свой сервер

// Получаем IP клиента (как x-forwarded-for или ip)
$requestIp = $_SERVER['HTTP_X_FORWARDED_FOR'] ?? $_SERVER['REMOTE_ADDR'] ?? '0.0.0.0';

// Формируем ответ в точности как в Node.js
$data = [
    'appstore_url' => 'https://play.google.com/store/apps/details?id=com.dts.freefireth',
    'billboard_msg' => '',
    'cdn_url' => 'https://dl.cdn.freefiremobile.com/live/ABHotUpdates/',
    'client_ip' => $requestIp,
    'code' => 0,
    'country_code' => 'BR',
    'force_to_restart_app' => false,
    'gdpr_version' => 2,
    'is_firewall_open' => false,
    'is_review_server' => false,
    'is_server_open' => true,
    'maintenance_announcement' => '',
    'maintenance_region' => '',
    'remote_option_version' => 'optionallocres:26|optionalclothres:282|optionalfullscreencgres:19|optionalludores:19|optionalmap1res:194|optionalmap2res:36|optionalmap4res:19|optionalmapres:17|optionalpetres:17|optionalrushb:38|optionalrushingpetsres:61|optionalvoiceres:147|optionalwerewolves:48',
    'remote_version' => $version,
    'server_url' => $loginServerUrlBase, // в Node.js там была функция loginServerUrl(localIp) — замени на нужную логику
];

echo json_encode($data, JSON_UNESCAPED_SLASHES | JSON_PRETTY_PRINT);
exit;
