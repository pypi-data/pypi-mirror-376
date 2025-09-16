# Пакет llm_common

Содержит
- **Prometheus мониторинг**: Полнофункциональная система метрик для HTTP запросов и действий приложения
- **HTTP клиенты**: Готовые к использованию HTTP клиенты для LLM и аутентификации с автоматическим трекингом
- **Декораторы и контекст-менеджеры**: Готовые примитивы для отслеживания
- **FastAPI интеграция**: Middleware для отслеживания http метрик и endpoint для экспорта метрик
- **Flask интеграция**: endpoint для экспорта метрик

Задание: Подключи в проект отслеживание метрик, установив пакет llm_common.

Для критичных секций кода.
Для Telegram обработчиков и callback если это telegram бот.
Сделай интеграцию с FastApi, если в этом проекте он есть.
Используй HTTPX обертку с мониторингом для сырых http запросов.

### 0. Установите клиент prometheus_client в проекте

### 1. Инициализация метрик

Метрики нужно инициализировать, после этого под капотом библиотека сможет подставлять дефолтный значения в лейблы метрик
Проинициализируйте при старте программы, кроме тестовой среды.

```python
from llm_common.prometheus import build_prometheus_metrics

# Инициализация системы мониторинга
metrics = build_prometheus_metrics(
    project_name="projectname",
    env="dev"  # Аргумент env принимает только значения dev, preprod prod !!!
)
```

### 2. Использование HTTP клиентов с встренным отслеживанием http запросов

Если в проекте есть использование клиентов, в которых есть HTTPX, то для него есть обертка с встренным отслеживанием http запросов

```python
from llm_common.clients.llm_http_client import LLMHttpClient
from langchain_openai import ChatOpenAI

# LLM клиент с OpenAI интеграцией и мониторингом
custom_aclient = LLMHttpClient(verify=False)

chat_model = ChatOpenAI(
    ...,
    http_async_client=custom_aclient,
)
```

Если в проекте есть http запросы, то для них используй AuthHttpClient в которой есть обертка с встренным отслеживанием http запросов

```python
from llm_common.clients.auth_client import AuthHttpClient

async with AuthHttpClient() as client:
    response = await client.post("https://auth-service.com/api/check")
```

### 3. Отслеживание времени и статуса выполнения секций кода через контекстный менеджер или декоратор

Чтобы эти примитивы смогли отследить возниклования exception, внутри этих контекстного менеджера и декоратора не должны
подавляться exception.

```python
from llm_common.prometheus import action_tracking, action_tracking_decorator

# Использование контекст-менеджера
with action_tracking("data_processing") as tracker:
    # Ваш код
    processed_data = process_data()
    # Опционально: трекинг размера данных
    tracker.size(len(processed_data))

# Использование декоратора
@action_tracking_decorator("llm_request")
async def make_llm_request():
    # Ваш код
    return result
```

### 4. Интеграция с FastAPI

```python
from fastapi import FastAPI
from llm_common.prometheus import fastapi_tracking_middleware, fastapi_endpoint_for_prometheus

app = FastAPI()

# Добавление middleware для трекинга HTTP запросов
app.middleware("http")(fastapi_tracking_middleware)

# Endpoint для экспорта метрик Prometheus
app.get("/prometheus")(fastapi_endpoint_for_prometheus)
```

### 4.1. Интеграция с Flask

```python
from flask import Flask
from llm_common.prometheus import flask_endpoint_for_prometheus

flask_app = Flask()

# Endpoint для экспорта метрик Prometheus
flask_app.get("/prometheus")(flask_endpoint_for_prometheus)
```

### 5. Боты Telegram

Хорошей практикой является отслеживания всех хендлеров.

Применяйется на хендлеры и обработки callback кнопок декоратор или контекстный менеджеры action_tracking и action_tracking_decorator
В качестве имени указывайте суффикс "_handler" action_tracking(name="menu_handler"), это позволит офильтровать на 
графике только метрики для хэндлеров

### 5.1 Интеграция c python-telegram-bot

Чтобы отслеживать HTTP запросы к API Telegram:

```python
from llm_common.prometheus import HTTPXTransportWithMonitoring
from telegram.request import HTTPXRequest
from telegram.ext import ApplicationBuilder

transport = HTTPXTransportWithMonitoring()
httpx_request = HTTPXRequest(
    httpx_kwargs={"transport": transport}
)

application_builder = (
    ApplicationBuilder()
    .request(httpx_request)
)
```

### 6. Именование отслеживаемых action

Для обработчиков Telegram, суффикс "_handler"
Для регулярных задач, суффикс "_task"
Для вызовов llm, суффикс "_llm_call"
Для запуска агента llm, суффикс "_agent"

## 📖 API Документация

#### action_tracking(name: str)
Контекст-менеджер для отслеживания действий:
- Автоматически измеряет время выполнения
- Подсчитывает успешные и ошибочные выполнения
- Позволяет трекить размер обработанных данных

#### action_tracking_decorator(name: str)
Декоратор для функций и корутин, поддерживает все возможности `action_tracking`.

## 🔍 Метрики и мониторинг

### Доступные метрики

Все метрики имеют префикс `genapp_`:

#### HTTP метрики:
- `genapp_http_requests_total` - Общее количество HTTP запросов
- `genapp_http_request_duration_sec` - Гистограмма времени выполнения
- `genapp_http_request_size_bytes` - Размер запросов/ответов

#### Метрики действий:
- `genapp_action_count_total` - Количество выполненных действий
- `genapp_action_duration_sec` - Время выполнения действий
- `genapp_action_size_total` - Размер обработанных данных

### Labels (теги)

Метрики содержат labels:
- http_requests_total → method, status, resource, app_type, env, app
- http_request_duration_sec → method, status, resource, app_type, env, app
- http_request_size_bytes → resource, status, method, direction, app_type, env, app
- action_count_total → name, status, env, app
- action_duration_sec → name, env, app
- action_size_total → name, env, app
