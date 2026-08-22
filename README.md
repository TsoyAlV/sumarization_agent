# 🤖 Агент для суммаризации JSON-статей

## 📋 Описание проекта

Данный проект представляет собой агента, который **end-to-end** выполняет суммаризацию записей в JSON-файле. Ключевая особенность: в коде **нет** явного Python-цикла с вызовом LLM для каждого файла — агент сам:

1. Получает команду от пользователя.
2. Сам вызывает инструмент чтения файла.
3. Сам находит статьи в файле.
4. Сам вызывает суммаризатор.
5. Сам сохраняет результат в JSON-файл.

Все вычисления выполняются в облаке (через API LLM), поэтому проект работает даже на слабых локальных машинах.

---

## 🏗 Варианты реализации

Проект реализован в трёх архитектурных подходах. Все варианты решают одну и ту же задачу, но разными способами:

### Вариант 1: LangChain (baseline)

```
User
 |
 v
LLM Agent (LangChain)
 |
 +-- Tool: read_file
 |
 +-- Tool: summarize_article
 |
 +-- Tool: save_result
 |
 v
output.json
```

**Стек:** LangChain, Tool calling, OpenAI/Groq/OpenRouter LLM.

Агент создаётся через `create_agent()` и получает набор из трёх инструментов. LLM сама решает, в каком порядке и с какими аргументами их вызывать.

### Вариант 2: LangGraph (более правильная архитектура)

```
START
  |
  v
Read JSON Node
  |
  v
Summarization Node
  |
  v
Validation Node
  |
  v
Save JSON Node
  |
  v
END
```

**Стек:** LangGraph, StateGraph, TypedDict.

Пайплайн собран из явных узлов (nodes), соединённых рёбрами. Состояние — объект `SummaryState`, который путешествует между узлами. Каждый узел — обычная Python-функция.

### Вариант 3: MCP + LangChain

**Стек:** LangChain + MCP (Model Context Protocol).

Инструменты вынесены в отдельный **MCP-сервер**, а агент подключается к ним через **MCP-клиент**. Сервер запускается как отдельный процесс, клиент получает инструменты и передаёт их LLM.

```
        LLM
         |
   MCP Client
         |
   MCP Server
     /   |   \
read_file summarize save_results

MCP server tools/
├── read_file()
├── summarize_article()
└── save_results()
```

---

## 📁 Структура проекта

```
project/
├── notebooks/
│   └── pipeline.ipynb          # Jupyter-ноутбук: все 3 варианта + тесты
│
├── scripts/
│   ├── pipeline_langchain.py   # CLI: LangChain-пайплайн
│   ├── pipeline_langgraph.py   # CLI: LangGraph-пайплайн
│   └── tools.py                # Общие вспомогательные функции
│
├── mcp/
│   ├── client/
│   │   └── agent.py            # MCP-клиент + LangChain-агент
│   └── server/
│       └── server.py           # MCP-сервер с инструментами
│
├── data/
│   └── articles.json           # Входные данные (статьи)
│
├── output/
│   └── summaries.json          # Результаты суммаризации
│
├── config.yaml                 # Конфигурация модели и параметров
├── .env                        # API-ключи (не в git)
└── requirements.txt            # Зависимости
```

---

## ⚙️ Установка и настройка

### 1. Предварительные требования

- Python 3.10+
- API-ключ для LLM:
  - **Groq** — [инструкция по получению](https://lokismentor.yonote.ru/doc/zadacha-rag-bAH77R5VXr)
  - **OpenRouter** — ключ с платформы [openrouter.ai](https://openrouter.ai)
  - или локальный сервер LM Studio / Ollama

### 2. Клонирование и окружение

```bash
# Клонировать репозиторий
git clone <repository-url>
cd <repository-folder>

# Создать виртуальное окружение
python -m venv venv

# Активировать
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows PowerShell

# Установить зависимости
pip install -r requirements.txt
```

### 3. Создать `.env`

```
GROQ_API=your_groq_api_key
OPENROUTER_API=your_openrouter_api_key
```

### 4. Настроить `config.yaml`

Пример:

```yaml
GROQ_MODEL: "groq-model-name"
OPENROUTER_MODEL: "deepseek/deepseek-v4-flash-0731"
TEMPERATURE: 0.7
MAX_TOKENS: 300
```

---

## 🚀 Команды для запуска

### Вариант 1: LangChain-пайплайн

```bash
python ./scripts/pipeline_langchain.py --path data/articles.json
```

| Аргумент | Описание | По умолчанию |
|----------|----------|---------------|
| `-h, --help` | Показать справку | — |
| `-p, --path` | Путь к входному JSON-файлу | `data/articles.json` |

Пример с кастомным путём:

```bash
python ./scripts/pipeline_langchain.py -p /path/to/my/articles.json
```

### Вариант 2: LangGraph-пайплайн

```bash
python ./scripts/pipeline_langgraph.py --path data/articles.json
```

Пример с кастомным путём:

```bash
python ./scripts/pipeline_langgraph.py -p /path/to/my/articles.json
```

### Вариант 3: MCP-агент

```bash
python mcp/client/agent.py
```

Этот запуск автоматически:
1. Запускает MCP-сервер (`mcp/server/server.py`) как отдельный процесс
2. Получает его инструменты через MCP-клиент
3. Запускает LangChain-агента с этими инструментами
4. Выполняет суммаризацию файла `data/articles.json`

### Запуск ноутбука

```bash
jupyter notebook notebooks/pipeline.ipynb
```

В ноутбуке интерактивно демонстрируются **все три варианта** + юнит-тесты для узлов графа.

---

## 🔧 Детальное описание файлов

### 1. `notebooks/pipeline.ipynb`

Jupyter-ноутбук, где исследуются все три подхода.

**Основные шаги:**

1. **Загрузка данных и конфигурации** — читает `data/articles.json` и `config.yaml`.
2. **Три клиента LLM:**
   - `client_groq` — облачный Groq (быстрый, бесплатный)
   - `client_lmstudio` — локальный LM Studio (`http://10.98.65.86:5985/v1`)
   - `client_openrouter` — OpenRouter (мультимодельная маршрутизация)

3. **Функция `generate_answer`**

   ```python
   def generate_answer(content='hi', client=client_groq, model=GROQ_MODEL):
   ```

   Единая обёртка над `chat.completions.create`. Системный промпт требует:
   - отвечать только на вопрос
   - максимум 30 слов
   - один короткий абзац
   - без Markdown, списков и таблиц

4. **Инструменты LangChain:**

   `read_file(path)` — читает JSON-файл со статьями, возвращает `List[dict]`.

   `summarize_article(data)` — суммаризирует каждую статью через LLM, заменяет `text` на короткое резюме, возвращает список тех же словарей с обновлённым текстом.

   `save_results(results)` — сохраняет результат в `../output/summaries.json` (создавая директорию при необходимости).

5. **Вспомогательная функция `clean_text`** — убирает "грязные" пробелы из текста LLM:

   ```python
   def clean_text(text):
       replacements = {
           "\u202f": " ",  # узкий неразрывный пробел
           "\xa0": " ",    # неразрывный пробел
           "\n": " ",
       }
       ...
   ```

6. **LangChain-агент (Вариант 1)** — создаётся через `create_agent` из LangChain с системным промптом:
   > 1. Прочитать JSON. → 2. Суммаризировать файл. → 3. Сохранить результат.

   Класс `ToolLogger` — коллбэк, логирующий инструменты: запуск/завершение каждого вызова.

7. **LangGraph-граф (Вариант 2)** — в ноутбуке же собран граф из 3 узлов:

   - `read_file_node` — открывает файл по пути из состояния
   - `summarize_node_openrouter` — суммаризирует статьи
   - `save_node` — записывает результат

8. **Юнит-тесты узлов графа** (`test_read_file_node`, `test_summarize_node`, `test_save_node`) — проверяют:
   - что файл прочитан и содержит `id`, `title`, `text`
   - что суммаризация работает даже с замоканной LLM (fake_generate_answer)
   - что результат сохраняется на диск корректно

9. **Выполнение скомпилированного графа** через `app.invoke({"path": ...})`.

### 2. `scripts/pipeline_langchain.py`

ЛangChain-пайплайн в виде CLI-скрипта.

**Импорт общих функций** из `tools.py`:
```python
from tools import generate_answer, clean_text, read_file, summarize_article, save_results
```

**Обёртки-инструменты** (`@tool`):
- `_read_file(path)` → вызывает `read_file(path)`
- `_summarize_article(data, client, modelname, temperature, max_tokens)` → вызывает `summarize_article(...)`
- `_save_results(results)` → вызывает `save_results(results)`

**Запуск через `click`:**
```bash
python ./scripts/pipeline_langchain.py --path data/articles.json
```

Логика `main(path)`:
1. Создаёт `ChatOpenAI` (на базе OpenRouter).
2. Собирает список инструментов.
3. Создаёт агента с системным промптом (шаги 1–3).
4. `agent.invoke(...)` с вопросом: `"Сделай суммаризацию {path}"`.
5. В конфиге агента включён `debug=True` и `recursion_limit=20` — видно вызовы инструментов.

### 3. `scripts/pipeline_langgraph.py`

LangGraph-пайплайн в CLI-файле.

**Состояние графа (TypedDict):**
```python
class SummaryState(TypedDict):
    path: str
    articles: List[dict]
    summaries: List[dict]
```

**Узлы:**

- `read_file_node(state)` — открывает `state["path"]` как JSON, возвращает список статей.
- `summarize_node(state, client, model_name)` — для каждой статьи формирует промпт («Сделай краткое резюме статьи. Максимум 30 слов.»), вызывает `generate_answer`, подставляет резюме в копию статьи.
- `summarize_node_openrouter(state)` — частный случай с OpenRouter-клиентом.
- `save_node(state)` — сохраняет `state["summaries"]` в `output/summaries.json`.

**Сборка графа:**
```python
graph = StateGraph(SummaryState)
graph.add_node("read_file", read_file_node)
graph.add_node("summarize", summaries_node_openrouter)
graph.add_node("save", save_node)

graph.add_edge(START, "read_file")
graph.add_edge("read_file", "summarize")
graph.add_edge("summarize", "save")
graph.add_edge("save", END)
```

**Компиляция и запуск:**
```python
app = graph.compile()
app.invoke({"path": path})
```

### 4. `mcp/server/server.py`

MCP-сервер (Model Context Protocol). Оборачивает инструменты в формате FastMCP:

- `FastMCP("Article Summarization Server")` — сервер
- Инструменты регистрируются через `@mcp.tool()`:
  - `read_file(path)` → возвращает список словарей статей
  - `summarize_article(data)` → суммаризирует статьи (использует OpenRouter LLM)
  - `save_results(results)` → сохраняет результат в `output/summaries.json`
- Внутри сервера также есть `generate_answer` и `clean_text` (самодостаточная логика).
- `mcp.run()` запускает сервер (по умолчанию stdio transport).

### 5. `mcp/client/agent.py`

MCP-клиент + LangChain-агент (асинхронный):

```python
client = MultiServerMCPClient({
    "articles": {
        "command": "python",
        "args": ["mcp/server/server.py"],
        "transport": "stdio"
    }
})
tools = await client.get_tools()
```

Дальше всё как вари# 1: создаётся `ChatOpenAI` (OpenRouter) + `create_agent(...)` + `agent.ainvoke(...)`.

Фрагмент кода: **вывод строк** `"Сделай суммаризацию data/articles.json"` запускает полный end-to-end пайплайн.

---

## 📊 Формат данных

### Входные данные (`data/articles.json`)

```json
[
  {
    "id": "1",
    "title": "Регламент командировок 2026",
    "text": "Полный текст статьи..."
  },
  {
    "id": "2",
    "title": "Обновление работы в TravelHub",
    "text": "Полный текст статьи..."
  }
]
```

### Выходные данные (`output/summaries.json`)

```json
[
  {
    "id": "1",
    "title": "Регламент командировок 2026",
    "text": "Краткое резюме статьи (до 30 слов)..."
  },
  {
    "id": "2",
    "title": "Обновление работы в TravelHub",
    "text": "Краткое резюме статьи (до 30 слов)..."
  }
]
```

---

## 🧪 Тестирование

В ноутбуке `notebooks/pipeline.ipynb` уже есть юнит-тесты узлов LangGraph:

| Тест | Что проверяет |
|------|----------------|
| `test_read_file_node` | Файл читается, в статьях есть `id`, `title`, `text` |
| `test_summarize_node` | Суммаризация возвращает количество статей и заменяет текст |
| `test_summarize_node` (с моком)` | LULLM можно замокануть функцией `fake_generate_answer` |
| `test_save_node` | Результат корректно сохраняется в JSON и зачитывается обратно |

---

## 🛠️ Полезные советы

- **Не забывайте про `.gitignore`**: добавьте в него `.env`, `venv/`, `output/summaries.json`.
- **Переключение LLM**: в ноутбуке есть три клиента (`groq`, `lmstudio`, `openrouter`) — меняйте дефолтный в вызовах `generate_answer(client=...)`.
- **Debugg**: в LangChain-агенте установите `config={"recursion_limit": 20, "debug": True}`, чтобы видеть все действия инструментов.
- **MCP-сервер** можно запускать и отдельно для тестов: `python mcp/server/server.py`.

---

Проект показывает **три способа** построения LLM-агента (LangChain tools, LangGraph StateGraph, MCP) — от простого до масштабируемого, с интерактивной разработкой в Jupyter.
