"""
数据库连接字符串解析器
支持多种MySQL连接字符串格式
"""
import re
from urllib.parse import urlparse, parse_qs
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class DatabaseConnectionParser:
    """解析各种格式的MySQL连接字符串"""

    @staticmethod
    def parse_connections(connection_string: str) -> List[Dict[str, Any]]:
        """
        解析连接字符串，返回数据库连接配置列表

        支持的格式：
        1. 单个连接: username:password@tcp(host:port)/database
        2. 单个连接: mysql://username:password@host:port/database?ssl-mode=REQUIRED
        3. 单个连接: mysql://username:password@host:port/database
        4. 同服务器多数据库: mysql://username:password@host:port/db1,db2,db3
        5. 多个不同服务器: 用分号分隔多个完整连接字符串
           例如: mysql://user1:pass1@host1:3306/db1;mysql://user2:pass2@host2:3306/db2
        6. JSON格式配置: 支持更复杂的配置，包括连接组名称和独立设置
        """
        connections = []

        # 去除空白字符
        connection_string = connection_string.strip()

        if not connection_string:
            raise ValueError("连接字符串不能为空")

        # 检查是否为JSON格式
        if connection_string.startswith('{') or connection_string.startswith('['):
            return DatabaseConnectionParser._parse_json_config(connection_string)

        # 检查是否包含分号（多个不同服务器）
        if ';' in connection_string:
            return DatabaseConnectionParser._parse_multiple_connections(connection_string)

        # 单个连接字符串解析
        return DatabaseConnectionParser._parse_single_connection(connection_string)

    @staticmethod
    def _parse_single_connection(connection_string: str) -> List[Dict[str, Any]]:
        """解析单个连接字符串"""
        # 格式1: username:password@tcp(host:port)/database
        tcp_pattern = r'^([^:]+):([^@]+)@tcp\(([^:]+):(\d+)\)/(.+)$'
        tcp_match = re.match(tcp_pattern, connection_string)

        if tcp_match:
            username, password, host, port, database = tcp_match.groups()
            connection = {
                'host': host,
                'port': int(port),
                'username': username,
                'password': password,
                'database': database,
                'ssl_mode': None,
                'group_name': f"{host}:{port}",
                'connection_id': f"{host}_{port}_{database}"
            }
            logger.info(f"解析TCP格式连接: {host}:{port}/{database}")
            return [connection]

        # 格式2-4: mysql://... 格式
        if connection_string.startswith('mysql://'):
            return DatabaseConnectionParser._parse_mysql_url(connection_string)

        raise ValueError(f"不支持的连接字符串格式: {connection_string}")

    @staticmethod
    def _parse_multiple_connections(connection_string: str) -> List[Dict[str, Any]]:
        """解析多个连接字符串（用分号分隔）"""
        connections = []
        connection_strings = [conn.strip() for conn in connection_string.split(';') if conn.strip()]

        for i, conn_str in enumerate(connection_strings):
            try:
                single_connections = DatabaseConnectionParser._parse_single_connection(conn_str)
                for conn in single_connections:
                    # 为多连接添加序号
                    conn['group_index'] = i
                    if 'group_name' not in conn:
                        conn['group_name'] = f"Group_{i+1}"
                connections.extend(single_connections)
            except Exception as e:
                logger.error(f"解析连接字符串失败 (第{i+1}个): {conn_str}, 错误: {str(e)}")
                raise ValueError(f"解析第{i+1}个连接字符串失败: {str(e)}")

        logger.info(f"解析多连接配置: 共{len(connections)}个数据库连接，来自{len(connection_strings)}个服务器")
        return connections
    
    @staticmethod
    def _parse_mysql_url(url: str) -> List[Dict[str, Any]]:
        """解析mysql://格式的URL"""
        try:
            parsed = urlparse(url)

            if not all([parsed.hostname, parsed.username, parsed.password]):
                raise ValueError("MySQL URL缺少必要的连接信息")

            # 解析SSL模式
            ssl_mode = None
            if parsed.query:
                query_params = parse_qs(parsed.query)
                ssl_mode = query_params.get('ssl-mode', [None])[0]

            # 解析数据库名称（可能是多个，用逗号分隔）
            path = parsed.path.lstrip('/')
            if not path:
                raise ValueError("MySQL URL中缺少数据库名称")

            databases = [db.strip() for db in path.split(',') if db.strip()]

            connections = []
            group_name = f"{parsed.hostname}:{parsed.port or 3306}"

            for database in databases:
                connection = {
                    'host': parsed.hostname,
                    'port': parsed.port or 3306,
                    'username': parsed.username,
                    'password': parsed.password,
                    'database': database,
                    'ssl_mode': ssl_mode,
                    'group_name': group_name,
                    'connection_id': f"{parsed.hostname}_{parsed.port or 3306}_{database}"
                }
                connections.append(connection)
                logger.info(f"解析MySQL URL连接: {parsed.hostname}:{connection['port']}/{database}")

            return connections

        except Exception as e:
            raise ValueError(f"解析MySQL URL失败: {str(e)}")

    @staticmethod
    def _parse_json_config(json_string: str) -> List[Dict[str, Any]]:
        """解析JSON格式的配置"""
        import json

        try:
            config = json.loads(json_string)
            connections = []

            # 支持两种JSON格式：
            # 1. 数组格式: [{"name": "group1", "connection": "mysql://...", "schedule": "..."}, ...]
            # 2. 对象格式: {"connections": [...], "global_settings": {...}}

            if isinstance(config, list):
                # 数组格式
                for i, item in enumerate(config):
                    group_connections = DatabaseConnectionParser._parse_json_group(item, i)
                    connections.extend(group_connections)
            elif isinstance(config, dict):
                if 'connections' in config:
                    # 对象格式
                    for i, item in enumerate(config['connections']):
                        group_connections = DatabaseConnectionParser._parse_json_group(item, i)
                        connections.extend(group_connections)
                else:
                    # 单个连接对象
                    group_connections = DatabaseConnectionParser._parse_json_group(config, 0)
                    connections.extend(group_connections)
            else:
                raise ValueError("JSON配置格式错误")

            logger.info(f"解析JSON配置: 共{len(connections)}个数据库连接")
            return connections

        except json.JSONDecodeError as e:
            raise ValueError(f"JSON格式错误: {str(e)}")
        except Exception as e:
            raise ValueError(f"解析JSON配置失败: {str(e)}")

    @staticmethod
    def _parse_json_group(group_config: Dict[str, Any], group_index: int) -> List[Dict[str, Any]]:
        """解析JSON配置中的单个连接组"""
        if 'connection' not in group_config:
            raise ValueError(f"连接组{group_index + 1}缺少connection字段")

        # 解析连接字符串
        connection_string = group_config['connection']
        base_connections = DatabaseConnectionParser._parse_single_connection(connection_string)

        # 添加组信息
        group_name = group_config.get('name', f"Group_{group_index + 1}")

        for conn in base_connections:
            conn['group_name'] = group_name
            conn['group_index'] = group_index

            # 添加可选的组级配置
            if 'schedule' in group_config:
                conn['custom_schedule'] = group_config['schedule']
            if 'retention_days' in group_config:
                conn['custom_retention_days'] = group_config['retention_days']
            if 'enabled' in group_config:
                conn['enabled'] = group_config['enabled']
            else:
                conn['enabled'] = True

            # 添加其他自定义配置
            for key, value in group_config.items():
                if key not in ['connection', 'name', 'schedule', 'retention_days', 'enabled']:
                    conn[f'custom_{key}'] = value

        return base_connections
    
    @staticmethod
    def validate_connection(connection: Dict[str, Any]) -> bool:
        """验证连接配置的完整性"""
        required_fields = ['host', 'port', 'username', 'password', 'database']
        
        for field in required_fields:
            if field not in connection or not connection[field]:
                logger.error(f"连接配置缺少必要字段: {field}")
                return False
        
        # 验证端口号
        try:
            port = int(connection['port'])
            if not (1 <= port <= 65535):
                logger.error(f"无效的端口号: {port}")
                return False
        except (ValueError, TypeError):
            logger.error(f"端口号必须是数字: {connection['port']}")
            return False
        
        return True
    
    @staticmethod
    def get_connection_info(connection: Dict[str, Any]) -> str:
        """获取连接信息的安全字符串表示（隐藏密码）"""
        group_info = f"[{connection.get('group_name', 'Unknown')}] " if connection.get('group_name') else ""
        return f"{group_info}{connection['username']}@{connection['host']}:{connection['port']}/{connection['database']}"

    @staticmethod
    def get_connection_groups(connections: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """按组名分组连接"""
        groups = {}
        for conn in connections:
            group_name = conn.get('group_name', 'Default')
            if group_name not in groups:
                groups[group_name] = []
            groups[group_name].append(conn)
        return groups

    @staticmethod
    def filter_enabled_connections(connections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """过滤启用的连接"""
        return [conn for conn in connections if conn.get('enabled', True)]
