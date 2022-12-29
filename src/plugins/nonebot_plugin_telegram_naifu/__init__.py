import json
import re
from base64 import b64decode
from random import randint

from colorama import Fore
from nonebot import get_driver, on_command, on_regex
from nonebot.adapters.telegram import Bot
from nonebot.adapters.telegram.event import MessageEvent
from nonebot.adapters.telegram.model import (
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from nonebot.exception import ActionFailed
from nonebot.log import logger

from .config import Config
from .utils import get_userid, get_data, get_config

__version__ = "0.0.1"

switch = True

config = get_config()

# config
global_config = get_driver().config
post_url = config['post_url']
prompt = config['prompt']
assets_path = 'naifu/src/plugins/nonebot_plugin_telegram_naifu/assets/'

# command
start = on_command("start", priority=5, block=True)
status = on_command("status", priority=5, block=True)
reply = on_command("reply", priority=5, block=True)
nai = on_command("nai", priority=5, block=True)
nai_more = on_command("nai_more", priority=5, block=True)
set_url = on_command("set_url", priority=5, block=True)
set_prompt = on_command("set_prompt", priority=5, block=True)
# regex
nai_regex = on_regex(pattern=r"nai_regex", priority=5, block=True)
nai_more_regex = on_regex(pattern=r"nai_more_regex", priority=5, block=True)
menu1 = on_regex(pattern=r"menu1", priority=5, block=True)
menu2 = on_regex(pattern=r"menu2", priority=5, block=True)


# 测试
@reply.handle()
async def reply(bot: Bot, event: MessageEvent):
    await bot.send(event, "我返回了你一条信息", reply_to_message_id=event.message_id)


@start.handle()
async def _(bot: Bot, event: MessageEvent):
    keyboards = [
        [
            InlineKeyboardButton(text='1张图', callback_data='nai_regex', url=''),
            InlineKeyboardButton(text='3张图', callback_data='nai_more_regex', url='')
        ],
        [InlineKeyboardButton(text='menu1', callback_data='menu1', url='')],
        [InlineKeyboardButton(text='menu2', callback_data='menu2', url='')],
    ]
    await bot.send(
        event,
        "主菜单",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=keyboards
        ).json(),
    )


@menu1.handle()
async def _(bot: Bot, event: MessageEvent):
    keyboards = [
        [InlineKeyboardButton('Submenu 1-1', callback_data='m1_1', url='')],
        [InlineKeyboardButton('Submenu 1-2', callback_data='m1_2', url='')],
        [InlineKeyboardButton('Main menu', callback_data='main', url='')]
    ]
    await bot.send(
        event,
        "1菜单",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=keyboards
        ).json(),
    )


@menu2.handle()
async def _(bot: Bot, event: MessageEvent):
    keyboards = [
        [InlineKeyboardButton('Submenu 2-1', callback_data='m2_1', url='')],
        [InlineKeyboardButton('Submenu 2-2', callback_data='m2_2', url='')],
        [InlineKeyboardButton('Main menu', callback_data='main', url='')]
    ]
    await bot.send(
        event,
        "2菜单",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=keyboards
        ).json(),
    )


@set_prompt.handle()
async def _(event: MessageEvent):
    global prompt
    msg_search = re.search(r"\s+(?P<prompt>.*)", str(event.message))
    prompt = msg_search.group('prompt')
    logger.info(prompt)
    new_dict = json.load(open('config.json'))
    new_dict['prompt'] = prompt
    with open("config.json", "w") as outfile:
        json.dump(new_dict, outfile)
        print("标签写入文件完成...")
    await set_prompt.finish(f"prompt设置成功, 设置将在下一次请求时启用. 当前描述: {prompt}")


# 设置后端URL
@set_url.handle()
async def _(event: MessageEvent):
    global post_url
    urls = re.findall('https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+', str(event.message))
    post_url = urls[0] + "/generate-stream"
    logger.success(Fore.LIGHTCYAN_EX + f"当前后端URL：{post_url}")
    new_dict = json.load(open('config.json'))
    new_dict['post_url'] = post_url
    with open("config.json", "w") as outfile:
        json.dump(new_dict, outfile)
        print("接口写入文件完成...")
    await set_url.finish(f"url设置成功, 设置将在下一次请求时启用. 当前地址: {post_url}")


# 查看当前状态
@status.handle()
async def _(bot: Bot, event: MessageEvent):
    keyboards = [
        [
            InlineKeyboardButton(
                text="Nonebot的telegram适配器",
                url="https://github.com/nonebot/adapter-telegram",
            )
        ],
        [
            InlineKeyboardButton(
                text="Telegram适配器案例",
                url="https://github.com/nonebot/adapter-telegram/blob/beta/example/photo.py",
            )
        ],
        [
            InlineKeyboardButton(
                text="基于naifu的插件案例",
                url="https://github.com/ZYKsslm/nonebot_plugin_zyk_novelai/blob/main/nonebot_plugin_zyk_novelai/__init__.py",
            )
        ],
        [
            InlineKeyboardButton(
                text="Telegram机器人API",
                url="https://core.telegram.org/bots/api",
            )
        ],
        [
            InlineKeyboardButton(
                text="Colab的naifu地址",
                url=f"{str(post_url)}",
            )
        ]
    ]
    await bot.send(
        event,
        "Hello InlineKeyboard !",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=keyboards
        ).json(),
    )


@nai.handle()
async def _(bot: Bot, event: MessageEvent):
    data_list = await generate(bot, event, 1)
    image = b64decode(data_list[0])

    try:
        await bot.send_photo(
            chat_id=event.chat.id,
            photo=image,
            caption="AiCat"
        )
        await nai.finish("图片生成完毕! 使用原生 API 发送图片")
    except ActionFailed:
        logger.warning(Fore.LIGHTYELLOW_EX + "Bot可能被风控，请稍后再试")
        await nai.finish("Bot可能被风控，请稍后再试")


@nai_regex.handle()
async def _(bot: Bot, event: MessageEvent):
    logger.info("打开啊第几")
    data_list = await generate(bot, event, 1)
    image = b64decode(data_list[0])

    try:
        await bot.send_photo(
            chat_id=event.chat.id,
            photo=image,
            caption="AiCat"
        )
        await nai.finish("图片生成完毕! 使用原生 API 发送图片")
    except ActionFailed:
        logger.warning(Fore.LIGHTYELLOW_EX + "Bot可能被风控，请稍后再试")
        await nai.finish("Bot可能被风控，请稍后再试")


@nai_more.handle()
async def _(bot: Bot, event: MessageEvent):
    num = 3
    data_list = await generate(bot, event, num)

    fo = open("info.txt", "w")
    fo.write(str(data_list))
    fo.close()
    logger.success('生成多张图片info文件写入成功')

    image1 = b64decode(data_list[0])
    image2 = b64decode(data_list[1])
    image3 = b64decode(data_list[2])

    # i = 0
    # media_list = []
    # while i < num:
    #     media_list.append()
    #     i = i + 1

    logger.success(Fore.LIGHTYELLOW_EX + "数据处理完毕,准备返回")
    try:
        # await bot.send_media_group(
        #     chat_id=event.chat.id,
        #     media=[
        #         InputMediaPhoto(
        #             media=image1, caption="基于NaifuAi001"
        #         ), InputMediaPhoto(
        #             media=image2, caption="基于NaifuAi002"
        #         ), InputMediaPhoto(
        #             media=image3, caption="基于NaifuAi003"
        #         )
        #     ],
        # )
        await bot.send_photo(
            chat_id=event.chat.id, photo=image1, caption="基于NaifuAi"
        )
        await bot.send_photo(
            chat_id=event.chat.id, photo=image2, caption="基于NaifuAi"
        )
        await bot.send_photo(
            chat_id=event.chat.id, photo=image3, caption="基于NaifuAi"
        )
        await bot.send(event, f"使用原生API发送{num}张图片")
        await nai_more.finish("图片生成完毕! ")
    except ActionFailed:
        logger.warning(Fore.LIGHTYELLOW_EX + "Bot可能被风控，请稍后再试")
        await nai_more.finish("Bot可能被风控，请稍后再试")


# 请求naifu的方法
async def generate(bot: Bot, event: MessageEvent, n_samples):
    global switch
    global prompt
    global post_url

    if switch is False:
        await bot.send(event, "资源占用中!")
        return

    height = 768
    prompt = prompt
    sampler = "k_euler_ancestral"
    scale = 12
    seed = randint(0, pow(2, 32))
    steps = 28
    uc = "lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry"
    width = 512

    id_ = get_userid(event)
    name = id_ + ''

    logger.info(
        Fore.LIGHTYELLOW_EX +
        f"\n开始生成{name}的图片："
        f"\nscale={scale}"
        f"\nsteps={steps}"
        f"\nsize={width},{height}"
        f"\nsampler={sampler}"
        f"\nseed={seed}"
        f"\nprompt={prompt}"
        f"\nnegative prompt={uc}"
    )
    switch = False
    data = await get_data(
        post_url=post_url,
        width=width,
        height=height,
        prompt=prompt,
        proxies={},
        timeout=180,
        uc=uc,
        steps=steps,
        scale=scale,
        seed=seed,
        sampler=sampler,
        n_samples=n_samples
    )
    switch = True
    if data[0] is False:
        logger.error(Fore.LIGHTRED_EX + f"后端请求失败")

    logger.success(Fore.LIGHTGREEN_EX + f"{name}的图片生成成功")

    data_list = json.loads(data[1])

    return data_list


logger.success(Fore.LIGHTGREEN_EX + f"成功导入本插件，插件版本为{__version__}")
