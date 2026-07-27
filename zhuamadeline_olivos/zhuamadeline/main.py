# -*- coding: utf-8 -*-
'''zhuamadeline OlivOS 插件入口

抓玛德琳群游戏插件（NoneBot2 -> OlivOS 移植版）。

结构说明：
- nbcompat/ : NoneBot2 兼容层，把 on_command / Matcher / scheduler 等
  API 映射到 OlivOS 事件模型上；
- zm/       : 原 zhuamadeline_nonebot_plugin 业务代码（近乎原样保留）。

业务代码在 init_after 阶段才真正加载：先向 sys.modules 注入伪造的
nonebot 系列模块，再 import zm 包，业务模块顶层的 on_command 注册、
定时任务注册便会落到兼容层的注册表中。
'''

import traceback

from . import nbcompat

gFlagReady = False


class Event(object):
    def init(plugin_event, Proc):
        # import 阶段不做重活，仅确保数据目录存在
        try:
            nbcompat.ensure_data_dirs()
        except Exception:
            Proc.log(4, '[zhuamadeline] 数据目录初始化失败:\n' + traceback.format_exc())

    def init_after(plugin_event, Proc):
        # 注入兼容模块并加载业务代码（按优先级顺序执行）
        global gFlagReady
        nbcompat.core.set_proc(Proc)
        try:
            nbcompat.install_modules()
            import importlib
            importlib.import_module('.zm', package=__package__)  # 触发全部命令/定时任务注册
            nbcompat.core.start_runtime()
            gFlagReady = True
            Proc.log(2, '[zhuamadeline] 抓玛德琳插件加载完成')
        except Exception:
            Proc.log(4, '[zhuamadeline] 插件加载失败:\n' + traceback.format_exc())

    def group_message(plugin_event, Proc):
        # 群消息事件入口
        if not gFlagReady:
            return
        try:
            nbcompat.core.dispatch_group_message(plugin_event, Proc)
        except Exception:
            Proc.log(4, '[zhuamadeline] 群消息处理异常:\n' + traceback.format_exc())

    def private_message(plugin_event, Proc):
        # 原插件所有指令均为群聊指令（permission=GROUP），私聊不处理
        pass

    def save(plugin_event, Proc):
        # 业务数据均为随写随存，无需额外保存动作
        pass

    def menu(plugin_event, Proc):
        pass
