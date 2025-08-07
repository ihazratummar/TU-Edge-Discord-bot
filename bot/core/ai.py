import asyncio
import logging

from openai import OpenAI

from bot import GITHUB_AI_TOKEN

api_sema = asyncio.Semaphore(3)

endpoint = "https://models.github.ai/inference"
model = "openai/gpt-4.1"


async def generate_ai_response(
        prompt: str
):
    async with api_sema:
        try:
            client = OpenAI(
                base_url=endpoint,
                api_key=GITHUB_AI_TOKEN,
            )
            messages = [
                {
                    "role": "system", "content": """
You are a professional financial analyst with expertise in cryptocurrency, stocks, forex, and options trading. 

You provide sharp, concise, and insightful commentary based on market data. Focus on trends, momentum, volatility, volume, and technical levels. Avoid disclaimers, filler words, and repeating the input. Your tone is confident, analytical, and to-the-point. Output should sound like a trader's opinion, not a report.

📝 Format Requirement: After every sentence, add a blank line for better readability.
"""
                },
                {
                    "role": "user", "content": prompt
                }
            ]

            response = client.chat.completions.create(
                messages=messages,
                temperature=1.0,
                top_p=1.0,
                model=model
            )
            return response.choices[0].message.content
        except Exception as e:
            logging.error(f"[OPENAI ERROR] - Error Generating AI Response: {e}")
            return None




async def generate_market_ai_response(live_data: dict):

    USER_PROMPT = f"""
    Give an opinion on the crypto market for symbol {live_data.get("symbol")} based on this data:
    {live_data}
    Focus on trend, momentum, and any key levels. Avoid repeating data. No disclaimers. No greetings. Just an insight.
    """
    try:
        response = await generate_ai_response(prompt=USER_PROMPT)
        return response
    except Exception as e:
        logging.error(f"Error generating market response :{e}")
        return None

live_datas = {'symbol': 'AAPL', 'current_price': 219.31, 'change': 6.06, 'percent_change': 2.84, 'day_high': 220.34,
             'day_low': 216.58, 'day_open': 218.8, 'last_close': 213.25, 'timestamp': 1754586786}
#
# info = asyncio.run(generate_market_ai_response(live_datas))
# print(info)