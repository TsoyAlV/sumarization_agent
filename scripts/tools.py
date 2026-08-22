import json
from pathlib import Path
import ast
from typing import List


def generate_answer(content='hi', client=None, model=None, temperature=0, max_tokens=1000):
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
        temperature=temperature,
        max_tokens=max_tokens,
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
    

def summarize_article(data: List[dict], client=None, modelname=None, temperature=0, max_tokens=1000) -> List[dict]:
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
        _ = generate_answer(content=prompt, client=client, model=modelname, temperature=temperature, max_tokens=max_tokens)
        if not _:
            _ = ' '
        doc['text'] = clean_text(_)
        res.append(doc)
    return res

def save_results(results: str):
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