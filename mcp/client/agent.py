import os
import asyncio

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from langchain.agents import create_agent
import yaml

load_dotenv()
with open("config.yaml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)
OPENROUTER_API = os.getenv('OPENROUTER_API')
OPENROUTER_MODEL = config.get('OPENROUTER_MODEL')

async def main():
    client = MultiServerMCPClient(
        {
            "articles": {
                "command": "python",
                "args": [
                    "mcp/server/server.py"
                ],
                "transport": "stdio"
            }
        }
    )
    
    tools = await client.get_tools()
    print(tools)
    
    llm = ChatOpenAI(
        model=OPENROUTER_MODEL,
        temperature=0,
        api_key=OPENROUTER_API,
        base_url="https://openrouter.ai/api/v1",
    )
    
    
    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt="""
        Ты агент суммаризации.
    
        Используй MCP tools:
        1. Прочитать файл
        2. Сделать суммаризацию
        3. Сохранить результат
        """
    )
    agent_config = {
        "recursion_limit": 20, 
        "debug": True
    }
    result = await agent.ainvoke(
    {
        "messages": [
            {
                "role": "user",
                "content":
                "Сделай суммаризацию data/articles.json"
            }
        ]
    },
    config=agent_config
)
    
if __name__ == "__main__":
    asyncio.run(main())
