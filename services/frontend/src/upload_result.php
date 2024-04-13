<?php

$data = json_decode(file_get_contents("php://input"), true);

if ($data['status'] !== 'success') {
    http_response_code(422);
    echo 'error';
    exit();
}

$conn = new mysqli('mysql', 'root', 'ROOT', 'dbmoc');

if ($result = $conn->query("SELECT * FROM `upload` WHERE `id` = {$data['data']['webhook_request_id']}")) {
    $resultImg = json_encode($data['data']['extras']['detection']['familiars']);
    $endDate = date("Y-m-d H:i:s");

    $result = $conn->query("UPDATE `upload` SET `description` = '{$data['data']['extras']['detection']['description']}',
                                            `class` = '{$data['data']['extras']['detection']['class_name']}',
                                            `is_processed` = 1 ,
                                            `end_date` = '{$endDate}',
                                            `result_imgs` = '{$resultImg}' 
                                   WHERE `upload`.`id` = {$data['data']['webhook_request_id']};"
    );

    if ($result) {
        http_response_code(200);
        exit();
    } else {
        http_response_code(422);
        echo 'false';
        exit();
    }
} else {
    http_response_code(404);
    echo 'error';
    exit();
}

exit();