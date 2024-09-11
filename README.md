# test-online-store
# Тестовый проект
# Интернет-магазин

## Установка и заполнение данными

В settings.py подключен MySQL backend.
Создать файл online_store/.env
В файле .env нужно прописать параметры подключения к базе данных.
Запустить миграции данных в БД.
`./online_store/manage.py migrate`

В файле .env нужно прописать ник и пароль для тестовых пользователей: клиента и менеджера

Заполнить таблицы тестовыми данными.
создать суперпользователя для админки
`./online_store/manage.py createsuperuser`
создать тестовые данные
`./online_store/manage.py create_test_objects`

## Запуск локального сервера

`./online_store/manage.py runserver`


## Админка

[http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

## Тесты

`./online_store/manage.py test online_store`

## Swagger

[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## Авторизация и доступ к запросам

Большинство запросов требуют авторизацию.
Необходимо отсылать в header Authorization токен пользователя в виде "Bearer token"
Для получения токена используйте
post /accounts/signin
Для регистрации нового пользователя используйте
post /accounts/signup
просмотр своего профиля
get /accounts/profile
изменение своего профиля
put /accounts/profile

Пользователи делятся на обычных и с правом менеджера.
Права менеджера добавляются пользователю в адvинке - permission manager


# Реализация ТЗ

## Вимоги до реалізації:
## API має підтримувати операції
1. отримання списку товарів
get /products
get /products/:pk
get /categories

2. фільтр товарів за категоріями, підкатегоріями
/products
параметры фильтрации в query string: category (список slug), subcategory (список slug), min_price, max_price
3. додавання товару
post /products
put /products/:pk
4. зміна ціни
post /products/:pk/price
5. старт акції (процент знижки)
post /products/action
post /products/action/disable
Хранится дата старта акции, скидка в процентах, флаг активности.
Используется последняя активная акция.
6. видалення товару
delete /products/:pk
товар не удаляется из базы, присваивается статус удалённого, товар не виден в запросах.
7. резервування товару
post /orders
список заказов
get /orders
get /orders/:pk
8. скасування резерву
delete /orders/:pk
заказ не удаляется, получает статус rejected
9. продажа товару
post /orders/payment
10. звіт про товари що були продані можливими фільтрами
get /orders/sold
фильтр по date_from, date_to, category, subcategory, product

Оплата заказа производится со счёта клиента.
Счёт пополняется менеджером или в админке или запросом
post /accounts/topup/account

