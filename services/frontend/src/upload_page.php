<!DOCTYPE html>
<html lang="en">
<head>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-EVSTQN3/azprG1Anm3QDgpJLIm9Nao0Yz1ztcQTwFspd3yD65VohhpuuCOmLASjC" crossorigin="anonymous">
    <meta charset="UTF-8">
    <title>Title</title>

    <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.7.1/jquery.min.js"></script>
</head>
<body style="min-height:100vh">
<style>
    svg{
        vertical-align: unset !important;
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
                    <ion-icon name="contact" size="large" class="upload-btn"></ion-icon>
                </a>
                <ul class="dropdown-menu text-small" aria-labelledby="dropdownUser1">
                    <li><a class="dropdown-item" href="/index.php">Все фото</a></li>
                </ul>
            </div>
        </div>
    </div>
</header>

<style>
    #FileUpload {
        display: flex;
        justify-content: flex-start;
    }
    .wrapper {
        margin: 30px 0;
        padding: 10px;
        box-shadow: 0 19px 38px rgba(0,0,0,0.30), 0 15px 12px rgba(0,0,0,0.22);
        border-radius: 10px;
        background-color: white;
    }
    /* === Upload Box === */
    .upload {
        margin: 10px;
        height: 85px;
        display: flex;
        justify-content: center;
        align-items: center;
        border-radius: 5px;
    }
    .upload p {
        margin-top: 12px;
        line-height: 0;
        font-size: 22px;
        color: #0c3214;
        letter-spacing: 1.5px;
    }
    .upload__button {
        background-color: #e6f5e9;
        border-radius: 10px;
        padding: 0px 8px 0px 10px;
    }
    .upload__button:hover {
        cursor: pointer;
        opacity: 0.8;
    }

    /* === Uploaded Files === */
    .uploaded {
        width: 375px;
        margin: 10px;
        padding: 5%;
        background-color: #e6f5e9;
        border-radius: 10px;
        display: flex;
        flex-direction: row;
        justify-content: flex-start;
        align-items: center;
    }
    .file {
        display: flex;
        flex-direction: column;
    }
    .file__name {
        display: flex;
        flex-direction: row;
        justify-content: space-between;
        align-items: baseline;
        width: 300px;
        line-height: 0;
        color: #0c3214;
        font-size: 18px;
        letter-spacing: 1.5px;
    }

    .hidden {
        display: none !important;
    }
</style>

<section style="min-height: 100vh" class="container">
    <div id="FileUpload">
        <div class="wrapper">
            <label for="filedrop" class="upload" style="cursor: pointer;">
                <ion-icon name="cloud-upload" style="font-size: 72px; color: grey">
            </label>
            <div class="uploaded uploaded--one hidden" id="hiddenbars">
                <ion-icon name="copy" size="large"></ion-icon>
                <div class="file">
                    <div class="file__name">
                        <p id="vidName" style="font-size: 12px;line-height: normal;">text</p>
                        <i class="fas fa-times"></i>
                    </div>
                    <div class="progress">
                        <div class="progress-bar bg-success progress-bar-striped progress-bar-animated" id="load-labels" style="width:100%">
                            <span id="queque"></span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <div class="d-flex" style="justify-content: space-between;
    gap: 10%; margin-bottom: 5%">
        <img src="" class="img-thumbnail hidden" id="uploadImg" alt="" style="max-width: 50%">
        <div class="selectImgs hidden">
            <img src="" class="img-thumbnail" id="selectImg" alt="">
            <div class="form-group" style="width: 100%">
                <label for="exampleFormControlSelect2">Выбрать похожие</label>
                <select class="form-control" id="exampleFormControlSelect2">
                    <optgroup label="релевантные" id="first_optgrup">
                    </optgroup>
                    <optgroup label="менее релевантные" id="second_optgrup">
                    </optgroup>
                </select>
            </div>
        </div>

    </div>
    <div class="d-flex" style="flex-direction: column;justify-content: space-between; gap: 10%;">

        <form class="d-flex" style="flex-direction: column; justify-content: space-around; gap: 10%; width: 100%" id="uploadForm">
            <div class="form-group" style="margin-bottom: 3%">
                <input type="file" name="" id="filedrop" class="hidden">
            </div>
            <button type="submit" class="btn btn-dark btn-upload">Отправить</button>
        </form>

        <div id="result_block" style="display: none;">
            <div style="width: 300px;">
                <p class="badge bg-dark">Дата начала обработки: <?= date('Y-m-d H:i:s') ?></p>
                <p class="badge bg-dark" id="end_date">Дата окончания обработки: <?= 'Отсутствует'; ?></p>
            </div>
            <div class="form-group" style="margin-bottom: 3%">
                <label for="class">Класс</label>
                <input class="form-control form-control-lg" type="text" placeholder="Название" id="class" disabled>
            </div>
            <form action="/change_description.php" method="POST">
                <input id="id_load" hidden="" name="id" value="">
                <div class="edit-desc" style="display: flex; justify-content: space-between">
                    <label for="description">Описание</label>
                    <div style="border: 1px solid #ddd; padding: 5px; border-radius: 6px; cursor: pointer;" id="pencil-edit"><ion-icon name="create"></ion-icon></div>
                </div>
                <p id="descField"></p>

                <textarea class="form-control form-control-lg hidden" placeholder="Описание" id="description" name="description"></textarea>
                <br>
                <button class="btn btn-dark hidden" id="edit-btn" type="submit">Изменить описание</button>
            </form>
        </div>

    </div>

</section>
<script>

    const uploadForm = document.querySelector('#uploadForm')
    const inpFile = document.querySelector('#filedrop')
    let elem = document.querySelector('.itemBar')
    let select = document.querySelector('#exampleFormControlSelect2')
    const rootDiv = document.querySelector('.container')
    let counter = 0;

    function ext(name) {
        var m = name.match(/\.([^.]+)$/)
        return m && m[1]
    }
    inpFile.onchange = (i) => {
        document.querySelector('.upload').classList.toggle('hidden')
        let img = document.querySelector('#uploadImg')
        img.classList.toggle('hidden')
        let fileReader = new FileReader();
        fileReader.onload = function(){
            img.src = fileReader.result;
        }

        fileReader.readAsDataURL(inpFile.files[0]);
        if(inpFile.files.length) {
            let fileName = inpFile.files[0].name
            var splittedFileName = ext(fileName)
            document.querySelector('#vidName').textContent = fileName
        }

        if (splittedFileName === 'jpg' || splittedFileName === 'png') {
            document.querySelector('#hiddenbars').classList.toggle('hidden')
            uploadForm.onsubmit = (e) => {
                e.preventDefault();
                const files = document.querySelector('[type=file]').files
                const formData = new FormData()
                formData.append('img', files[0])

                const xhr = new XMLHttpRequest()

                xhr.open('POST', '/upload_user_file.php')
                xhr.upload.addEventListener('progress', e => {
                    const percent = e.lengthComputable ? (e.loaded / e.total) * 100 : 0;
                    elem.style.width = percent.toFixed(2) + '%'
                    document.querySelector('#load-labels').textContent = percent.toFixed(2) + '%'
                })

                xhr.onload = () => {
                    document.querySelector('.btn-upload').style.display = 'none';
                    document.getElementById('queque').textContent = 'В ОБРАБОТКЕ';
                    let JSONobj = JSON.parse(xhr.response)
                    if (JSONobj.status == 'success') {
                        var xhr2 = new XMLHttpRequest()
                        var formdata2 = new FormData()
                        formdata2.append('id', JSONobj.id)

                        console.log(JSONobj.id);

                        var proccess = setInterval(() => {
                            xhr2.open('POST', '/check_user_load.php')
                            xhr2.send(formdata2)
                            xhr2.onload = () => {
                                let JSONobj2 = JSON.parse(xhr2.response)

                                if (JSONobj2.is_processed == 1) {
                                    if(JSONobj2.result_imgs !== undefined){
                                        let imgLinks = JSON.parse(JSONobj2.result_imgs)
                                        document.getElementById('selectImg').src = imgLinks[0];
                                        document.querySelector('.selectImgs').classList.remove('hidden')

                                        imgLinks.forEach((e) => {
                                            counter++;
                                            let option = document.createElement('option')
                                            option.textContent = 'Картинка ' + counter;
                                            option.dataset.selector = e

                                            if (counter < 6) {
                                                document.getElementById('first_optgrup').appendChild(option)
                                            } else {
                                                document.getElementById('second_optgrup').appendChild(option)
                                            }
                                        });
                                    }

                                    clearInterval(proccess)
                                    document.getElementById('FileUpload').style.display = 'none';
                                    document.getElementById('result_block').style.display = 'block';
                                    document.getElementById('id_load').value = JSONobj2.id;
                                    document.getElementById('class').value = JSONobj2.class;
                                    document.getElementById('description').textContent = JSONobj2.description;
                                    document.getElementById('descField').textContent = JSONobj2.description;
                                    document.getElementById('end_date').innerHTML = 'Дата окончания обработки ' + JSONobj2.end_date;
                                }
                            }
                        }, 2000)
                    }

                    let responseObj = xhr.response;
                    console.log(responseObj); // Привет, мир!
                }
                xhr.send(formData)

            }
        }
    }
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

<footer class="bg-body-tertiary text-center" style="margin-top: 10%">
    <div class="text-center p-3" style="background-color: rgba(0, 0, 0, 0.05);">
        2024 НейрON
    </div>
</footer>

<script src="https://unpkg.com/ionicons@4.1.2/dist/ionicons.js"></script>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/js/bootstrap.bundle.min.js" integrity="sha384-MrcW6ZMFYlzcLA8Nl+NtUVF0sA7MsXsP1UyJoMp4YLEuNSfAP+JcXn/tWtIaxVXM" crossorigin="anonymous"></script>
</body>
</html>