<?php

if (empty($_POST['id'])) {
    http_response_code(404);
    echo 'error';
    exit();
}

$conn = new mysqli('mysql', 'root', 'ROOT', 'dbmoc');

if ($result = $conn->query("SELECT * FROM `upload` WHERE `id` = {$_POST['id']}")) {
    foreach ($result as $row) {
        if ($row['is_processed'] == 0) {
            http_response_code(200);
            echo 'false';
            exit();
        }

        $result = [
            'id' => $_POST['id'],
            'start_date' => $row['start_date'],
            'end_date' => $row['end_date'],
            'class' => $row['class'],
            'description' => $row['description'],
            'result_imgs' => $row['result_imgs'],
            'is_processed' => 1,
        ];

        http_response_code(200);
        echo json_encode($result);
        exit();
    }
} else {
    http_response_code(404);
    echo 'error';
    exit();
}
