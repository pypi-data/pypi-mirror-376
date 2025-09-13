from __future__ import annotations

from aiohttp import ClientSession

from ..typing import AsyncResult, Messages
from .base_provider import AsyncGeneratorProvider, ProviderModelMixin
from .helper import format_prompt
from ..providers.response import FinishReason

class Pizzagpt(AsyncGeneratorProvider, ProviderModelMixin):
    url = "https://www.pizzagpt.it"
    api_endpoint = "/api/chatx-completion"
    
    working = True
    
    default_model = 'gpt-4o-mini'
    models = [default_model]

    @classmethod
    async def create_async_generator(
        cls,
        model: str,
        messages: Messages,
        proxy: str = None,
        **kwargs
    ) -> AsyncResult:
        headers = {
            "accept": "application/json",
            "accept-language": "en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7,gu;q=0.6,hi;q=0.5,ko;q=0.4",
            "content-type": "application/json",
            "origin": cls.url,
            "referer": f"{cls.url}/",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
            "x-secret": "Diavola"
        }
        async with ClientSession(headers=headers) as session:
            # Build chat history
            chat = []
            for message in messages:
                sender = "user" if message["role"] == "user" else "assistant"
                chat.append({
                    "text": message["content"],
                    "sender": sender,
                    "studyMode": False
                })
            
            # Get the last user message as question
            last_message = messages[-1]["content"] if messages else ""
            
            data = {
                "question": last_message,
                "searchEnabled": False,
                "studyMode": False,
                "chat": chat
            }
            async with session.post(f"{cls.url}{cls.api_endpoint}", json=data, proxy=proxy) as response:
                response.raise_for_status()
                response_json = await response.json()
                content = response_json.get("content")
                if content:
                    if "Misuse detected. please get in touch" in content:
                        raise ValueError(content)
                    yield content
                    yield FinishReason("stop")
