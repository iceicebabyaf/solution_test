# Quick Start

## Setup

Установить зависимости и браузер:

```bash
./setup.sh
```

Устанавливает Python пакеты, Playwright и Chromium. Проверяет ANTHROPIC_API_KEY.

Установить API ключ:

```bash
export ANTHROPIC_API_KEY='your-key-here'
```

## Тесты

Проверить настройки:

```bash
python test_setup.py
```

Проверяет импорты, API ключ, браузер, файлы, конфиг.

## Login Helper

Залогиниться на сайте (сохранит сессию для агента):

```bash
python login_helper.py
```

Открывает браузер, логинишься вручную, жмёшь Enter. Сессия сохранится в `.browser_session/`.

## Запуск

```bash
./run.sh
```

Проверяет venv и API ключ, запускает агента.
