import json
import string
import asyncio
from typing import Dict, List

import aiofiles
from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from async_timeout import timeout
from gsuid_core.models import Event
from gsuid_core.message_models import Button

from ..utils.load_data import load_test
from ..utils.resource_path import all_test, history_path

sv_test_help = SV('心理测试帮助')
sv_test_start = SV('心理测试开始')
sv_test_hot = SV('心理测试热门')

answer_map = {
    str(index + 1): i for index, i in enumerate(string.ascii_letters.upper())
}


@sv_test_help.on_fullmatch(('心理测试帮助', '心里测试帮助'))
async def send_help(bot: Bot, ev: Event):
    await bot.send_option(
        '欢迎来到心理测试!',
        [['热门测试', '全部测试列表'], ['心理测试帮助']],
        True,
        '\n',
        '【以下命令可用】：',
        '✅输入: ',
    )


@sv_test_help.on_fullmatch(('全部测试列表', '全部测试'))
async def send_all_test_list(bot: Bot, ev: Event):
    all_button_list = [
        Button(x.name, f'开始测试{x.name}', x.name) for x in all_test
    ]

    if len(all_button_list) >= 6:
        button_list = all_button_list[:6]
    else:
        button_list = all_button_list

    await bot.send_option(
        '\n下面是全部的测试列表噢，请任选一项开始测试吧！',
        button_list,
        True,
        '\n',
        '【以下命令可用】：',
        '✅输入: ',
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
            '\n下面是非常热门的测试噢！请选择一项吧！',
            [Button(x, f'开始测试{x}', x) for x in top_six_names],
            True,
            '\n',
            '【以下命令可用】：',
            '✅输入: ',
        )


@sv_test_start.on_command(('开始测试'))
async def send_test(bot: Bot, ev: Event):
    test_name = ev.text.strip()
    if not test_name:
        return await bot.send_option(
            '\n该功能后面需要接具体的测试项名称噢~\n查看帮助以获得更多信息！',
            ['热门测试', '全部测试列表', '心理测试帮助'],
            True,
            '\n',
            '【以下命令可用】：',
            '✅输入: ',
        )

    test = await load_test(test_name)
    if test is None:
        return await bot.send_option(
            '\n你输入的该测试不存在噢！\n请输入正确的测试名称！或者查看帮助以获得更多信息！',
            ['热门测试', '全部测试列表', '心理测试帮助'],
            True,
            '\n',
            '【以下命令可用】：',
            '✅输入: ',
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
            '\n',
            '【以下命令可用】：',
            '✅输入: ',
        )

    _path = []
    _answer = None
    _point = 0
    _key = []

    # 开始测试
    while True:
        try:
            async with timeout(60):
                user_answer = ''
                answer_hint = f'你选择的是 {user_answer}' if user_answer else ''
                answers = {a.detail: a for a in start.answer}
                all_answers = [
                    f'✅选{string.ascii_letters.upper()[index]}: {a}'
                    for index, a in enumerate(answers)
                ]
                send_answers = "\n".join(all_answers)
                send_msg = f'{answer_hint}\n{start.question}\n{send_answers}'
                resp = await bot.receive_resp(
                    send_msg,
                    [
                        '✅选' + string.ascii_letters.upper()[index]
                        for index in range(len(all_answers))
                    ],
                )
                if resp is not None:
                    user_answer = resp.text.strip()
                    if user_answer not in answers:
                        _user_answer = None

                        if _user_answer is None:
                            for index, i in enumerate(answer_map):
                                if len(user_answer) <= 4:
                                    user_answer = user_answer.upper()

                                    if (
                                        i in user_answer
                                        or answer_map[i] in user_answer
                                    ):
                                        _user_answer = start.answer[
                                            index
                                        ].detail
                                        break

                        if _user_answer is None:
                            _user_percent = 0
                            for _ans in start.answer:
                                sim = len(set(_ans.detail) & set(user_answer))
                                percent = 0.6 * len(_ans.detail)
                                if sim >= percent and _user_percent <= percent:
                                    _user_answer = _ans.detail
                                    _user_percent = percent

                        if _user_answer is None:
                            await bot.send('你的回答不在选项中噢...请重新回答!')
                            continue
                        else:
                            user_answer = _user_answer

                    _to = answers[user_answer].to
                    if _to == 'end':
                        _answer = _to
                        break
                    elif _to[0] == 'A' or _to[0] == 'a':
                        _answer = _to[1:]
                        break
                    _point += answers[user_answer].point
                    _key.extend(answers[user_answer].key)
                    _path.append(user_answer)
                    start = test.questions[_to]
                else:
                    break
        except asyncio.TimeoutError:
            return await bot.send_option(
                '\n回答问题超时噢, 可以重新开始测试~',
                ['热门测试', '全部测试列表', '心理测试帮助'],
                True,
                '\n',
                '【以下命令可用】：',
                '✅输入: ',
            )

    if _answer is None:
        return await bot.send_option(
            '\n回答问题超时噢, 可以重新开始测试~',
            ['热门测试', '全部测试列表', '心理测试帮助'],
            True,
            '\n',
            '【以下命令可用】：',
            '✅输入: ',
        )

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
                    await bot.send('👇测试结果出来了噢！')
                    await bot.send(f'\n【{result.title}】\n{result.detail}')
                    await bot.send_option(
                        '感谢喵~\n欢迎尝试更多测试!',
                        [['热门测试', '全部测试列表'], ['心理测试帮助']],
                        True,
                        '\n',
                        '【以下命令可用】：',
                        '✅输入: ',
                    )
    else:
        for _num in test.results:
            if _num == _answer:
                _title = _num
                result = test.results[_num]
                await bot.send('👇测试结果出来了噢！')
                await bot.send(f'\n【{result.title}】\n{result.detail}')
                await bot.send_option(
                    '感谢喵~\n欢迎尝试更多测试!',
                    ['热门测试', '全部测试列表', '心理测试帮助'],
                    True,
                    '\n',
                    '【以下命令可用】：',
                    '✅输入: ',
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
