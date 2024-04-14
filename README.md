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
<img width="864" alt="модель" src="">
</p>


Как видно из схемы, обработчик (в данном случае один) постоянно отслеживает появление новой фотографии во входной очереди (input). Очереди (input и output) были реализованы с помощью сервиса RabbitMQ. Как только обработчик обнаруживает новое изображение - он отправляет данные в модель, которая развернута на Triton Server. А в выходную очередь помещаются класс загруженного изображения и его описание, а также топ 10 похожих изображений.

Все параметры сервиса масштабируемы, поэтому скорость обработки можно увеличить путем добавления дополнительных экземпляров обработчиков и моделей (это один из параметров запуска). 

Использование Triton Server повышает эффективность работы GPU и делает вывод намного экономически эффективнее. На сервере входящие запросы упаковываются в пакеты и отправляются для вывода. Таким образом, пакетная обработка позволяет эффективнее использовать ресурсы GPU.
Для ускорения работы модели был использован TensorRT, который позволил увеличить скорость обработки моделью до 40 раз быстрее чем на CPU и до 5 раз быстрее чем обычный запуск на GPU!


## <a name="3">Результат разработки </a>

В ходе решения поставленной задачи нам удалось реализовать *рабочий* прототип со следующими компонентами:
1.  Для удобства пользователя был сделать прогресс бар;
2. Сконвертированная в TensorRT модель;
3. Очереди RabbitMQ для асинхронной обработки;
4. Triton Server, на котором развернута модель;
5. Обработчики - связующее звено между моделью и очередями.


## <a name="5">Уникальность нашего решения </a>



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
- [Гугл диск с материалами]()


