"""
Используй для запуска пайплайна:
python ./scripts/pipeline_langgraph.py --path "суммаризируй файл data/articles.json"
"""

import os
from typing import TypedDict, List
from pathlib import Path

import yaml
import json
import click
from dotenv import load_dotenv
from openai import OpenAI
from langgraph.graph import StateGraph, START, END

from tools import generate_answer

load_dotenv()

with open("config.yaml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)
    
OPENROUTER_API = os.getenv('OPENROUTER_API')
OPENROUTER_MODEL = 'deepseek/deepseek-v4-flash-0731'
TEMPERATURE = config['TEMPERATURE']
MAX_TOKENS = config['MAX_TOKENS']

client_openrouter = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API,
)


class SummaryState(TypedDict):
    path: str
    articles: List[dict]
    summaries: List[dict]


def read_file_node(state: SummaryState):

    with open(
        state["path"],
        encoding="utf-8"
    ) as f:
        articles = json.load(f)


    return {
        "articles": articles
    }

def summarize_node(state: SummaryState, client=client_openrouter, model_name='modelname'):

    summaries = []

    for article in state["articles"]:

        prompt = f"""
        Сделай краткое резюме статьи.

        Максимум 30 слов.

        Текст:

        {article['text']}
        """


        summary = generate_answer(
            content=prompt,
            client=client,
            model=model_name,
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS
        )


        article_copy = article.copy()

        article_copy["text"] = summary

        summaries.append(article_copy)


    return {
        "summaries": summaries
    }

def summarize_node_openrouter(state: SummaryState):
    return summarize_node(state=state, client=client_openrouter, model_name=OPENROUTER_MODEL)

def save_node(state: SummaryState):

    output_path = Path(
        "output/summaries.json"
    )

    output_path.parent.mkdir(
        exist_ok=True
    )


    with open(
        output_path,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            state["summaries"],
            f,
            ensure_ascii=False,
            indent=2
        )

    return {}

graph = StateGraph(
    SummaryState
)


graph.add_node(
    "read_file",
    read_file_node
)


graph.add_node(
    "summarize",
    summarize_node_openrouter
)


graph.add_node(
    "save",
    save_node
);

graph.add_edge(
    START,
    "read_file"
)


graph.add_edge(
    "read_file",
    "summarize"
)


graph.add_edge(
    "summarize",
    "save"
)


graph.add_edge(
    "save",
    END
)

@click.command()
@click.option('-p','--path', type=str)
def main(path):
    app = graph.compile()
    if not path:
        path = "data/articles.json"
    result = app.invoke(
        {
            "path": path
        }
    )

if __name__ == '__main__':
    main()
    