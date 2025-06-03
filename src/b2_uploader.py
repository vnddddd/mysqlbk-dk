"""
Backblaze B2云存储上传管理器
处理备份文件的上传和清理
"""
import os
import logging
from datetime import datetime, timedelta
from typing import List, Optional
from b2sdk.v2 import InMemoryAccountInfo, B2Api, FileVersion
import tempfile

logger = logging.getLogger(__name__)


class B2Uploader:
    """Backblaze B2云存储管理器"""
    
    def __init__(self, application_key_id: str, application_key: str, bucket_name: str):
        """
        初始化B2上传器
        
        Args:
            application_key_id: B2应用密钥ID
            application_key: B2应用密钥
            bucket_name: B2存储桶名称
        """
        self.application_key_id = application_key_id
        self.application_key = application_key
        self.bucket_name = bucket_name
        self.api = None
        self.bucket = None
        
    def _initialize_api(self):
        """初始化B2 API连接"""
        if self.api is None:
            try:
                info = InMemoryAccountInfo()
                self.api = B2Api(info)
                self.api.authorize_account("production", self.application_key_id, self.application_key)
                self.bucket = self.api.get_bucket_by_name(self.bucket_name)
                logger.info(f"成功连接到B2存储桶: {self.bucket_name}")
            except Exception as e:
                logger.error(f"初始化B2 API失败: {str(e)}")
                raise
    
    def upload_file(self, file_path: str, remote_filename: str) -> bool:
        """
        上传文件到B2存储桶
        
        Args:
            file_path: 本地文件路径
            remote_filename: 远程文件名
            
        Returns:
            bool: 上传是否成功
        """
        try:
            self._initialize_api()
            
            if not os.path.exists(file_path):
                logger.error(f"文件不存在: {file_path}")
                return False
            
            file_size = os.path.getsize(file_path)
            logger.info(f"开始上传文件: {file_path} -> {remote_filename} ({file_size} bytes)")
            
            with open(file_path, 'rb') as file_data:
                file_info = self.bucket.upload(
                    file_data,
                    remote_filename,
                    content_type='application/gzip'
                )
            
            logger.info(f"文件上传成功: {remote_filename} (ID: {file_info.id_})")
            return True
            
        except Exception as e:
            logger.error(f"上传文件失败: {str(e)}")
            return False
    
    def list_backup_files(self, prefix: str = "backup_") -> List[FileVersion]:
        """
        列出存储桶中的备份文件
        
        Args:
            prefix: 文件名前缀
            
        Returns:
            List[FileVersion]: 文件版本列表
        """
        try:
            self._initialize_api()
            
            files = []
            for file_version, _ in self.bucket.ls(folder_to_list="", recursive=True):
                if file_version.file_name.startswith(prefix):
                    files.append(file_version)
            
            logger.info(f"找到 {len(files)} 个备份文件")
            return files
            
        except Exception as e:
            logger.error(f"列出文件失败: {str(e)}")
            return []
    
    def delete_old_backups(self, retention_days: int = 7) -> int:
        """
        删除超过保留期的备份文件
        
        Args:
            retention_days: 保留天数
            
        Returns:
            int: 删除的文件数量
        """
        try:
            self._initialize_api()
            
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            cutoff_timestamp = int(cutoff_date.timestamp() * 1000)  # B2使用毫秒时间戳
            
            backup_files = self.list_backup_files()
            deleted_count = 0
            
            for file_version in backup_files:
                if file_version.upload_timestamp < cutoff_timestamp:
                    try:
                        self.api.delete_file_version(file_version.id_, file_version.file_name)
                        logger.info(f"删除过期备份: {file_version.file_name}")
                        deleted_count += 1
                    except Exception as e:
                        logger.error(f"删除文件失败 {file_version.file_name}: {str(e)}")
            
            logger.info(f"清理完成，删除了 {deleted_count} 个过期备份文件")
            return deleted_count
            
        except Exception as e:
            logger.error(f"清理过期备份失败: {str(e)}")
            return 0
    
    def test_connection(self) -> bool:
        """
        测试B2连接
        
        Returns:
            bool: 连接是否成功
        """
        try:
            self._initialize_api()
            
            # 尝试列出存储桶内容来测试连接
            list(self.bucket.ls(folder_to_list="", recursive=False, fetch_count=1))
            logger.info("B2连接测试成功")
            return True
            
        except Exception as e:
            logger.error(f"B2连接测试失败: {str(e)}")
            return False
    
    def get_bucket_info(self) -> Optional[dict]:
        """
        获取存储桶信息
        
        Returns:
            dict: 存储桶信息
        """
        try:
            self._initialize_api()
            
            bucket_info = {
                'name': self.bucket.name,
                'id': self.bucket.id_,
                'type': self.bucket.type_,
                'revision': self.bucket.revision
            }
            
            return bucket_info
            
        except Exception as e:
            logger.error(f"获取存储桶信息失败: {str(e)}")
            return None
