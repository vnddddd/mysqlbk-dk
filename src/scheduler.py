"""
备份任务调度器
处理定时备份任务的调度和执行
"""
import schedule
import time
import threading
import logging
from datetime import datetime
from typing import List, Dict, Any, Callable
from croniter import croniter

logger = logging.getLogger(__name__)


class BackupScheduler:
    """备份任务调度器"""
    
    def __init__(self, backup_function: Callable, cleanup_function: Callable):
        """
        初始化调度器
        
        Args:
            backup_function: 备份执行函数
            cleanup_function: 清理执行函数
        """
        self.backup_function = backup_function
        self.cleanup_function = cleanup_function
        self.running = False
        self.scheduler_thread = None
        self.backup_schedule = "0 4 * * *"  # 默认每天4点
        self.cleanup_schedule = "0 5 * * *"  # 默认每天5点清理
        
    def set_backup_schedule(self, cron_expression: str):
        """
        设置备份调度时间
        
        Args:
            cron_expression: Cron表达式
        """
        try:
            # 验证cron表达式
            croniter(cron_expression)
            self.backup_schedule = cron_expression
            logger.info(f"备份调度时间已设置: {cron_expression}")
        except Exception as e:
            logger.error(f"无效的cron表达式: {cron_expression}, 错误: {str(e)}")
            raise ValueError(f"无效的cron表达式: {cron_expression}")
    
    def set_cleanup_schedule(self, cron_expression: str):
        """
        设置清理调度时间
        
        Args:
            cron_expression: Cron表达式
        """
        try:
            croniter(cron_expression)
            self.cleanup_schedule = cron_expression
            logger.info(f"清理调度时间已设置: {cron_expression}")
        except Exception as e:
            logger.error(f"无效的cron表达式: {cron_expression}, 错误: {str(e)}")
            raise ValueError(f"无效的cron表达式: {cron_expression}")
    
    def _parse_cron_to_schedule(self, cron_expression: str) -> str:
        """
        将cron表达式转换为schedule库可用的格式

        Args:
            cron_expression: Cron表达式 (分 时 日 月 周)

        Returns:
            str: schedule时间格式
        """
        parts = cron_expression.split()
        if len(parts) != 5:
            raise ValueError("Cron表达式必须包含5个部分: 分 时 日 月 周")

        minute, hour, day, month, weekday = parts

        # 简单的cron解析，支持基本格式
        if minute == "0" and hour != "*" and day == "*" and month == "*" and weekday == "*":
            # 每天特定时间，确保小时是两位数格式
            hour_int = int(hour)
            return f"{hour_int:02d}:00"

        # 更复杂的cron表达式需要使用croniter
        return None
    
    def _schedule_with_cron(self, cron_expression: str, job_function: Callable):
        """
        使用cron表达式调度任务
        
        Args:
            cron_expression: Cron表达式
            job_function: 要执行的函数
        """
        def cron_job():
            try:
                cron = croniter(cron_expression, datetime.now())
                next_run = cron.get_next(datetime)
                
                while self.running:
                    now = datetime.now()
                    if now >= next_run:
                        logger.info(f"执行定时任务: {job_function.__name__}")
                        try:
                            job_function()
                        except Exception as e:
                            logger.error(f"定时任务执行失败: {str(e)}")
                        
                        # 计算下次执行时间
                        cron = croniter(cron_expression, now)
                        next_run = cron.get_next(datetime)
                        logger.info(f"下次执行时间: {next_run}")
                    
                    time.sleep(60)  # 每分钟检查一次
                    
            except Exception as e:
                logger.error(f"Cron调度器错误: {str(e)}")
        
        return cron_job
    
    def start(self):
        """启动调度器"""
        if self.running:
            logger.warning("调度器已在运行")
            return
        
        self.running = True
        
        # 清除现有的调度任务
        schedule.clear()
        
        # 尝试使用简单的schedule库调度
        backup_time = self._parse_cron_to_schedule(self.backup_schedule)
        cleanup_time = self._parse_cron_to_schedule(self.cleanup_schedule)
        
        if backup_time:
            schedule.every().day.at(backup_time).do(self._safe_backup_job)
            logger.info(f"使用schedule库调度备份任务: 每天 {backup_time}")
        else:
            # 使用cron调度器
            backup_cron_job = self._schedule_with_cron(self.backup_schedule, self._safe_backup_job)
            backup_thread = threading.Thread(target=backup_cron_job, daemon=True)
            backup_thread.start()
            logger.info(f"使用cron调度器调度备份任务: {self.backup_schedule}")
        
        if cleanup_time:
            schedule.every().day.at(cleanup_time).do(self._safe_cleanup_job)
            logger.info(f"使用schedule库调度清理任务: 每天 {cleanup_time}")
        else:
            # 使用cron调度器
            cleanup_cron_job = self._schedule_with_cron(self.cleanup_schedule, self._safe_cleanup_job)
            cleanup_thread = threading.Thread(target=cleanup_cron_job, daemon=True)
            cleanup_thread.start()
            logger.info(f"使用cron调度器调度清理任务: {self.cleanup_schedule}")
        
        # 启动schedule调度器线程
        self.scheduler_thread = threading.Thread(target=self._run_schedule, daemon=True)
        self.scheduler_thread.start()
        
        logger.info("备份调度器已启动")
    
    def stop(self):
        """停止调度器"""
        self.running = False
        schedule.clear()
        
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5)
        
        logger.info("备份调度器已停止")
    
    def _run_schedule(self):
        """运行schedule调度器"""
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(60)  # 每分钟检查一次
            except Exception as e:
                logger.error(f"调度器运行错误: {str(e)}")
                time.sleep(60)
    
    def _safe_backup_job(self):
        """安全的备份任务包装器"""
        try:
            logger.info("开始执行定时备份任务")
            self.backup_function()
            logger.info("定时备份任务完成")
        except Exception as e:
            logger.error(f"定时备份任务失败: {str(e)}")
    
    def _safe_cleanup_job(self):
        """安全的清理任务包装器"""
        try:
            logger.info("开始执行定时清理任务")
            self.cleanup_function()
            logger.info("定时清理任务完成")
        except Exception as e:
            logger.error(f"定时清理任务失败: {str(e)}")
    
    def run_backup_now(self):
        """立即执行备份任务"""
        logger.info("手动触发备份任务")
        self._safe_backup_job()
    
    def run_cleanup_now(self):
        """立即执行清理任务"""
        logger.info("手动触发清理任务")
        self._safe_cleanup_job()
    
    def get_next_run_times(self) -> Dict[str, str]:
        """
        获取下次执行时间
        
        Returns:
            dict: 包含备份和清理的下次执行时间
        """
        try:
            now = datetime.now()
            
            backup_cron = croniter(self.backup_schedule, now)
            next_backup = backup_cron.get_next(datetime)
            
            cleanup_cron = croniter(self.cleanup_schedule, now)
            next_cleanup = cleanup_cron.get_next(datetime)
            
            return {
                'next_backup': next_backup.strftime('%Y-%m-%d %H:%M:%S'),
                'next_cleanup': next_cleanup.strftime('%Y-%m-%d %H:%M:%S')
            }
        except Exception as e:
            logger.error(f"获取下次执行时间失败: {str(e)}")
            return {
                'next_backup': 'Unknown',
                'next_cleanup': 'Unknown'
            }
