"""
Используй для запуска пайплайна:
python ./scripts/pipeline_langchain.py --path data/articles.json
"""

import os
from typing import List

import click
import yaml
from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from openai import OpenAI

from tools import generate_answer, clean_text, read_file, summarize_article, save_results

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


@tool
def _read_file(path: str) -> List[dict]:
    """
    Читает json файл со статьями
    
    Примеры:
    [
     {'id': '1', 'title': ..., 'text': ...},
     {'id': '2', ...}
    ]
    """
    return read_file(path)

    
@tool
def _summarize_article(data: List[dict], client=client_openrouter, modelname=OPENROUTER_MODEL, temperature=TEMPERATURE, max_tokens=MAX_TOKENS) -> List[dict]:
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
    ]"""
    return summarize_article(data, client, modelname, temperature, max_tokens)


@tool
def _save_results(results: str):
    """
    Сохраняет результаты суммаризации List[dict] в json файл.
    """
    return save_results(results)

@click.command()
@click.option('-p','--path', type=str)
def main(path):
    llm = ChatOpenAI(
        model=OPENROUTER_MODEL,
        temperature=TEMPERATURE,
        api_key=OPENROUTER_API,
        base_url="https://openrouter.ai/api/v1",
    )
    tools = [
        _read_file,
        _summarize_article,
        _save_results
    ]
    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt="""
        Ты агент для суммаризации.
    
        Нужно:
        1. Прочитать JSON.
        2. Суммаризировать файл.
        3. Сохранить результат суммаризации в виде JSON.
        """
    )
    agent_config = {
            "recursion_limit": 20, 
            "debug": True
        }
    if not path:
        query = "Сделай суммаризацию data/articles.json"
    else:
        query = f"Сделай суммаризацию {path}"
    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": query
                }
            ]
        },
        config=agent_config
    )

if __name__ == '__main__':
    main()