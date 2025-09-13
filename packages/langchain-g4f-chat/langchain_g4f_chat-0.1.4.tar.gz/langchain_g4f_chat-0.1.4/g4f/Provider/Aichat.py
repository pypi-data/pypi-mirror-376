from __future__ import annotations

from ..typing import Messages
from .base_provider import AsyncProvider, format_prompt
from ..requests import StreamSession

class Aichat(AsyncProvider):
    url = "https://chatplus.com"
    working = True
    supports_gpt_35_turbo = True

    @staticmethod
    async def create_async(
        model: str,
        messages: Messages,
        proxy: str = None, **kwargs) -> str:

        headers = {
            'authority': 'chatplus.com',
            'accept': 'text/plain, */*; q=0.01',
            'accept-language': 'en,fr-FR;q=0.9,fr;q=0.8,es-ES;q=0.7,es;q=0.6,en-US;q=0.5,am;q=0.4,de;q=0.3',
            'content-type': 'application/json',
            'origin': 'https://chatplus.com',
            'referer': 'https://chatplus.com/',
            'sec-ch-ua': '"Chromium";v="118", "Google Chrome";v="118", "Not=A?Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
            'x-requested-with': 'XMLHttpRequest',
        }

        # Fix the proxy handling
        proxies = {"https": proxy} if proxy else {}

        async with StreamSession(headers=headers,
                                timeout=30,
                                proxies=proxies,
                                impersonate="chrome110") as session:

            # Convert messages to ChatPlus format
            from datetime import datetime
            
            chatplus_messages = []
            for i, msg in enumerate(messages):
                chatplus_messages.append({
                    "id": f"msg-{i}",
                    "createdAt": datetime.utcnow().isoformat() + "Z",
                    "role": msg["role"],
                    "content": msg["content"],
                    "parts": [{"type": "text", "text": msg["content"]}]
                })

            json_data = {
                "id": "guest",
                "messages": chatplus_messages,
                "selectedChatModelId": model or "gpt-4o-mini",
                "token": None
            }

            async with session.post("https://chatplus.com/api/chat",
                                    json=json_data) as response:

                # Parse ChatPlus streaming response
                response_text = ""
                async for line in response.content:
                    if line:
                        line_str = line.decode('utf-8').strip()
                        if line_str.startswith('0:"'):
                            # Extract text chunk: 0:"Hello! " -> Hello! 
                            chunk = line_str[3:-1]  # Remove '0:"' and closing '"'
                            response_text += chunk
                        elif line_str.startswith('d:') or line_str.startswith('e:'):
                            # End of stream indicators
                            break
                
                return response_text

    @staticmethod
    async def create_async_generator(
        model: str,
        messages: Messages,
        proxy: str = None, **kwargs):
        """
        Optional: Add streaming support if ChatPlus supports it
        """

        headers = {
            'authority': 'chatplus.com',
            'accept': 'text/event-stream',
            'accept-language': 'en,fr-FR;q=0.9,fr;q=0.8,es-ES;q=0.7,es;q=0.6,en-US;q=0.5,am;q=0.4,de;q=0.3',
            'content-type': 'application/json',
            'origin': 'https://chatplus.com',
            'referer': 'https://chatplus.com/',
            'sec-ch-ua': '"Chromium";v="118", "Google Chrome";v="118", "Not=A?Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
            'x-requested-with': 'XMLHttpRequest',
        }

        # Fix the proxy handling
        proxies = {"https": proxy} if proxy else {}

        async with StreamSession(headers=headers,
                                timeout=30,
                                proxies=proxies,
                                impersonate="chrome110") as session:

            # Convert messages to ChatPlus format
            from datetime import datetime
            
            chatplus_messages = []
            for i, msg in enumerate(messages):
                chatplus_messages.append({
                    "id": f"msg-{i}",
                    "createdAt": datetime.utcnow().isoformat() + "Z",
                    "role": msg["role"],
                    "content": msg["content"],
                    "parts": [{"type": "text", "text": msg["content"]}]
                })

            json_data = {
                "id": "guest",
                "messages": chatplus_messages,
                "selectedChatModelId": model or "gpt-4o-mini",
                "token": None
            }

            async with session.post("https://chatplus.com/api/chat",
                                    json=json_data) as response:
                response.raise_for_status()
                
                async for line in response.content:
                    if line:
                        line_str = line.decode('utf-8').strip()
                        if line_str.startswith('0:"'):
                            # Extract text chunk: 0:"Hello! " -> Hello! 
                            chunk = line_str[3:-1]  # Remove '0:"' and closing '"'
                            yield chunk
                        elif line_str.startswith('d:') or line_str.startswith('e:'):
                            # End of stream indicators
                            break