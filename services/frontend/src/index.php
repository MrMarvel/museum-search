<!DOCTYPE html>
<html lang="en">
<head>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-EVSTQN3/azprG1Anm3QDgpJLIm9Nao0Yz1ztcQTwFspd3yD65VohhpuuCOmLASjC" crossorigin="anonymous">
    <meta charset="UTF-8">
    <title>Title</title>
</head>
<style>
    svg{
        vertical-align: unset !important;
    }
</style>

<body>
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
    <a class="btn btn-dark" href="/upload_page.php">Добавить</a>
    <br>
    <br>
    <div class="cards d-flex" style="flex-wrap: wrap;
    gap: 20px;">
    <?php
    $conn = new mysqli('mysql', 'root', 'ROOT', 'dbmoc');

    if ($result = $conn->query("SELECT * FROM `upload`;")) {
        foreach ($result as $row) {
            ?>
            <div class="card" style="width: 18rem;">
                <img src="/user_upload_img/<?=$row['load_img']?>" class="card-img-top" alt="...">
                <div class="card-body">
                    <h5 class="card-title"><?=$row['class']?></h5>
                    <p class="card-text"><?=$row['description']?></p>
                    <p class="card-text">Время начала: <?=$row['start_date']?></p>
                    <p class="card-text">Время завершения: <?=$row['end_date']?></p>
                    <a href="/card.php?id=<?=$row['id']?>" class="btn btn-primary">Открыть</a>
                </div>
            </div>
    <?php
        }
    }
    ?>
    </div>
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