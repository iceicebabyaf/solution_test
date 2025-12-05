# Autonomous Browser Agent

AI-агент для автоматизации браузера на базе Claude API и Playwright.

## Архитектура

Агент работает через supervisor-tools модель:
- **Supervisor** ([agent/supervisor.py](agent/supervisor.py)) - оркестрирует выполнение через Claude API
- **Tools** ([agent/tools.py](agent/tools.py)) - функции для взаимодействия с браузером

## Инструменты

### Навигация
- `goto_url(url)` - переход по URL
- `go_back()` - назад в истории браузера

### Извлечение контента
- `get_page_content()` - основной инструмент. Автоматически скроллит страницу, подгружает lazy content, возвращает структурированный текст.
- `take_screenshot()` - скриншот viewport в base64. Для CAPTCHA, сложных layout'ов, визуального анализа.

### Взаимодействие с элементами
- `find_element(description)` - поиск элемента на естественном языке (например, "кнопка логина", "поле поиска"). Возвращает CSS/XPath селектор.
- `click(selector)` - надежный клик. Поддерживает CSS, XPath, text-селекторы. Автопереключение на новые вкладки. Защита от опасных действий.
- `type_text(selector, text)` - очистка и ввод текста с задержками
- `press_key(key)` - нажатие клавиш  (типа esc, tab..)
- `scroll(direction)` - скролл страницы (down/up/to_element)
- `wait_for_element(selector)` - ожидание появления элемента (для async контента)
- `get_element_text(selector)` - извлечение текста из конкретного элемента

### Взаимодействие с пользователем
- `ask_human(question)` - пауза выполнения, запрос ввода от пользователя. Для CAPTCHA, 2FA, неоднозначных выборов.

## Установка

См. [quickstart.md](quickstart.md)

## Использование

```bash
export ANTHROPIC_API_KEY='your-key'
./run.sh
```

далее вводите задачи на естественном языке:



## Сессии

используйте [login_helper.py](login_helper.py) для ручной авторизации на сайтах. Сессии сохраняются в `.browser_session/` и доступны агенту при следующих запусках.

