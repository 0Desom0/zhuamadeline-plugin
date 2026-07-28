import datetime
import shutil
import threading
import time

from nonebot import get_bot, get_driver, require
from nonebot.adapters.onebot.v11 import Bot
from nonebot.log import logger

from ..nbcompat.core import run_data_write_worker
from .config import backup_path, user_path, zhuama_group
from .function import lock as data_file_lock

require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler

_backup_lock = threading.Lock()


def _remove_backup_dir(path):
    """只允许删除备份根目录内的目录。"""
    backup_root = backup_path.resolve()
    target = path.resolve()
    if target == backup_root or backup_root not in target.parents:
        raise RuntimeError(f"拒绝删除备份目录之外的路径: {target}")
    shutil.rmtree(target)


def start_backup_thread(bot=None, group_id=None, delay=0.0, resolve_bot=False, name="manual"):
    """在独立写事务线程中执行备份，避免跨文件快照被业务写入打断。"""
    def worker():
        if delay > 0:
            time.sleep(delay)

        async def run_backup():
            target_bot = get_bot() if resolve_bot else bot
            return await backup_user_data(target_bot, group_id)

        try:
            run_data_write_worker(run_backup)
        except Exception as e:
            logger.error(f"备份线程执行失败: {e}")

    try:
        threading.Thread(
            target=worker,
            name=f"zhuamadeline-job-{name}-backup",
            daemon=True,
        ).start()
        return True
    except Exception as e:
        logger.error(f"备份线程创建失败: {e}")
        return False


async def cleanup_old_backups(max_backups=100):
    """清理旧备份，保留最多max_backups个"""
    try:
        backups = sorted(backup_path.glob("Backup_*"), key=lambda x: x.stat().st_ctime)
        if len(backups) > max_backups:
            for old_backup in backups[:len(backups)-max_backups]:
                _remove_backup_dir(old_backup)
                logger.info(f"已删除旧备份: {old_backup}")
    except Exception as e:
        logger.error(f"清理旧备份时出错: {e}")


async def backup_user_data(bot: Bot = None, group_id: int = None):
    """备份用户数据"""
    if not user_path.exists():
        logger.warning("用户数据目录不存在，跳过备份")
        return False
    if not _backup_lock.acquire(blocking=False):
        logger.info("已有用户数据备份正在执行，跳过本次备份")
        return False
    
    try:
        backup_path.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        backup_dir = backup_path / f"Backup_{timestamp}"
        temp_dir = backup_path / f".{backup_dir.name}-{threading.get_ident()}.tmp"

        # 写事务保证多文件处于同一业务时刻，文件锁避免复制撞上单次 JSON 写入。
        with data_file_lock:
            if temp_dir.exists():
                _remove_backup_dir(temp_dir)
            shutil.copytree(user_path, temp_dir)

        # 每次使用唯一目录名，完整复制成功后再原子改名为正式备份。
        if backup_dir.exists():
            raise FileExistsError(f"备份目录已存在: {backup_dir}")
        temp_dir.rename(backup_dir)
        logger.success(f"用户数据已备份到：{backup_dir}")

        await cleanup_old_backups()

        if bot and group_id:
            backups = sorted(backup_path.glob("Backup_*"), key=lambda x: x.stat().st_ctime)
            message = f"用户数据备份已完成"
            # 备份数量达到100不显示
            if int(len(backups)) < 100:
                message += f"\n当前备份数量: {len(backups)}/100"
            await bot.send_group_msg(group_id=group_id, message=message)
        
        return True
    except Exception as e:
        logger.error(f"备份过程中发生错误: {e}")
        return False
    finally:
        try:
            if 'temp_dir' in locals() and temp_dir.exists():
                _remove_backup_dir(temp_dir)
        except Exception as e:
            logger.error(f"清理备份临时目录失败: {e}")
        _backup_lock.release()


# 每天凌晨4点定时备份
@scheduler.scheduled_job("cron", hour=4, minute=0, id="daily_backup")
async def daily_backup():
    try:
        bot = get_bot()
        await backup_user_data(bot, zhuama_group)
    except Exception as e:
        logger.error(f"定时备份失败: {e}")


# 启动时创建延迟备份任务
@get_driver().on_startup
async def schedule_delayed_backup():
    """启动时调度延迟备份任务"""
    if start_backup_thread(
        group_id=zhuama_group,
        delay=5.0,
        resolve_bot=True,
        name="initial",
    ):
        logger.info("已创建延迟5秒的备份任务")
