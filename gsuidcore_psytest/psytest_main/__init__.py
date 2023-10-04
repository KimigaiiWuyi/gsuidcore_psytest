import json
from typing import Dict, List, Union

import aiofiles
from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event
from gsuid_core.message_models import Button

from ..utils.load_data import load_test
from ..utils.resource_path import all_test, history_path

sv_test_help = SV('心理测试帮助')
sv_test_start = SV('心理测试开始')
sv_test_hot = SV('心理测试热门')


@sv_test_help.on_fullmatch(('心理测试帮助'))
async def send_help(bot: Bot, ev: Event):
    await bot.send_option(
        '欢迎来到心理测试!',
        ['热门测试', '全部测试列表', '心理测试帮助'],
        True,
    )


@sv_test_help.on_fullmatch(('全部测试列表', '全部测试'))
async def send_all_test_list(bot: Bot, ev: Event):
    all_button_list: List[Union[Button, str]] = [
        Button(x.name, f'开始测试{x.name}', x.name) for x in all_test
    ]

    if len(all_button_list) >= 6:
        button_list = all_button_list[:6]
    else:
        button_list = all_button_list

    await bot.send_option(
        '欢迎来到心理测试!',
        button_list,
        True,
    )


@sv_test_hot.on_fullmatch(('心理测试热门', '热门测试'))
async def send_hot(bot: Bot, ev: Event):
    sorted_files = sorted(
        all_test, key=lambda x: x.stat().st_size, reverse=True
    )
    top_six_files = sorted_files[:6]
    top_six_names = [str(x.name) for x in top_six_files]
    if top_six_names == []:
        await bot.send('目前还没有非常热门的测试噢，请@我输入 全部测试列表 查看完整测试！')
    else:
        await bot.send_option(
            '以下测试非常热门噢！请选择一项吧！',
            [Button(x, f'开始测试{x}', x) for x in top_six_names],
        )


@sv_test_start.on_prefix(('开始测试'))
async def send_test(bot: Bot, ev: Event):
    test_name = ev.text
    test = await load_test(test_name)
    if test is None:
        return await bot.send_option(
            '该测试不存在噢！请输入正确的测试名称！或者查看帮助以获得更多信息！',
            ['热门测试', '全部测试列表', '心理测试帮助'],
            True,
        )

    if 'start' in test.questions:
        start = test.questions['start']
    elif '1' in test.questions:
        start = test.questions['1']
    else:
        return await bot.send_option(
            '该测试不存在噢！请输入正确的测试名称！或者查看帮助以获得更多信息！',
            ['热门测试', '全部测试列表', '心理测试帮助'],
            True,
        )

    _path = []
    _answer = None
    _point = 0
    _key = []

    # 开始测试
    while True:
        resp = await bot.receive_resp(
            start.question, [a for a in start.answer], True
        )
        if resp is not None:
            user_answer = resp.text.strip()
            if user_answer not in start.answer:
                await bot.send('你的回答不在选项中噢...请重新回答!')
                continue
            _to = start.answer[user_answer].to
            if _to == 'end':
                _answer = _to
                break
            elif _to[0] == 'A' or _to[0] == 'a':
                _answer = _to[1:]
                break
            _point += start.answer[user_answer].point
            _key.extend(start.answer[user_answer].key)
            _path.append(user_answer)
            start = test.questions[_to]
        else:
            break

    if _answer is None:
        return await bot.send('回答问题超时噢, 可以重新开始测试~, @我并发送 心理测试帮助 可以获得更多信息！')

    result = None
    _title = None

    # 结束
    if _answer == 'end':
        for _num in test.results:
            _title = _num
            result = test.results[_num]
            if _point >= result.point_down and _point <= result.point_up:
                _need_key = set(result.need_key)
                _self_key = set(_key)
                if _need_key.issubset(_self_key):
                    await bot.send_option(
                        result.detail, ['热门测试', '全部测试列表', '心理测试帮助'], True
                    )
    else:
        for _num in test.results:
            if _num == _answer:
                _title = _num
                result = test.results[_num]
                await bot.send_option(
                    result.detail, ['热门测试', '全部测试列表', '心理测试帮助'], True
                )

    if result is not None:
        # 保存每个人的结果
        _record = {
            'bot_id': ev.real_bot_id,
            'group': ev.group_id,
            'user': ev.user_id,
            'path': _path,
            'point': _point,
            'key': _key,
            'answer': _answer,
            'result': _title,
        }

        path = history_path / f'{test_name}.json'
        if not path.exists():
            record = [_record]
            async with aiofiles.open(path, 'x', encoding='UTF-8') as f:
                await f.write(json.dumps(record, ensure_ascii=False, indent=4))
        else:
            async with aiofiles.open(path, 'x', encoding='UTF-8') as f:
                record: List[Dict] = json.loads(await f.read())
                record.append(_record)
                await f.write(json.dumps(record, ensure_ascii=False, indent=4))
