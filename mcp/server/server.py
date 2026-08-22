import os
from typing import List

import yaml
from mcp.server.fastmcp import FastMCP
import json
import ast
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()
with open("config.yaml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)
OPENROUTER_API = os.getenv('OPENROUTER_API')
OPENROUTER_MODEL = config.get('OPENROUTER_MODEL')
mcp = FastMCP(
    "Article Summarization Server"
)
client_openrouter = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API,
)



def generate_answer(content='hi', client=client_openrouter, model=OPENROUTER_MODEL):
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": """
                Отвечай только на вопрос.
                Максимум 30 слов.
                Только один короткий абзац.
                Без Markdown, списков и таблиц.
                """
            },
            {
                "role": "user",
                "content": content
            }
        ],
        temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS,
        extra_body={
            "reasoning_effort": "low"
        }
    )
    return completion.choices[0].message.content


def clean_text(text):
    replacements = {
        "\u202f": " ",  # narrow no-break space
        "\xa0": " ",    # non-breaking space
        "\n": " ",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return text.strip()


@mcp.tool()
def read_file(path: str) -> List[dict]:
    """
    Читает json файл со статьями
    
    Примеры:
    [
     {'id': '1', 'title': ..., 'text': ...},
     {'id': '2', ...}
    ]
    """

    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    # return json.dumps(data, ensure_ascii=False)
    return data


@mcp.tool()
def summarize_article(data: List[dict], client=client_openrouter, model_name=OPENROUTER_MODEL) -> List[dict]:
    """
    Суммаризирует данные 

    input:
    [
     {'id': '1', 'title': ..., 'text': some_text},
     {'id': '2', ...}
    ]

    output:
    [
     {'id': '1', 'title': ..., 'text': summarized_text},
     {'id': '2', ...}
    ]
    """
    res = []
    if isinstance(data, str):
        _data = ast.literal_eval(data)
    else:
        _data = data
    for doc in _data:
        prompt = f"""
        Сделай краткое резюме статьи (суммаризацию):
    
        {doc['text']}
    """
        _ = generate_answer(content=prompt, client=client, model=model_name)
        doc['text'] = clean_text(_)
        res.append(doc)
    return res


@mcp.tool()
def save_results(results: List[dict]):
    """
    Сохраняет результаты суммаризации List[dict] в json файл.
    """

    output_path = Path("output/summaries.json")

    output_path.parent.mkdir(exist_ok=True)
    _results = ast.literal_eval(results)

    with open(
        output_path,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            _results,
            f,
            ensure_ascii=False,
            indent=2
        )
    
    return "Файл успешно сохранен"

if __name__ == "__main__":
    mcp.run()