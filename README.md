# <p align="center"> ЦИФРОВОЙ ПРОРЫВ: СЕЗОН ИИ </p>
# <p align="center"> ПОИСК МУЗЕЙНЫХ ПРЕДМЕТОВ </p>
<p align="center">
<img width="800" height="600" alt="Заставка" src="https://github.com/VoLuIcHiK/museum-search/assets/90902903/fb0e265e-88e1-445c-ae0b-328e37a29b54">
</p>



*Состав команды "нейрON"*   
*Чиженко Леон (https://github.com/Leon200211) - Fullstack-разработчик*    
*Сергей Куликов (https://github.com/MrMarvel) - Backend-разработчик/ML-engineer*  
*Карпов Даниил (https://github.com/Free4ky) - ML-engineer/MLOps*  
*Валуева Анастасия (https://github.com/VoLuIcHiK) - Team Lead/Designer/ML-engineer*   
*Козлов Михаил (https://github.com/Borntowarn) - ML-engineer/ML
Ops*  


## Оглавление
1. [Задание](#1)
2. [Решение](#2)
3. [Результат разработки](#3)
4. [Уникальность нашего решения](#5)
5. [Стек](#6)
6. [Развертывание и тестировани](#7)
7. [Ссылки](#9)

## <a name="1"> Задание </a>

На основе базы данных с изображениями музейных предметов, внесенных в Государственный каталог Музейного фонда Российской Федерации, с применением технологий машинного зрения необходимо создать MVP в виде программного модуля поиска музейных предметов по заданному изображению. В целях повышения качества данных и стандартизации описания предлагается разработать функционал, позволяющий при внесении в базу нового музейного предмета найти похожие предметы, уже внесенные в каталог для использования их описания в качестве образца.

## <a name="2">Решение </a>

Ниже представлен алгоритм работы ML-части нашего приложения, а также взаимодействие RabbitMQ, обработчика и модели: 
<p align="center">
<img width="864" alt="модель" src="https://github.com/VoLuIcHiK/museum-search/assets/90902903/18db9215-c7e0-4a95-b0d5-6a6de133da40">
</p>


Как видно из схемы, обработчик (в данном случае один) постоянно отслеживает появление новой фотографии во входной очереди (input). Очереди (input, output_web и output_bot) были реализованы с помощью сервиса RabbitMQ. Как только обработчик обнаруживает новое изображение - он отправляет данные в модель, которая развернута на Triton Server. С помощью модели Blip2 T5 и алгоритмов постобработки и предобработки извлекаются эмбеддинги из исходных изображений, затем производится поиск наиболее похожих изображений и классификация. Затем в выходную очередь помещаются класс загруженного изображения и его описание, а также топ 10 похожих изображений, далее полученная информация отправляется либо на веб-сайт пользователю, либо в телеграмм бот.

Все параметры сервиса масштабируемы:
- Скорость обработки можно увеличить путем добавления дополнительных экземпляров обработчиков и моделей (это один из параметров запуска).
- Количество хранимых эмбеддингов можно увеличить благодаря линейному масштабированию базы данных.

Использование Triton Server повышает эффективность работы GPU и делает вывод намного экономически эффективнее. На сервере входящие запросы упаковываются в пакеты и отправляются для вывода. Таким образом, пакетная обработка позволяет эффективнее использовать ресурсы GPU.
Для ускорения работы модели был использован TensorRT, который позволил увеличить скорость обработки моделью до 40 раз быстрее чем на CPU и до 5 раз быстрее чем обычный запуск на GPU!


## <a name="3">Результат разработки </a>

В ходе решения поставленной задачи нам удалось реализовать *работающий* прототип со следующими компонентами:
1. Для удобства рабоыт пользователя с программы был сделан сайт и бот в телеграмме;
2. Векторная база данных Milvus, где хранятся эмбеддинги изображений;
3. Сконвертированная в TensorRT модель;
4. Очереди RabbitMQ для асинхронной обработки;
5. Triton Server, на котором развернута модель;
6. Обработчики - связующее звено между моделью и очередями.


## <a name="5">Уникальность нашего решения </a>
Уникальность нашего решения заключается в сочетание векторной базы данных (Milvus) и микросервисной архитектуры (RabbitMQ+Triton), а также высокой точности классификации и поиска похожих объектов. Нам удалось реализовать быстрое, точное и надежное решение, при этом сделав его удобным в использовании как через компьютер (веб-сайт), так и через смартфон (бот в телеграмме). Наша программа дает возможность работать с миллиардами изображений.


## <a name="6">Стек </a>
<div>
  <img src="https://github.com/devicons/devicon/blob/master/icons/python/python-original-wordmark.svg" title="Python" alt="Puthon" width="40" height="40"/>&nbsp;
  <img src="https://github.com/devicons/devicon/blob/master/icons/css3/css3-plain-wordmark.svg" title="css" alt="css" width="40" height="40"/>&nbsp;
  <img src="https://github.com/devicons/devicon/blob/master/icons/javascript/javascript-original.svg" title="js" alt="js" width="40" height="40"/>&nbsp;
  <img src="https://github.com/devicons/devicon/blob/master/icons/html5/html5-original-wordmark.svg" title="html" alt="html" width="40" height="40"/>&nbsp;
  <img src="https://github.com/devicons/devicon/blob/master/icons/php/php-original.svg" title="php" alt="php" width="40" height="40"/>&nbsp;
  <img src="https://github.com/devicons/devicon/blob/master/icons/docker/docker-original-wordmark.svg" title="docker" alt="docker" width="40" height="40"/>&nbsp;
  <img src="https://github.com/devicons/devicon/blob/master/icons/mysql/mysql-original.svg" title="mysql" alt="mysqlr" width="40" height="40"/>&nbsp;
  <img src="https://github.com/leungwensen/svg-icon/blob/master/dist/svg/logos/rabbitmq.svg" title="RabbitMQ" alt="RabbitMQ" width="40" height="40"/>&nbsp;
  <img src="https://github.com/vinceliuice/Tela-icon-theme/blob/master/src/scalable/apps/nvidia.svg" title="Triton" alt="Triton" width="40" height="40"/>&nbsp;

## <a name="7">Развертывание и тестирование </a>

 

## <a name="9">Ссылки</a>
- [Гугл диск с материалами](https://drive.google.com/drive/folders/1UwCNLUYw1t6u2DDVyUr7FXumXBfqObfm?usp=sharing)


