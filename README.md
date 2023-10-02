# praktikum_new_diplom
Проект Foodgram является простой социальной сетью, где люди, зарегистировавшись на сайте, могут делиться своими рецептами. На сайте можно просматривать рецепты, создавать их, добавлять в избранное, список покупок, подписываться на автора, скачать список покупок. Данный проект создан мной для закрепления навыков работы с Docker, Django, REST API, Python. Ознакомиться с проектом можно на сайте https://pumpkin.hopto.org/


##### Для его запуска на локальном сервере необходимо:
HINT: описание инструкции для запуска с Linux, на котором установлен Docker
1) Склонировать репозиторий:
```
git clone https://github.com/Zhovtyak/foodgram-project-react.git
```
2) Перейти в директорию foodgram-project-react/infra/, провести установку контейнеров, и их совместный запуск, используя файл docker-compose.production.yml:
```
sudo docker compose -f docker-compose.production.yml up -d
```
3) Провести миграции в контейнере backend'a:
```
sudo docker compose -f docker-compose.production.yml exec backend python manage.py migrate
```
4) Собрать статику backend'a, передать её в volume статики для работы последовательными командами:
```
sudo docker compose -f docker-compose.production.yml exec backend python manage.py collectstatic
sudo docker compose -f docker-compose.production.yml exec backend cp -r /app/static/. /var/html/
```
5) Введя в браузере localhost:8000, можно оценить работу социальной сети

##### Примеры выполняемых к нему API-запросов
1. Получение всего списка рецептов (GET)
```
/api/recipes/
```
2. Получение информации об одном рецепте (GET)
```
/api/recipes/<number>/
```
3. Создать рецепт (POST)
```
/api/recipes/create
```
