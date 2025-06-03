"""
健康检查HTTP服务
提供系统状态监控端点
"""
import json
import logging
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class HealthCheckHandler(BaseHTTPRequestHandler):
    """健康检查HTTP请求处理器"""
    
    def __init__(self, *args, health_checker=None, **kwargs):
        self.health_checker = health_checker
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """处理GET请求"""
        try:
            parsed_path = urlparse(self.path)
            path = parsed_path.path
            
            if path == '/health':
                self._handle_health_check()
            elif path == '/status':
                self._handle_status_check()
            elif path == '/metrics':
                self._handle_metrics()
            elif path == '/backup/run':
                self._handle_manual_backup()
            elif path == '/cleanup/run':
                self._handle_manual_cleanup()
            else:
                self._send_response(404, {'error': 'Not Found'})
                
        except Exception as e:
            logger.error(f"处理请求失败: {str(e)}")
            self._send_response(500, {'error': 'Internal Server Error'})
    
    def do_POST(self):
        """处理POST请求"""
        try:
            parsed_path = urlparse(self.path)
            path = parsed_path.path
            
            if path == '/backup/run':
                self._handle_manual_backup()
            elif path == '/cleanup/run':
                self._handle_manual_cleanup()
            else:
                self._send_response(404, {'error': 'Not Found'})
                
        except Exception as e:
            logger.error(f"处理POST请求失败: {str(e)}")
            self._send_response(500, {'error': 'Internal Server Error'})
    
    def _handle_health_check(self):
        """处理健康检查请求"""
        if self.health_checker:
            health_status = self.health_checker.get_health_status()
            status_code = 200 if health_status['status'] == 'healthy' else 503
            self._send_response(status_code, health_status)
        else:
            self._send_response(200, {'status': 'healthy', 'timestamp': datetime.now().isoformat()})
    
    def _handle_status_check(self):
        """处理状态检查请求"""
        if self.health_checker:
            status = self.health_checker.get_detailed_status()
            self._send_response(200, status)
        else:
            self._send_response(200, {'status': 'unknown', 'timestamp': datetime.now().isoformat()})
    
    def _handle_metrics(self):
        """处理指标请求"""
        if self.health_checker:
            metrics = self.health_checker.get_metrics()
            self._send_response(200, metrics)
        else:
            self._send_response(200, {'metrics': {}, 'timestamp': datetime.now().isoformat()})
    
    def _handle_manual_backup(self):
        """处理手动备份请求"""
        if self.health_checker and hasattr(self.health_checker, 'trigger_backup'):
            try:
                result = self.health_checker.trigger_backup()
                self._send_response(200, {'message': 'Backup triggered', 'result': result})
            except Exception as e:
                self._send_response(500, {'error': f'Backup failed: {str(e)}'})
        else:
            self._send_response(503, {'error': 'Backup service not available'})
    
    def _handle_manual_cleanup(self):
        """处理手动清理请求"""
        if self.health_checker and hasattr(self.health_checker, 'trigger_cleanup'):
            try:
                result = self.health_checker.trigger_cleanup()
                self._send_response(200, {'message': 'Cleanup triggered', 'result': result})
            except Exception as e:
                self._send_response(500, {'error': f'Cleanup failed: {str(e)}'})
        else:
            self._send_response(503, {'error': 'Cleanup service not available'})
    
    def _send_response(self, status_code: int, data: Dict[str, Any]):
        """发送JSON响应"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response_data = json.dumps(data, ensure_ascii=False, indent=2)
        self.wfile.write(response_data.encode('utf-8'))
    
    def log_message(self, format, *args):
        """重写日志方法以使用标准日志"""
        logger.info(f"{self.address_string()} - {format % args}")


class HealthChecker:
    """健康检查器"""
    
    def __init__(self, backup_service=None):
        """
        初始化健康检查器
        
        Args:
            backup_service: 备份服务实例
        """
        self.backup_service = backup_service
        self.start_time = datetime.now()
        self.last_backup_time = None
        self.last_cleanup_time = None
        self.backup_count = 0
        self.cleanup_count = 0
        self.error_count = 0
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        获取基本健康状态
        
        Returns:
            dict: 健康状态信息
        """
        try:
            status = 'healthy'
            checks = {}
            
            # 检查备份服务
            if self.backup_service:
                try:
                    service_status = self.backup_service.get_status()
                    checks['backup_service'] = service_status
                    if not service_status.get('healthy', False):
                        status = 'unhealthy'
                except Exception as e:
                    checks['backup_service'] = {'healthy': False, 'error': str(e)}
                    status = 'unhealthy'
            
            return {
                'status': status,
                'timestamp': datetime.now().isoformat(),
                'uptime_seconds': (datetime.now() - self.start_time).total_seconds(),
                'checks': checks
            }
            
        except Exception as e:
            logger.error(f"获取健康状态失败: {str(e)}")
            return {
                'status': 'unhealthy',
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }
    
    def get_detailed_status(self) -> Dict[str, Any]:
        """
        获取详细状态信息
        
        Returns:
            dict: 详细状态信息
        """
        try:
            basic_status = self.get_health_status()
            
            # 添加详细信息
            detailed_status = {
                **basic_status,
                'service_info': {
                    'start_time': self.start_time.isoformat(),
                    'last_backup_time': self.last_backup_time.isoformat() if self.last_backup_time else None,
                    'last_cleanup_time': self.last_cleanup_time.isoformat() if self.last_cleanup_time else None,
                    'backup_count': self.backup_count,
                    'cleanup_count': self.cleanup_count,
                    'error_count': self.error_count
                }
            }
            
            # 添加调度器信息
            if self.backup_service and hasattr(self.backup_service, 'scheduler'):
                try:
                    next_runs = self.backup_service.scheduler.get_next_run_times()
                    detailed_status['scheduler'] = next_runs
                except Exception as e:
                    detailed_status['scheduler'] = {'error': str(e)}
            
            return detailed_status
            
        except Exception as e:
            logger.error(f"获取详细状态失败: {str(e)}")
            return {
                'status': 'error',
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        获取系统指标
        
        Returns:
            dict: 系统指标
        """
        try:
            uptime = (datetime.now() - self.start_time).total_seconds()
            
            metrics = {
                'uptime_seconds': uptime,
                'backup_count': self.backup_count,
                'cleanup_count': self.cleanup_count,
                'error_count': self.error_count,
                'backup_rate': self.backup_count / (uptime / 3600) if uptime > 0 else 0,  # 每小时备份次数
                'timestamp': datetime.now().isoformat()
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"获取指标失败: {str(e)}")
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def record_backup(self, success: bool = True):
        """记录备份操作"""
        self.last_backup_time = datetime.now()
        if success:
            self.backup_count += 1
        else:
            self.error_count += 1
    
    def record_cleanup(self, success: bool = True):
        """记录清理操作"""
        self.last_cleanup_time = datetime.now()
        if success:
            self.cleanup_count += 1
        else:
            self.error_count += 1
    
    def trigger_backup(self):
        """触发手动备份"""
        if self.backup_service and hasattr(self.backup_service, 'run_backup'):
            return self.backup_service.run_backup()
        else:
            raise Exception("备份服务不可用")
    
    def trigger_cleanup(self):
        """触发手动清理"""
        if self.backup_service and hasattr(self.backup_service, 'run_cleanup'):
            return self.backup_service.run_cleanup()
        else:
            raise Exception("清理服务不可用")


class HealthCheckServer:
    """健康检查HTTP服务器"""
    
    def __init__(self, port: int = 8080, health_checker: Optional[HealthChecker] = None):
        """
        初始化健康检查服务器
        
        Args:
            port: 服务端口
            health_checker: 健康检查器实例
        """
        self.port = port
        self.health_checker = health_checker
        self.server = None
        self.server_thread = None
    
    def start(self):
        """启动健康检查服务器"""
        try:
            def handler(*args, **kwargs):
                return HealthCheckHandler(*args, health_checker=self.health_checker, **kwargs)
            
            self.server = HTTPServer(('0.0.0.0', self.port), handler)
            self.server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.server_thread.start()
            
            logger.info(f"健康检查服务器已启动，端口: {self.port}")
            
        except Exception as e:
            logger.error(f"启动健康检查服务器失败: {str(e)}")
            raise
    
    def stop(self):
        """停止健康检查服务器"""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            
        if self.server_thread and self.server_thread.is_alive():
            self.server_thread.join(timeout=5)
        
        logger.info("健康检查服务器已停止")
