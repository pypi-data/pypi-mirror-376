from __future__ import annotations

import asyncio
import random
import json

from ..typing import AsyncResult, Messages
from ..requests import StreamSession, raise_for_status
from ..errors import ResponseError
from ..providers.response import FinishReason, Sources
from .base_provider import AsyncGeneratorProvider, ProviderModelMixin

API_URL = "https://www.perplexity.ai/socket.io/"
WS_URL = "wss://www.perplexity.ai/socket.io/"

class PerplexityLabs(AsyncGeneratorProvider, ProviderModelMixin):
    label = "Perplexity Labs"
    url = "https://labs.perplexity.ai"
    working = True
    active_by_default = True

    default_model = "r1-1776"
    models = [
        default_model,
        "sonar-pro",
        "sonar",
        "sonar-reasoning",
        "sonar-reasoning-pro",
    ]

    @classmethod
    async def create_async_generator(
        cls,
        model: str,
        messages: Messages,
        proxy: str = None,
        **kwargs
    ) -> AsyncResult:
        # Enhanced headers to avoid Cloudflare detection
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
        
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "no-cache",
            "DNT": "1",
            "Origin": cls.url,
            "Pragma": "no-cache",
            "Referer": f"{cls.url}/",
            "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": random.choice(user_agents)
        }
        
        # Try different impersonation methods
        impersonate_options = ["chrome120", "chrome", "edge120", "safari"]
        
        for impersonate in impersonate_options:
            try:
                async with StreamSession(headers=headers, proxy=proxy, impersonate=impersonate) as session:
                    # Add a small delay to appear more human-like
                    await asyncio.sleep(random.uniform(0.5, 1.5))
                    
                    t = format(random.getrandbits(32), "08x")
                    async with session.get(
                        f"{API_URL}?EIO=4&transport=polling&t={t}"
                    ) as response:
                        await raise_for_status(response)
                        text = await response.text()
                    assert text.startswith("0")
                    sid = json.loads(text[1:])["sid"]
                    
                    # Add delay between requests
                    await asyncio.sleep(random.uniform(0.2, 0.8))
                    
                    post_data = '40{"jwt":"anonymous-ask-user"}'
                    async with session.post(
                        f"{API_URL}?EIO=4&transport=polling&t={t}&sid={sid}",
                        data=post_data
                    ) as response:
                        await raise_for_status(response)
                        assert await response.text() == "OK"
                    
                    # Add delay
                    await asyncio.sleep(random.uniform(0.2, 0.8))
                    
                    async with session.get(
                        f"{API_URL}?EIO=4&transport=polling&t={t}&sid={sid}",
                        data=post_data
                    ) as response:
                        await raise_for_status(response)
                        assert (await response.text()).startswith("40")
                    
                    # Add delay before WebSocket
                    await asyncio.sleep(random.uniform(0.5, 1.0))
                    
                    async with session.ws_connect(f"{WS_URL}?EIO=4&transport=websocket&sid={sid}", autoping=False) as ws:
                        await ws.send_str("2probe")
                        assert(await ws.receive_str() == "3probe")
                        await ws.send_str("5")
                        assert(await ws.receive_str() == "6")
                        
                        format_messages = []
                        last_is_assistant = False
                        for message in messages:
                            if message["role"] == "assistant":
                                if last_is_assistant:
                                    continue
                                last_is_assistant = True
                            else:
                                last_is_assistant = False
                            if isinstance(message["content"], str):
                                format_messages.append({
                                    "role": message["role"],
                                    "content": message["content"]
                                })
                        
                        message_data = {
                            "version": "2.18",
                            "source": "default",
                            "model": model,
                            "messages": format_messages
                        }
                        
                        await ws.send_str("42" + json.dumps(["perplexity_labs", message_data]))
                        last_message = 0
                        while True:
                            message = await ws.receive_str()
                            if message == "2":
                                if last_message == 0:
                                    raise RuntimeError("Unknown error")
                                await ws.send_str("3")
                                continue
                            try:
                                if not message.startswith("42"):
                                    continue
                                    
                                parsed_data = json.loads(message[2:])
                                message_type = parsed_data[0]
                                data = parsed_data[1]
                                
                                # Handle error responses
                                if message_type.endswith("_query_progress") and data.get("status") == "failed":
                                    error_message = data.get("text", "Unknown API error")
                                    raise ResponseError(f"API Error: {error_message}\n")
                                
                                # Handle normal responses
                                if "output" in data:
                                    if last_message == 0 and model == cls.default_model:
                                        yield "<think>"
                                    yield data["output"][last_message:]
                                    last_message = len(data["output"])
                                    if data["final"]:
                                        if data["citations"]:
                                            yield Sources(data["citations"])
                                        yield FinishReason("stop")
                                        break
                            except ResponseError as e:
                                # Re-raise ResponseError directly
                                raise e
                            except Exception as e:
                                raise ResponseError(f"Error processing message: {message}") from e
                # If we get here, the impersonation worked
                break
            except Exception as e:
                if impersonate == impersonate_options[-1]:
                    # Last attempt failed, re-raise the error
                    raise e
                # Try next impersonation method
                continue
            t = format(random.getrandbits(32), "08x")
            async with session.get(
                f"{API_URL}?EIO=4&transport=polling&t={t}"
            ) as response:
                await raise_for_status(response)
                text = await response.text()
            assert text.startswith("0")
            sid = json.loads(text[1:])["sid"]
            post_data = '40{"jwt":"anonymous-ask-user"}'
            async with session.post(
                f"{API_URL}?EIO=4&transport=polling&t={t}&sid={sid}",
                data=post_data
            ) as response:
                await raise_for_status(response)
                assert await response.text() == "OK"
            async with session.get(
                f"{API_URL}?EIO=4&transport=polling&t={t}&sid={sid}",
                data=post_data
            ) as response:
                await raise_for_status(response)
                assert (await response.text()).startswith("40")
            async with session.ws_connect(f"{WS_URL}?EIO=4&transport=websocket&sid={sid}", autoping=False) as ws:
                await ws.send_str("2probe")
                assert(await ws.receive_str() == "3probe")
                await ws.send_str("5")
                assert(await ws.receive_str() == "6")
                format_messages = []
                last_is_assistant = False
                for message in messages:
                    if message["role"] == "assistant":
                        if last_is_assistant:
                            continue
                        last_is_assistant = True
                    else:
                        last_is_assistant = False
                    if isinstance(message["content"], str):
                        format_messages.append({
                            "role": message["role"],
                            "content": message["content"]
                        })
                message_data = {
                    "version": "2.18",
                    "source": "default",
                    "model": model,
                    "messages": format_messages
                }
                await ws.send_str("42" + json.dumps(["perplexity_labs", message_data]))
                last_message = 0
                while True:
                    message = await ws.receive_str()
                    if message == "2":
                        if last_message == 0:
                            raise RuntimeError("Unknown error")
                        await ws.send_str("3")
                        continue
                    try:
                        if not message.startswith("42"):
                            continue
                            
                        parsed_data = json.loads(message[2:])
                        message_type = parsed_data[0]
                        data = parsed_data[1]
                        
                        # Handle error responses
                        if message_type.endswith("_query_progress") and data.get("status") == "failed":
                            error_message = data.get("text", "Unknown API error")
                            raise ResponseError(f"API Error: {error_message}\n")
                        
                        # Handle normal responses
                        if "output" in data:
                            if last_message == 0 and model == cls.default_model:
                                yield "<think>"
                            yield data["output"][last_message:]
                            last_message = len(data["output"])
                            if data["final"]:
                                if data["citations"]:
                                    yield Sources(data["citations"])
                                yield FinishReason("stop")
                                break
                    except ResponseError as e:
                        # Re-raise ResponseError directly
                        raise e
                    except Exception as e:
                        raise ResponseError(f"Error processing message: {message}") from e


if __name__ == "__main__":
    import asyncio
    
    async def test_perplexity_labs():
        # Test messages
        messages = [
            {"role": "user", "content": "What is the capital of France?"}
        ]
        
        print("Testing PerplexityLabs provider...")
        print("Sending message:", messages[0]["content"])
        print("Using model:", PerplexityLabs.default_model)
        
        try:
            async for response in PerplexityLabs.create_async_generator(
                model=PerplexityLabs.default_model,
                messages=messages
            ):
                if isinstance(response, str):
                    print(response, end="", flush=True)
                elif hasattr(response, 'citations'):  # Sources object
                    print(f"\nSources: {response.citations}")
                else:  # FinishReason
                    print(f"\nFinished with reason: {response}")
        except Exception as e:
            print(f"\nError: {str(e)}")
    
    # Run the test
    asyncio.run(test_perplexity_labs())
