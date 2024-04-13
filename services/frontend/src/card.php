<?php


if (empty($_GET['id'])) {
    http_response_code(404);
    header('Location: /index.php');
    exit();
}

$conn = new mysqli('mysql', 'root', 'ROOT', 'dbmoc');

if ($result = $conn->query("SELECT * FROM `upload` WHERE `id` = {$_GET['id']}")) {
    foreach ($result as $row) {
        $class = $row['class'];
        $description = $row['description'];
        $imgs = json_decode($row['result_imgs']);
        $startDate = $row['start_date'];
        $endDate = $row['end_date'];
        $loadImg = $row['load_img'];
        $isProcessed = $row['is_processed'];
    }
} else {
    http_response_code(404);
    header('Location: /index.php');
    exit();
}
?>


<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Title</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-EVSTQN3/azprG1Anm3QDgpJLIm9Nao0Yz1ztcQTwFspd3yD65VohhpuuCOmLASjC" crossorigin="anonymous">
</head>
<body>
<style>
    svg{
        vertical-align: unset !important;
    }
    .hidden {
        display: none !important;
    }
</style>
<header class="p-3 mb-3 border-bottom">
    <div class="container">
        <div class="d-flex flex-wrap align-items-center" style="justify-content: space-between">
            <a href="/index.php" class="d-flex align-items-center mb-2 mb-lg-0 text-dark text-decoration-none">
                <img src="/MINCULT_RUS_RGB.jpg" alt="" width="125" height="100">
            </a>
            <div class="dropdown text-end">
                <a href="/index.php" class="d-block link-dark text-decoration-none dropdown-toggle" id="dropdownUser1" data-bs-toggle="dropdown" aria-expanded="false">
                    <ion-icon name="contact" size="large"></ion-icon>
                </a>
                <ul class="dropdown-menu text-small" aria-labelledby="dropdownUser1">
                    <li><a class="dropdown-item" href="/index.php">Все фото</a></li>
                </ul>
            </div>
        </div>
    </div>
</header>
<section style="min-height: 100vh" class="container">
    <?php if (!$isProcessed) {?>
        <div class="alert alert-danger">
            Фото ещё обрабатывается!
        </div>
    <?php } else { ?>
    <div class="d-flex" style="justify-content: space-between;
    gap: 10%; margin-bottom: 5%">
        <img src="/user_upload_img/<?=$loadImg?>" class="img-thumbnail" id="uploadImg" alt="" style="max-width: 50%">
        <div class="selectImgs">
            <img src="<?= $imgs[0] ?>" class="img-thumbnail" id="selectImg" alt="">
            <div class="form-group" style="width: 100%">
                <label for="exampleFormControlSelect2">Выбрать похожие фото</label>
                <select class="form-control" id="exampleFormControlSelect2">
                    <optgroup label="Релевантные">
                    <?php foreach ($imgs as $key => $img): ?>
                        <?php if ($key <= 4): ?>
                            <option data-selector="<?=$img?>">Картинка <?=++$key?></option>
                        <?php endif; ?>
                    <?php endforeach; ?>
                    </optgroup>
                    <optgroup label="Менее релевантные">
                    <?php foreach ($imgs as $key => $img): ?>
                        <?php if ($key > 4): ?>
                            <option data-selector="<?=$img?>">Картинка <?=++$key?></option>
                        <?php endif; ?>
                    <?php endforeach; ?>
                    </optgroup>
                </select>
            </div>
        </div>

    </div>
    <div class="d-flex" style="justify-content: space-between; flex-direction: column; gap: 10%;">
        <div style="width: 300px;">
            <p class="badge bg-dark">Дата начала обработки: <?= $startDate ?? 'Отсутствует' ?></p>
            <p class="badge bg-dark">Дата окончания обработки: <?= $endDate ?? 'Отсутствует' ?></p>
        </div>
        <div class="form-group" style="    margin-bottom: 3%">
            <label for="title">Класс</label>
            <input class="form-control form-control-lg" type="text" value="<?=$class?>" id="title" disabled>
        </div>
        <form action="/change_description.php" method="POST">
            <input id="id" hidden="" name="id" value="<?=$_GET['id']?>">
            <div class="form-group" style="margin-bottom: 3%">
                <div class="edit-desc" style="display: flex; justify-content: space-between">
                    <label for="description">Описание</label>
                    <div style="border: 1px solid #ddd; padding: 5px; border-radius: 6px; cursor: pointer;" id="pencil-edit"><ion-icon name="create"></ion-icon></div>
                </div>
                <p id="descField"><?=$description?></p>

                <textarea class="form-control form-control-lg hidden" placeholder="Описание" id="description" name="description"><?=$description?></textarea>
            </div>
            <button class="btn btn-dark hidden" id="edit-btn" type="submit">Изменить описание</button>
        </form>
    </div>
    <?php } ?>
    <script>
        let select = document.querySelector('#exampleFormControlSelect2')
            select.onchange = (e) => {
                document.querySelector('#selectImg').src = e.target[e.target.selectedIndex].dataset.selector;
                document.querySelector('#selectImg').classList.remove('hidden');
        }
        let edit = document.querySelector('#pencil-edit')
        edit.onclick = () => {
            document.querySelector('#description').classList.toggle('hidden')
            document.querySelector('#descField').classList.toggle('hidden')

            document.querySelector('#edit-btn').classList.toggle('hidden')
        }

    </script>
</section>

<footer class="bg-body-tertiary text-center" style="margin-top: 10%">
    <div class="text-center p-3" style="background-color: rgba(0, 0, 0, 0.05);">
        2024 НейрON
    </div>
</footer>
<script src="https://unpkg.com/ionicons@4.1.2/dist/ionicons.js"></script>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/js/bootstrap.bundle.min.js" integrity="sha384-MrcW6ZMFYlzcLA8Nl+NtUVF0sA7MsXsP1UyJoMp4YLEuNSfAP+JcXn/tWtIaxVXM" crossorigin="anonymous"></script>
</body>
</html>