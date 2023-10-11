# Foodgram
Проект Foodgram является простой социальной сетью, где люди, зарегистировавшись на сайте, могут делиться своими рецептами. На сайте можно просматривать рецепты, создавать их, добавлять в избранное, список покупок, подписываться на автора, скачать список покупок. Ознакомиться с проектом можно на сайте https://pumpkin.hopto.org/

##### Для его запуска на локальном сервере необходимо:
HINT: описание инструкции для запуска с Linux, на котором установлен Docker
1) Склонировать репозиторий:
```
git clone https://github.com/Zhovtyak/foodgram-project-react.git
```
2) Перейти в директорию foodgram-project-react/infra/, создать файл .env. Например, с такими данными:
```
POSTGRES_USER=django_user
POSTGRES_PASSWORD=mysecretpassword
POSTGRES_DB=django
DB_HOST=db
DB_PORT=5432
SECRET_KEY=mysecretkey
DEBUG=False
ALLOWED_HOSTS=127.0.0.1,localhost
```
3) Провести установку контейнеров, и их совместный запуск, используя файл docker-compose.production.yml:
```
sudo docker compose -f docker-compose.production.yml up -d
```
4) Провести миграции в контейнере backend'a:
```
sudo docker compose -f docker-compose.production.yml exec backend python manage.py migrate
```
5) Собрать статику backend'a, передать её в volume статики для работы последовательными командами:
```
sudo docker compose -f docker-compose.production.yml exec backend python manage.py collectstatic
sudo docker compose -f docker-compose.production.yml exec backend cp -r /app/static/. /var/html/
```
6) Введя в браузере localhost:8000, можно оценить работу социальной сети

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

Автор проекта: Максим Жовтяк
Frontend сайта разработан и предоставлен компанией "Яндекс" в учебных целях
Для разработки backend'а использовались Django, REST API, Python, Docker
