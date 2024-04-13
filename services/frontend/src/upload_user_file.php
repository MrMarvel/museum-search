<?php

if (empty($_FILES['img']) || $_FILES['img']['size'] <= 0) {
    http_response_code(422);
    echo 'error';
    exit();
}

$imgExt = ['png', 'jpg', 'jpeg'];
$fileExtension = pathinfo($_FILES['img']['name'], PATHINFO_EXTENSION);

if (!in_array($fileExtension, $imgExt)) {
    http_response_code(422);
    echo 'error';
    exit();
}

while (true) {
    $fileName = rand() . '.' . $fileExtension;

    if (!file_exists('user_upload_img/' . $fileName)) {
        break;
    }
}

if (!move_uploaded_file($_FILES['img']['tmp_name'], 'user_upload_img/' . $fileName)) {
    http_response_code(422);
    echo 'error';
    exit();
}

$conn = new mysqli('mysql', 'root', 'ROOT', 'dbmoc');
$conn->query("INSERT INTO upload (load_img) VALUES ('{$fileName}')");

$uploadId = mysqli_insert_id($conn);

$curl = curl_init();
$aPost = array(
    'webhook_url' => 'default',
    'webhook_request_id' => $uploadId,
);
if ((version_compare(PHP_VERSION, '5.5') >= 0)) {
    $aPost['file'] = new \CURLFile('user_upload_img/' . $fileName);
    curl_setopt($curl, CURLOPT_SAFE_UPLOAD, true);
} else {
    $aPost['file'] = "@".'user_upload_img/' . $fileName;
}

curl_setopt($curl, CURLOPT_URL, "http://projectvoid.my.to:8102/upload");
//curl_setopt($curl, CURLOPT_URL, "https://webhook.site/434a337a-ff60-4e9e-94f4-ffe1b968d77b");

curl_setopt($curl, CURLOPT_TIMEOUT, 120);
curl_setopt($curl, CURLOPT_BUFFERSIZE, 128);
curl_setopt($curl, CURLOPT_POSTFIELDS, $aPost);
curl_setopt($curl, CURLOPT_RETURNTRANSFER, true);
curl_setopt($curl, CURLOPT_SSL_VERIFYPEER, 0);
curl_setopt($curl, CURLOPT_HEADER, 0);
curl_setopt($curl, CURLOPT_TIMEOUT_MS, 2000);
$sResponse = curl_exec($curl);

$result = [
    'id' => $uploadId,
    'status' => 'success',
];
http_response_code(200);
echo json_encode($result);
exit();