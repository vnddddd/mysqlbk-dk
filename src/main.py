"""
MySQL备份系统主程序
整合所有组件，提供完整的备份解决方案
"""
import os
import sys
import logging
import signal
import time
from typing import List, Dict, Any
from datetime import datetime

from database_parser import DatabaseConnectionParser
from backup_manager import BackupManager
from b2_uploader import B2Uploader
from scheduler import BackupScheduler
from health_check import HealthChecker, HealthCheckServer


class MySQLBackupService:
    """MySQL备份服务主类"""
    
    def __init__(self):
        """初始化备份服务"""
        self.setup_logging()
        self.load_config()
        self.initialize_components()
        self.running = False
        
    def setup_logging(self):
        """设置日志配置"""
        log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
        logging.basicConfig(
            level=getattr(logging, log_level),
            format=log_format,
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler('/var/log/mysql-backup.log', mode='a') if os.path.exists('/var/log') else logging.NullHandler()
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("MySQL备份服务启动")
    
    def load_config(self):
        """加载配置"""
        try:
            # 必需的环境变量
            self.mysql_connections = os.getenv('MYSQL_CONNECTIONS')
            self.b2_key_id = os.getenv('B2_APPLICATION_KEY_ID')
            self.b2_key = os.getenv('B2_APPLICATION_KEY')
            self.b2_bucket = os.getenv('B2_BUCKET_NAME')
            
            if not all([self.mysql_connections, self.b2_key_id, self.b2_key, self.b2_bucket]):
                missing = []
                if not self.mysql_connections: missing.append('MYSQL_CONNECTIONS')
                if not self.b2_key_id: missing.append('B2_APPLICATION_KEY_ID')
                if not self.b2_key: missing.append('B2_APPLICATION_KEY')
                if not self.b2_bucket: missing.append('B2_BUCKET_NAME')
                
                raise ValueError(f"缺少必需的环境变量: {', '.join(missing)}")
            
            # 可选的环境变量
            self.backup_schedule = os.getenv('BACKUP_SCHEDULE', '0 4 * * *')
            self.retention_days = int(os.getenv('RETENTION_DAYS', '7'))
            self.health_check_port = int(os.getenv('HEALTH_CHECK_PORT', '8080'))
            self.run_initial_backup = os.getenv('RUN_INITIAL_BACKUP', 'true').lower() == 'true'
            
            self.logger.info("配置加载完成")
            self.logger.info(f"备份调度: {self.backup_schedule}")
            self.logger.info(f"保留天数: {self.retention_days}")
            self.logger.info(f"健康检查端口: {self.health_check_port}")
            
        except Exception as e:
            self.logger.error(f"加载配置失败: {str(e)}")
            raise
    
    def initialize_components(self):
        """初始化各个组件"""
        try:
            # 解析数据库连接
            all_connections = DatabaseConnectionParser.parse_connections(self.mysql_connections)

            # 过滤启用的连接
            self.db_connections = DatabaseConnectionParser.filter_enabled_connections(all_connections)

            # 按组分类连接
            self.connection_groups = DatabaseConnectionParser.get_connection_groups(self.db_connections)

            self.logger.info(f"解析到 {len(all_connections)} 个数据库连接，其中 {len(self.db_connections)} 个已启用")
            self.logger.info(f"连接分组情况: {list(self.connection_groups.keys())}")

            # 初始化组件
            self.backup_manager = BackupManager()
            self.b2_uploader = B2Uploader(self.b2_key_id, self.b2_key, self.b2_bucket)
            self.scheduler = BackupScheduler(self.run_backup, self.run_cleanup)
            self.health_checker = HealthChecker(self)
            self.health_server = HealthCheckServer(self.health_check_port, self.health_checker)

            # 设置调度时间
            self.scheduler.set_backup_schedule(self.backup_schedule)

            self.logger.info("组件初始化完成")

        except Exception as e:
            self.logger.error(f"初始化组件失败: {str(e)}")
            raise
    
    def test_connections(self) -> bool:
        """测试所有连接"""
        self.logger.info("开始测试连接...")

        # 按组测试数据库连接
        db_success = True
        total_connections = len(self.db_connections)

        for group_name, connections in self.connection_groups.items():
            self.logger.info(f"测试连接组: {group_name} ({len(connections)} 个连接)")

            for i, connection in enumerate(connections):
                conn_index = self.db_connections.index(connection) + 1
                self.logger.info(f"测试数据库连接 {conn_index}/{total_connections}: {DatabaseConnectionParser.get_connection_info(connection)}")
                if not self.backup_manager.test_connection(connection):
                    db_success = False

        # 测试B2连接
        self.logger.info("测试B2云存储连接...")
        b2_success = self.b2_uploader.test_connection()

        if db_success and b2_success:
            self.logger.info("所有连接测试成功")
            return True
        else:
            self.logger.error("连接测试失败")
            return False
    
    def run_backup(self) -> Dict[str, Any]:
        """执行备份任务"""
        start_time = datetime.now()
        self.logger.info("开始执行备份任务")

        results = {
            'start_time': start_time.isoformat(),
            'groups': {},
            'databases': [],
            'success_count': 0,
            'error_count': 0,
            'total_size': 0
        }

        try:
            # 按组执行备份
            for group_name, connections in self.connection_groups.items():
                self.logger.info(f"开始备份连接组: {group_name} ({len(connections)} 个数据库)")

                group_result = {
                    'group_name': group_name,
                    'databases': [],
                    'success_count': 0,
                    'error_count': 0,
                    'total_size': 0
                }

                for connection in connections:
                    db_result = {
                        'database': connection['database'],
                        'host': connection['host'],
                        'group_name': group_name,
                        'connection_id': connection.get('connection_id', ''),
                        'success': False,
                        'error': None,
                        'backup_file': None,
                        'size': 0
                    }

                    try:
                        self.logger.info(f"备份数据库: {DatabaseConnectionParser.get_connection_info(connection)}")

                        # 创建备份
                        backup_file = self.backup_manager.create_backup(connection)
                        if not backup_file:
                            raise Exception("备份文件创建失败")

                        # 获取文件大小
                        file_size = os.path.getsize(backup_file)
                        db_result['size'] = file_size
                        group_result['total_size'] += file_size
                        results['total_size'] += file_size

                        # 生成带组名的远程文件名
                        original_filename = os.path.basename(backup_file)
                        # 格式: backup_[group]_[database]_[timestamp].sql.gz
                        name_parts = original_filename.split('_')
                        if len(name_parts) >= 3:
                            remote_filename = f"backup_{group_name}_{name_parts[1]}_{name_parts[2]}"
                        else:
                            remote_filename = f"backup_{group_name}_{original_filename}"

                        # 上传到B2
                        if self.b2_uploader.upload_file(backup_file, remote_filename):
                            db_result['success'] = True
                            db_result['backup_file'] = remote_filename
                            group_result['success_count'] += 1
                            results['success_count'] += 1
                            self.logger.info(f"数据库备份成功: {connection['database']} -> {remote_filename}")
                        else:
                            raise Exception("上传到B2失败")

                        # 清理本地文件
                        self.backup_manager.cleanup_local_file(backup_file)

                    except Exception as e:
                        db_result['error'] = str(e)
                        group_result['error_count'] += 1
                        results['error_count'] += 1
                        self.logger.error(f"数据库备份失败 {connection['database']}: {str(e)}")

                    group_result['databases'].append(db_result)
                    results['databases'].append(db_result)

                results['groups'][group_name] = group_result
                self.logger.info(f"连接组 {group_name} 备份完成: 成功 {group_result['success_count']}, 失败 {group_result['error_count']}")
            
            # 记录备份操作
            success = results['error_count'] == 0
            self.health_checker.record_backup(success)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            results.update({
                'end_time': end_time.isoformat(),
                'duration_seconds': duration,
                'overall_success': success
            })
            
            self.logger.info(f"备份任务完成: 成功 {results['success_count']}, 失败 {results['error_count']}, 耗时 {duration:.2f}秒")
            
            return results
            
        except Exception as e:
            self.logger.error(f"备份任务执行失败: {str(e)}")
            self.health_checker.record_backup(False)
            results['error'] = str(e)
            results['overall_success'] = False
            return results
    
    def run_cleanup(self) -> Dict[str, Any]:
        """执行清理任务"""
        start_time = datetime.now()
        self.logger.info("开始执行清理任务")
        
        try:
            deleted_count = self.b2_uploader.delete_old_backups(self.retention_days)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            result = {
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'duration_seconds': duration,
                'deleted_count': deleted_count,
                'retention_days': self.retention_days,
                'success': True
            }
            
            self.health_checker.record_cleanup(True)
            self.logger.info(f"清理任务完成: 删除了 {deleted_count} 个过期备份文件")
            
            return result
            
        except Exception as e:
            self.logger.error(f"清理任务失败: {str(e)}")
            self.health_checker.record_cleanup(False)
            return {
                'start_time': start_time.isoformat(),
                'error': str(e),
                'success': False
            }
    
    def get_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        group_info = {}
        for group_name, connections in self.connection_groups.items():
            group_info[group_name] = {
                'connection_count': len(connections),
                'databases': [conn['database'] for conn in connections],
                'hosts': list(set(f"{conn['host']}:{conn['port']}" for conn in connections))
            }

        return {
            'healthy': self.running,
            'total_database_count': len(self.db_connections),
            'connection_groups': group_info,
            'b2_bucket': self.b2_bucket,
            'backup_schedule': self.backup_schedule,
            'retention_days': self.retention_days
        }
    
    def start(self):
        """启动服务"""
        try:
            # 测试连接
            if not self.test_connections():
                self.logger.error("连接测试失败，服务启动中止")
                return False
            
            # 启动健康检查服务器
            self.health_server.start()
            
            # 启动调度器
            self.scheduler.start()
            
            # 执行初始备份
            if self.run_initial_backup:
                self.logger.info("执行初始备份...")
                self.run_backup()
            
            self.running = True
            self.logger.info("MySQL备份服务启动成功")
            
            return True
            
        except Exception as e:
            self.logger.error(f"启动服务失败: {str(e)}")
            return False
    
    def stop(self):
        """停止服务"""
        self.logger.info("正在停止MySQL备份服务...")
        
        self.running = False
        
        # 停止调度器
        if hasattr(self, 'scheduler'):
            self.scheduler.stop()
        
        # 停止健康检查服务器
        if hasattr(self, 'health_server'):
            self.health_server.stop()
        
        self.logger.info("MySQL备份服务已停止")
    
    def run_forever(self):
        """持续运行服务"""
        if not self.start():
            sys.exit(1)
        
        # 设置信号处理
        def signal_handler(signum, frame):
            self.logger.info(f"收到信号 {signum}，正在停止服务...")
            self.stop()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("收到键盘中断，正在停止服务...")
            self.stop()


def main():
    """主函数"""
    service = MySQLBackupService()
    service.run_forever()


if __name__ == '__main__':
    main()
