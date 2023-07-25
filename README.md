# Сервис по замене ссылок и составлению заявлению на выдачу сим-карты
В данном проекте содержится два сервиса
1. Сервис по замене ссылок в рассылках - Для быстрого составления маркетинговых писем. На вход подается HTML-файл письма.
2. Сервис для составления заявления на выдачу корпоративной сим-карты. На вход подается номер тикета из JIRA.

## Настройка сервере

Подключитесь к своему серверу и подготовьте его к установке пакетов Python:
```shell
apt update
apt install python3-pip
pip3 install virtualenv
```

Скачайте на сервер код проекта и установите его зависимости:
```shell
cd /opt/
git clone git@github.com:name_repository
cd /opt/name_repository/
virtualenv --python=python3 venv
source venv/bin/activate
pip install -r requirements.txt
```

## Переменные окружения

Настроить бэкенд: создать файл .env в каталоге проекта со следующими настройками:

```
DEBUG=False
YOURLS_TOKEN='12343432'
SECRET_KEY='django-insecure-lyo7@7z437*is81v24234'
JIRA_TOKEN=ODYxMTcgdfg345345345
JIRA_LOGIN=service
JIRA_PASSWORD=password123
STOP_LINKS=['http://www.w3.org/TR/REC-html40', 'http://schemas.microsoft.com/office/2004/12/omml', 'https://l.ertelecom.ru/vkdigest', 'https://l.ertelecom.ru/tgdigest','https://l.ertelecom.ru/220415digestrutube']
ALLOWED_HOSTS=['.localhost', '127.0.0.1', '[::1]']
```

- DEBUG — дебаг-режим. Поставьте False.
- YOURLS_TOKEN - Токен от сервиса по сокращению ссылок
- SECRET_KEY — секретный ключ проекта. Он отвечает за шифрование на сайте. Например, им зашифрованы все пароли на вашем сайте.
- JIRA_TOKEN - Токен от сервиса JIRA
- JIRA_LOGIN - Логин сервисного аккаунта
- JIRA_PASSWORD - Пароль сервисного аккаунта
- STOP_LINKS - Список ссылок, которые не нужно сокращать
- ALLOWED_HOSTS — [см. документацию Django](https://docs.djangoproject.com/en/3.1/ref/settings/#allowed-hosts)
- YANDEX_GEO_KEY — ключ для определения геопозиции (Широты и долготы) по заданному адресу.