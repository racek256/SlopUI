import litellm
import asyncio
from exa_py import Exa

exa = Exa(api_key="not_telling_you")

async def search():
    mode = input("enter mode: ")
    query = input("enter query: ")

    response = exa.search(query, type=mode, contents={
            "highlights": True,                     
        },
        num_results=4)


    result = await litellm.acount_tokens(
                model="openai/gpt-5.6-astra",
                messages=[{"role":"user","content":str(response)}]
            )
    print(f"tokens: {result.total_tokens}")

while True:
    asyncio.run(search())
