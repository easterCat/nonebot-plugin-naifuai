import json
from re import findall

from fake_useragent import UserAgent
from httpx import AsyncClient, ConnectTimeout
from nonebot import logger


def get_userid(event):
    info = str(event.get_session_id())
    try:
        res = findall(r"group_(?P<group_id>\d+)_(?P<member_id>\d+)", info)[0]
    except IndexError:
        id_ = info
    else:
        id_ = res[1]

    return id_


async def get_data(
        post_url, prompt, proxies, timeout,
        img=None, mode=None, strength=None, n_samples=None,
        noise=None, sampler=None, uc=None,
        scale=None, steps=None, seed=None, width=None, height=None
):
    data = {
        "height": height,
        "n_samples": n_samples,
        "prompt": prompt,
        "sampler": sampler,
        "scale": scale,
        "seed": seed,
        "steps": steps,
        "uc": uc,
        "ucPreset": 0,
        "width": width,
    }

    headers = {
        "User-Agent": UserAgent().random
    }

    if mode == "以图生图":
        data.update(
            {
                "strength": strength,
                "noise": noise,
                "image": img
            }
        )

    async with AsyncClient(headers=headers, proxies=proxies, timeout=timeout) as client:
        try:
            resp = await client.post(url=post_url, json=data)
        except ConnectTimeout:
            return False, "时间超过限制！"
        info = resp.text

        # 获取错误
        if "data:" not in info:
            return False, info

        base64_list = findall(r'data:(?P<base64>.*)', info)

        return True, json.dumps(base64_list)


def get_config():
    f = open('config.json')
    config = json.load(f)
    f.close()
    logger.info(f'当前保存的配置{config}')
    return config
