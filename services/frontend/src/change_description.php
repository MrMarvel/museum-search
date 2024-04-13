<?php

if (empty($_POST['id']) || empty($_POST['description'])) {
    http_response_code(404);
    header('Location: /index.php');
    exit();
}

if (!array_key_exists('description', $_POST)) {
    header('Location: /card.php?id=' . $_POST['id']);
    exit();
}

if (empty($_POST['description'])) {
    http_response_code(422);
    header('Location: /card.php?id=' . $_POST['id']);
    exit();
}

$conn = new mysqli('mysql', 'root', 'ROOT', 'dbmoc');

if ($result = $conn->query("SELECT * FROM `upload` WHERE `id` = {$_POST['id']}")) {
    $result = $conn->query("UPDATE `upload` SET `description` = '{$_POST['description']}' WHERE `upload`.`id` = {$_POST['id']};");

    if ($result) {
        http_response_code(200);
        header('Location: /card.php?id=' . $_POST['id']);
        exit();
    } else {
        http_response_code(422);
        header('Location: /card.php?id=' . $_POST['id']);
        exit();
    }
} else {
    http_response_code(404);
    header('Location: /index.php');
    exit();
}

exit();