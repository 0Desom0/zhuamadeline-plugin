# -*- coding: utf-8 -*-
'''路径垫片：把原插件基于运行目录的相对路径重定向到 OlivOS 插件数据目录

原 NoneBot 插件中大量使用 `Path() / "data" / ...`、`Path("data") / ...`
形式的相对路径（相对 bot 运行目录），且存在 data/Data、UserList/Userlist
大小写混用（Windows 不区分大小写故可运行）。本模块提供替代 `Path`：

- Path()                  -> plugin/data/zhuamadeline
- Path("data"/"Data")     -> plugin/data/zhuamadeline/data
- Path(其他参数)           -> 原生 pathlib.Path 行为

并在路径拼接时对 data / UserList / UserList_Backup 三个目录名做大小写
归一化，保证在 Linux 等大小写敏感文件系统上也能正确运行。

业务代码只需把 `from pathlib import Path` 换成 `from .pathshim import Path`，
其余路径拼接语句原样保留。
'''

import pathlib
import sys

# 需要大小写归一化的目录名
_CANON = {
    'data': 'data',
    'userlist': 'UserList',
    'userlist_backup': 'UserList_Backup',
}

_Native = type(pathlib.Path())  # PosixPath / WindowsPath


class ZmPath(_Native):
    '''在拼接时对关键目录名做大小写归一化的 Path'''

    if sys.version_info < (3, 12):
        _flavour = _Native._flavour

    def __truediv__(self, key):
        try:
            k = str(key)
            canon = _CANON.get(k.lower())
            if canon is not None:
                k = canon
            return ZmPath(_Native.__truediv__(self, k))
        except Exception:
            return _Native.__truediv__(self, key)


# OlivOS 运行时工作目录固定为 OlivOS 根目录
DATA_BASE = ZmPath('plugin') / 'data' / 'zhuamadeline'


def Path(*args, **kwargs):
    if len(args) == 0:
        return DATA_BASE
    if len(args) == 1 and isinstance(args[0], str) and args[0].lower() == 'data':
        return DATA_BASE / 'data'
    return pathlib.Path(*args, **kwargs)
