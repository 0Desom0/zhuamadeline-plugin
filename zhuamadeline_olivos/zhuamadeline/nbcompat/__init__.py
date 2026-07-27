# -*- coding: utf-8 -*-
'''NoneBot2 兼容层：模块注入与数据目录初始化'''

import os
import sys
import types

from . import core  # noqa: F401

DATA_BASE = os.path.join('plugin', 'data', core.NAMESPACE)

_installed = False


def _make_module(name, attrs):
    module = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(module, key, value)
    sys.modules[name] = module
    return module


def install_modules():
    '''向 sys.modules 注入 nonebot 系列伪模块（需在 import zm 之前调用）'''
    global _installed
    if _installed:
        return
    _installed = True

    nonebot = _make_module('nonebot', {
        'on_command': core.on_command,
        'on_fullmatch': core.on_fullmatch,
        'on_message': core.on_message,
        'get_bot': core.get_bot,
        'get_bots': core.get_bots,
        'get_driver': core.get_driver,
        'require': core.require,
        'logger': core.logger,
    })

    _make_module('nonebot.log', {
        'logger': core.logger,
    })

    _make_module('nonebot.params', {
        'CommandArg': core.CommandArg,
    })

    _make_module('nonebot.rule', {
        'Rule': core.Rule,
    })

    _make_module('nonebot.matcher', {
        'Matcher': core.Matcher,
    })

    _make_module('nonebot.exception', {
        'FinishedException': core.FinishedException,
        'IgnoredException': core.IgnoredException,
    })

    _make_module('nonebot.message', {
        'run_preprocessor': core.run_preprocessor,
        'event_postprocessor': core.event_postprocessor,
        'event_preprocessor': core.event_preprocessor,
    })

    adapters = _make_module('nonebot.adapters', {})

    onebot = _make_module('nonebot.adapters.onebot', {})

    v11 = _make_module('nonebot.adapters.onebot.v11', {
        'Bot': core.Bot,
        'Event': core.Event,
        'MessageEvent': core.MessageEvent,
        'GroupMessageEvent': core.GroupMessageEvent,
        'PrivateMessageEvent': core.PrivateMessageEvent,
        'Message': core.Message,
        'MessageSegment': core.MessageSegment,
        'GROUP': core.GROUP,
    })

    nonebot.adapters = adapters
    adapters.onebot = onebot
    onebot.v11 = v11

    _make_module('nonebot_plugin_apscheduler', {
        'scheduler': core.scheduler,
    })


def ensure_data_dirs():
    '''创建插件数据目录（不覆盖既有数据）'''
    for sub in [
        '',
        'data',
        os.path.join('data', 'UserList'),
        os.path.join('data', 'UserList_Backup'),
        os.path.join('data', 'generate_image'),
        os.path.join('data', 'fonts'),
        os.path.join('data', 'Shop'),
        os.path.join('data', 'DuChang'),
        os.path.join('data', 'Image'),
        os.path.join('data', 'qd_background'),
    ]:
        path = os.path.join(DATA_BASE, sub)
        try:
            os.makedirs(path, exist_ok=True)
        except Exception:
            pass
