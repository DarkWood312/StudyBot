import asyncio
import base64
import io
import typing
from dataclasses import dataclass
import re
import aiogram
from aiogram.enums import ChatAction
from openai import AsyncOpenAI
import aiohttp

from extra.chatgpt_parser import telegram_format
from extra.exceptions import AIException
from extra.utils import chunker


@dataclass(frozen=True)
class AIResponse:
    content: str
    messages: list[dict[str, str]]
    tokens: int


class VisionAI:
    def __init__(self, api_key: str):
        self.api_key = api_key

    @staticmethod
    async def get_llm_models() -> list[str]:
        async with aiohttp.ClientSession() as session:
            async with session.get('https://visioncraft.top/models-llm') as response:
                return await response.json()

    @staticmethod
    async def get_sd_models(variant: typing.Literal[
        'models-sd', 'models-sdxl', 'loras-sd', 'loras-sdxl', 'samplers'] = 'models-sd') -> dict:
        async with aiohttp.ClientSession() as session:
            async with session.get(f'https://visioncraft.top/sd/{variant}') as response:
                return await response.json()

    async def generate_image(self, prompt: str,
                             variant: typing.Literal['dalle', 'kandinsky', 'playground'] = 'dalle') -> io.BytesIO:
        size = re.search(r'(^|\s)\d+x\d+(\s|$)', prompt)
        quality = re.search(r'(^|\s)hd(\s|$)', prompt)
        prompt = prompt.replace(size.group() if size else '', '').replace(quality.group() if quality else '', '')
        async with aiohttp.ClientSession() as session:
            async with session.post(f'https://visioncraft.top/{variant}', json={
                'token': self.api_key,
                'prompt': prompt,
                'size': size.group().strip() if size else '1024x1024',
                'quality': quality.group().strip() if quality else 'standard'
            }) as response:
                return io.BytesIO(await response.read())

    async def generate_sd_image(self, prompt: str, model: str, sampler: str = 'Euler', **kwargs) -> io.BytesIO:
        async with aiohttp.ClientSession() as session:
            async with session.post('https://visioncraft.top/sd', json={
                'token': self.api_key,
                'prompt': prompt,
                'model': model,
                'sampler': sampler,
                'steps': kwargs.get('steps', 30),
                'width': kwargs.get('width', 1024),
                'height': kwargs.get('height', 1024),
                'cfg_scale': kwargs.get('cfg_scale', 7),
                'loras': kwargs.get('loras', {})
            }) as response:
                print(await response.json())
                return io.BytesIO(await response.read())

    async def midjourney_create_task(self, prompt: str) -> str:
        async with aiohttp.ClientSession() as session:
            async with session.post('https://visioncraft.top/midjourney',
                                    json={'token': self.api_key, 'prompt': prompt}) as response:
                print(await response.json())
                return (await response.json())['data']

    async def midjourney_get_img(self, task_id: str) -> dict:
        async with aiohttp.ClientSession() as session:
            async with session.post('https://visioncraft.top/midjourney/result',
                                    json={'token': self.api_key, 'task_id': task_id}) as response:
                return await response.json()

    async def llm(self, prompt: str, model: str = 'claude-3-sonnet', messages: list[dict[str, str]] = None, **kwargs) -> \
            AIResponse:
        messages = [{'role': 'user', 'content': prompt}] if messages is None else messages + [
            {'role': 'user', 'content': prompt}]
        client = AsyncOpenAI(api_key=self.api_key, base_url='https://visioncraft.top/v1')

        response = await client.chat.completions.create(stream=kwargs.get('stream', False), model=model,
                                                        messages=messages)
        response_content = response.choices[0].message.content

        if response.id is None:
            raise AIException.Error(response.error['message'])

        return AIResponse(response_content,
                          messages + [{'role': 'assistant', 'content': response.choices[0].message.content}],
                          response.usage.total_tokens)

    async def generate_gif(self, prompt: str, sampler: str = 'Euler') -> list[io.BytesIO]:
        async with aiohttp.ClientSession() as session:
            async with session.post('https://visioncraft.top/generate-gif', json={
                'token': self.api_key,
                'prompt': prompt,
                'sampler': sampler
            }, verify_ssl=False) as response:
                gifs_url = (await response.json())['images']

            gifs = []

            for gif in gifs_url:
                async with session.get(gif) as response:
                    gifs.append(io.BytesIO(await response.read()))

        return gifs


class TrueOpenAI:
    def __init__(self, api_key: str, **kwargs):
        self.api_key = api_key
        self.client = AsyncOpenAI(api_key=api_key, **kwargs)

    async def chat(self, prompt: str, model: str = 'gpt-4o', messages: list[dict] = None, image: bytes = None,
                   **kwargs) -> AIResponse:
        messages = [
            {'role': 'user', 'content': [{'type': 'text', 'text': prompt}]}] if messages is None else messages + [
            {'role': 'user', 'content': [{'type': 'text', 'text': prompt}]}]
        if image:
            base64_image = base64.b64encode(image).decode('utf-8')
            messages[-1]['content'] = messages[-1]['content'] + [{'type': 'image_url', 'image_url': {
                "url": f"data:image/jpeg;base64,{base64_image}", "detail": kwargs.get("detail", "auto")}}]

        response = await self.client.chat.completions.create(model=model,
                                                             messages=messages)
        response_content = response.choices[0].message.content

        return AIResponse(response_content, messages + [{'role': 'assistant', 'content': response_content}],
                          response.usage.total_tokens)

    async def generate_image(self, prompt: str) -> tuple[io.BytesIO, str]:
        size = re.search(r'(^|\s)\d+x\d+(\s|$)', prompt)
        quality = re.search(r'(^|\s)hd(\s|$)', prompt)
        prompt = prompt.replace(size.group() if size else '', '').replace(quality.group() if quality else '', '')
        response = await self.client.images.generate(model='dall-e-3',
                                                     n=1,
                                                     quality=quality.group().strip() if quality else "standard",
                                                     size=size.group().strip() if size else '1024x1024',
                                                     prompt=prompt,
                                                     response_format='b64_json')

        b64 = response.data[0].b64_json
        if 'data:image' in b64:
            b64 = b64.split(',')[1]
        return io.BytesIO(base64.b64decode(b64)), response.data[0].revised_prompt


async def ai2text(response: AIResponse, model: str, chunk_size: int = 4000, show_tokens: bool = True) -> list[str]:
    text = f'<b>{model}</b>💬: ' + telegram_format(response.content)
    if show_tokens:
        text += f'\n~<code>{response.tokens}</code>'
    chunks = await chunker(text, chunk_size)
    return chunks
