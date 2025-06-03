"""
MySQL数据库备份管理器
处理数据库备份的创建和管理
"""
import os
import subprocess
import tempfile
import gzip
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import mysql.connector
from mysql.connector import Error

logger = logging.getLogger(__name__)


class BackupManager:
    """MySQL数据库备份管理器"""
    
    def __init__(self):
        """初始化备份管理器"""
        self.temp_dir = tempfile.gettempdir()
        
    def test_connection(self, connection: Dict[str, Any]) -> bool:
        """
        测试数据库连接
        
        Args:
            connection: 数据库连接配置
            
        Returns:
            bool: 连接是否成功
        """
        try:
            # 构建连接配置
            config = {
                'host': connection['host'],
                'port': connection['port'],
                'user': connection['username'],
                'password': connection['password'],
                'database': connection['database'],
                'connect_timeout': 10,
                'autocommit': True
            }
            
            # 添加SSL配置
            if connection.get('ssl_mode'):
                if connection['ssl_mode'].upper() == 'REQUIRED':
                    config['ssl_verify_cert'] = True
                    config['ssl_verify_identity'] = True
            
            # 尝试连接
            conn = mysql.connector.connect(**config)
            
            if conn.is_connected():
                cursor = conn.cursor()
                cursor.execute("SELECT VERSION()")
                version = cursor.fetchone()
                logger.info(f"数据库连接成功: {connection['host']}:{connection['port']}/{connection['database']} (MySQL {version[0]})")
                cursor.close()
                conn.close()
                return True
                
        except Error as e:
            logger.error(f"数据库连接失败 {connection['host']}:{connection['port']}/{connection['database']}: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"连接测试异常 {connection['host']}:{connection['port']}/{connection['database']}: {str(e)}")
            return False
        
        return False
    
    def create_backup(self, connection: Dict[str, Any]) -> Optional[str]:
        """
        创建数据库备份
        
        Args:
            connection: 数据库连接配置
            
        Returns:
            str: 备份文件路径，失败时返回None
        """
        try:
            # 生成备份文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"backup_{connection['database']}_{timestamp}.sql.gz"
            backup_path = os.path.join(self.temp_dir, backup_filename)
            
            logger.info(f"开始备份数据库: {connection['database']}")
            
            # 构建mysqldump命令
            cmd = [
                'mysqldump',
                f"--host={connection['host']}",
                f"--port={connection['port']}",
                f"--user={connection['username']}",
                f"--password={connection['password']}",
                '--single-transaction',
                '--routines',
                '--triggers',
                '--events',
                '--add-drop-database',
                '--create-options',
                '--disable-keys',
                '--extended-insert',
                '--quick',
                '--lock-tables=false',
                connection['database']
            ]
            
            # 添加SSL选项
            if connection.get('ssl_mode'):
                if connection['ssl_mode'].upper() == 'REQUIRED':
                    cmd.extend(['--ssl-mode=REQUIRED'])
            
            logger.debug(f"执行备份命令: {' '.join(cmd[:8])} [密码已隐藏] {' '.join(cmd[9:])}")
            
            # 执行mysqldump并压缩
            with open(backup_path, 'wb') as f:
                with gzip.GzipFile(fileobj=f, mode='wb') as gz_file:
                    process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        env=dict(os.environ, MYSQL_PWD=connection['password'])
                    )
                    
                    # 读取输出并写入压缩文件
                    while True:
                        chunk = process.stdout.read(8192)
                        if not chunk:
                            break
                        gz_file.write(chunk)
                    
                    # 等待进程完成
                    process.wait()
                    
                    if process.returncode != 0:
                        stderr_output = process.stderr.read().decode('utf-8')
                        logger.error(f"mysqldump执行失败: {stderr_output}")
                        if os.path.exists(backup_path):
                            os.remove(backup_path)
                        return None
            
            # 检查备份文件大小
            file_size = os.path.getsize(backup_path)
            if file_size == 0:
                logger.error("备份文件为空")
                os.remove(backup_path)
                return None
            
            logger.info(f"备份创建成功: {backup_filename} ({file_size} bytes)")
            return backup_path
            
        except subprocess.CalledProcessError as e:
            logger.error(f"mysqldump命令执行失败: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"创建备份失败: {str(e)}")
            return None
    
    def cleanup_local_file(self, file_path: str) -> bool:
        """
        清理本地备份文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            bool: 清理是否成功
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"本地备份文件已删除: {file_path}")
                return True
            else:
                logger.warning(f"文件不存在，无需删除: {file_path}")
                return True
        except Exception as e:
            logger.error(f"删除本地文件失败: {str(e)}")
            return False
    
    def get_database_info(self, connection: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        获取数据库信息
        
        Args:
            connection: 数据库连接配置
            
        Returns:
            dict: 数据库信息
        """
        try:
            config = {
                'host': connection['host'],
                'port': connection['port'],
                'user': connection['username'],
                'password': connection['password'],
                'database': connection['database'],
                'connect_timeout': 10
            }
            
            if connection.get('ssl_mode'):
                if connection['ssl_mode'].upper() == 'REQUIRED':
                    config['ssl_verify_cert'] = True
                    config['ssl_verify_identity'] = True
            
            conn = mysql.connector.connect(**config)
            cursor = conn.cursor()
            
            # 获取数据库版本
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()[0]
            
            # 获取数据库大小
            cursor.execute(f"""
                SELECT 
                    ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS size_mb
                FROM information_schema.tables 
                WHERE table_schema = '{connection['database']}'
            """)
            size_result = cursor.fetchone()
            size_mb = size_result[0] if size_result[0] else 0
            
            # 获取表数量
            cursor.execute(f"""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = '{connection['database']}'
            """)
            table_count = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            return {
                'version': version,
                'size_mb': float(size_mb),
                'table_count': table_count,
                'database': connection['database']
            }
            
        except Exception as e:
            logger.error(f"获取数据库信息失败: {str(e)}")
            return None
