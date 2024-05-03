import asyncio
import io
import typing

import aiogram
from aiogram.enums import ChatAction
from openai import AsyncOpenAI
import aiohttp

from extra.constants import llm_system_message
from extra.exceptions import AIException


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
        async with aiohttp.ClientSession() as session:
            async with session.post(f'https://visioncraft.top/{variant}', json={
                'token': self.api_key,
                'prompt': prompt,
                'size': '1024x1024'
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
            list[dict[str, str]]:
        messages = [{'role': 'user', 'content': prompt}] if messages is None else messages + [
            {'role': 'user', 'content': prompt}]
        client = AsyncOpenAI(api_key=self.api_key, base_url='https://visioncraft.top/v1')

        chat_completion = await client.chat.completions.create(stream=kwargs.get('stream', False), model=model,
                                                               messages=messages + [
                                                                   {'role': 'user', 'content': prompt}])
        if chat_completion.id is None:
            raise AIException.Error(chat_completion.error['message'])
        return messages + [{'role': 'assistant', 'content': chat_completion.choices[0].message.content}]

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
