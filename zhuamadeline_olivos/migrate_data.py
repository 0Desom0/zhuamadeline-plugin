# -*- coding: utf-8 -*-
"""zhuamadeline 数据迁移工具（NoneBot 版 -> OlivOS 版）

用法（在命令行运行）:

    # 方式一：从正在运行的 NoneBot 机器人目录迁移（推荐，带全部实时数据）
    python migrate_data.py --from-bot "D:\\你的nonebot机器人目录" --olivos "D:\\OlivOS根目录"

    # 方式二：从 zhuamadeline-plugin 仓库初始化（仓库内只有部分资源）
    python migrate_data.py --from-repo "C:\\Users\\Administrator\\OneDrive\\zhuamadeline-plugin" --olivos "D:\\OlivOS根目录"

说明:
- NoneBot 版数据位于机器人运行目录的 data/（Windows 下 data 与 Data 为同一目录）；
- OlivOS 版数据位于 <OlivOS根目录>/plugin/data/zhuamadeline/data/；
- 目录内部结构完全一致，本工具只做整目录复制与重命名映射；
- 已存在的目标文件默认跳过（--overwrite 可覆盖）。
"""
import argparse
import shutil
import sys
from pathlib import Path


def copy_tree(src: Path, dst: Path, overwrite: bool):
    if not src.exists():
        print(f'  [跳过] 源不存在: {src}')
        return 0
    count = 0
    for item in src.rglob('*'):
        rel = item.relative_to(src)
        target = dst / rel
        if item.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            continue
        if target.exists() and not overwrite:
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item, target)
        count += 1
    print(f'  [完成] {src.name} -> {dst}  (复制 {count} 个文件)')
    return count


def main():
    parser = argparse.ArgumentParser(description='zhuamadeline 数据迁移工具')
    parser.add_argument('--from-bot', help='NoneBot 机器人运行目录（内含 data 文件夹）')
    parser.add_argument('--from-repo', help='zhuamadeline-plugin 仓库目录')
    parser.add_argument('--olivos', required=True, help='OlivOS 根目录')
    parser.add_argument('--overwrite', action='store_true', help='覆盖已存在的目标文件')
    args = parser.parse_args()

    if not args.from_bot and not args.from_repo:
        parser.error('必须指定 --from-bot 或 --from-repo 之一')

    dst_base = Path(args.olivos) / 'plugin' / 'data' / 'zhuamadeline' / 'data'
    dst_base.mkdir(parents=True, exist_ok=True)
    total = 0

    if args.from_bot:
        src_data = Path(args.from_bot) / 'data'
        if not src_data.exists():
            src_data = Path(args.from_bot) / 'Data'
        if not src_data.exists():
            print(f'错误: 未在 {args.from_bot} 下找到 data/Data 目录')
            sys.exit(1)
        print(f'从机器人目录迁移: {src_data}')
        total += copy_tree(src_data, dst_base, args.overwrite)

    if args.from_repo:
        repo = Path(args.from_repo)
        print(f'从仓库初始化: {repo}')
        # 仓库目录名 -> OlivOS 数据目录名 映射
        mapping = {
            'MadelineLc1': 'madelineLc1',
            'MadelineLc2': 'madelineLc2',
            'MadelineLc3': 'madelineLc3',
            'MadelineLc4': 'madelineLc4',
            'MadelineLc5': 'madelineLc5',
            'qd_background': 'qd_background',
            'zhuamadeline_puzzle': 'Image',
            'UserList': 'UserList',
        }
        for src_name, dst_name in mapping.items():
            total += copy_tree(repo / src_name, dst_base / dst_name, args.overwrite)

    print()
    print(f'迁移完成，共复制 {total} 个文件。')
    print(f'目标目录: {dst_base}')
    print()
    print('请检查以下关键文件是否就位（缺失的请从原机器人目录手动补充）:')
    for need in [
        'UserList/UserData.json',
        'fonts/ZhanKu.ttf     (图文消息字体，缺失时退化为纯文本)',
        'madelineLc1/madeline1  (各猎场图鉴图片目录)',
        'Shop/开张图.png / 营业图.png',
        'DuChang/duchang.png',
        'group.jpg',
        'Image/  (解密图片)',
        'qd_background/  (签到背景)',
    ]:
        name = need.split()[0]
        mark = 'OK' if (dst_base / name).exists() else '缺失'
        print(f'  [{mark}] {need}')


if __name__ == '__main__':
    main()
