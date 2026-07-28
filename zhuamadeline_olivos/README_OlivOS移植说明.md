# 抓玛德琳 OlivOS 移植版说明

本目录是 `zhuamadeline_nonebot_plugin`（NoneBot2 版）到 **OlivOS** 的完整移植。业务模块、命令入口、8 个调度任务、启动后延迟备份与冷却钩子均已保留，并针对 `qqGuildV2` 做了消息发送适配。

## 目录结构

```
zhuamadeline/            OlivOS 插件本体（源码目录格式）
├── app.json             插件自述文件（namespace=zhuamadeline, message_mode=old_string）
├── __init__.py          加载入口
├── main.py              OlivOS 事件入口（init/init_after/group_message/save）
├── nbcompat/            NoneBot2 兼容层（本次移植新写的核心）
│   ├── __init__.py      伪 nonebot 模块注入 + 数据目录初始化
│   └── core.py          Matcher/Message/Bot/scheduler/driver 等 API 的 OlivOS 实现
└── zm/                  原业务代码（近原样保留，见"移植改动清单"）
zhuamadeline.opk         上述插件的 opk 打包（二选一安装）
migrate_data.py          数据迁移脚本
```

## 工作原理

业务代码原本 `from nonebot import on_command` 等导入，移植版在插件 `init_after` 阶段先向 `sys.modules` 注入一套**伪 nonebot 模块**（由 `nbcompat` 实现），再加载业务包 `zm`。业务模块顶层的 `on_command(...)` 注册、`@scheduler.scheduled_job` 注册就会落到兼容层的注册表中；收到 OlivOS 群消息事件后，兼容层按 NoneBot 的语义（**最长前缀命令匹配**、fullmatch、白名单 rule、依赖注入、`finish/send`、block）驱动原 handler 运行。

- 业务层仍使用 `old_string`（CQ 码），兼容层发送前统一转换为 OlivOS 消息段；
- 被动命令统一引用触发消息，忽略 `at_sender` 并移除回复正文里的 at；
- `qqGuildV2` 主动消息只要含 at，就使用 Markdown at；若同时含图片，先发图片，再发 Markdown 文字；
- 图片和文字同发时统一调整为图片在前、文字在后，以匹配 `qqGuildV2` 的单条图文分组规则；
- 每次定时任务触发都会新建独立 daemon 线程，并在线程内运行该次协程；定时任务通过写事务门与普通命令的数据操作隔离，同一任务尚未结束时不会重入；启动与手动备份也在独立写事务线程中执行；
- `get_bot()` 主动发送使用同一账号的新伪事件，避免复用被动消息凭据或污染当前事件；
- 数据路径从"机器人运行目录/data"重定向到 `plugin/data/zhuamadeline/data`（见下文迁移）。

## 安装步骤

1. **装插件**（二选一）
   - 把 `zhuamadeline` 整个文件夹放入 `OlivOS根目录/plugin/app/`；
   - 或把 `zhuamadeline.opk` 放入 `OlivOS根目录/plugin/opk/`。
2. **装依赖**：在 OlivOS 使用的 Python 环境中执行
   ```
   pip install pillow numpy psutil
   ```
   （`requests` OlivOS 自带；`psutil` 仅 `.状态` 命令需要，缺失时该命令会提示而不影响其他功能。）
3. **迁数据**：
   ```
   python migrate_data.py --from-bot "你的NoneBot机器人目录" --olivos "OlivOS根目录"
   ```
   即把原机器人 `data/` 整个目录复制到 `plugin/data/zhuamadeline/data/`。没有旧机器人数据时，可用 `--from-repo "zhuamadeline-plugin仓库目录"` 从仓库初始化（注意仓库内没有 fonts/Shop/DuChang/group.jpg 等资源，脚本结束时会列出缺失清单）。
4. **确认 OlivOS 版本**：`qqGuildV2` 需要包含 `create_markdown_message`、引用消息和图片在前图文分组实现的当前 OlivOS 源码/构建；本仓库开发时核对的是用户提供的青果主项目。
5. **重启 OlivOS**，日志出现 `[zhuamadeline] 抓玛德琳插件加载完成` 即可。

## 数据目录对照

| 原 NoneBot 版 | OlivOS 版 |
|---|---|
| `<机器人目录>/data/UserList/` | `plugin/data/zhuamadeline/data/UserList/` |
| `<机器人目录>/data/madelineLc1~5/` | `plugin/data/zhuamadeline/data/madelineLc1~5/` |
| `<机器人目录>/data/fonts/ZhanKu.ttf` | `plugin/data/zhuamadeline/data/fonts/ZhanKu.ttf` |
| `<机器人目录>/data/Image、Shop、DuChang、qd_background、group.jpg 等` | 同名迁移 |

内部结构完全一致，直接整目录复制即可。备份目录（UserList_Backup）与图片缓存（generate_image）会自动创建。

## 移植改动清单（相对原 NoneBot 版）

除导入行 `from pathlib import Path` → `from .pathshim import Path` 与去 BOM/统一换行外，业务代码实质改动仅以下几处：

1. **news.py**：`httpx`（异步）改为 `requests` + 线程池，去掉一个第三方依赖，行为不变；
2. **function.py `emoji_like`**：原实现向 `localhost:9635` 发 HTTP（NoneBot 专用），改为调用 OlivOS 原生 `set_msg_emoji_like`（该函数目前无调用点，属预防性修复）；
3. **admin.py**：`psutil` 改为软依赖，缺失时 `.状态` 给出安装提示；
4. **text_image_text.py**：字体文件缺失时图文消息自动退化为纯文本；文字转图改为调用点显式开启，仅签到、shop 列表、成就列表、mymadeline、0 猎 PVP 保留生成图片；
5. **madelinejd.py `.count`**：修复原版 `user_id` 在赋值前被引用的 `UnboundLocalError`（原版查询不存在的名字时会静默无回复）；
6. **bet.py / item.py / pvp.py**：8 处 f-string 同引号嵌套写法改为 Python 3.11 兼容（原写法仅 3.12+ 可用，语义不变）。
7. **zhuamadeline.py / item.py**：`.zhua`、祈愿、单次抓捕道具和批量抓捕不再把原图与文案合成新图，改为原图在前、正文在后。
8. **nbcompat/core.py**：被动 at 改为消息引用；主动 at 在 `qqGuildV2` 使用 Markdown；主动事件与被动事件隔离；调度任务每次在独立线程运行。
9. **backup.py / admin.py**：启动与手动备份改为独立写事务线程；先复制到临时目录，成功后再原子改名为唯一的正式备份，避免跨文件不一致、半成品快照和同名备份互相覆盖。

配置内容（白名单群、管理员 QQ、猎场数等）全部原样保留在 `zm/config.py` / `zm/whitelist.py`，改动方式与原版相同。

## 与原版的行为差异（已知且可接受）

- 所有指令仅响应**群聊**（原版个别无 `permission=GROUP` 的命令理论上可私聊触发，实际从未使用）；
- 被动命令仍在共享事件循环上并发运行；定时任务每次在独立线程和独立事件循环中运行，并通过读写事务门避免结算与命令交叉覆盖共享 JSON；
- `qqGuildV2` 不支持 OneBot 合并转发；由命令触发的四处管理/谜题查询会降级为引用原消息的普通文本回复；
- 若同一 OlivOS 实例还挂了骰子等其他插件：本插件 priority=30000，命中命令后会 `set_block` 阻断后续插件；白名单外的群完全不响应、不阻断。注意 `.ck` 等命令与 OlivaDice 指令重名，请避免在白名单群里同时启用两者，或调整优先级。

## 验证情况

当前验证覆盖：全部业务模块加载、422 个命令 key、8 个 scheduler job、被动引用且无 at、图片优先顺序、`qqGuildV2` 主动 Markdown at、主动图片与 Markdown 分段、定时任务独立线程和防重入、图片生成白名单、Python 3.11 编译以及 OPK 与源码一致性。
