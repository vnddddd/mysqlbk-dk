#!/usr/bin/env python3
"""
安全检查脚本
检查项目中是否存在敏感信息泄露
"""
import os
import re
import sys
from pathlib import Path

class SecurityChecker:
    """安全检查器"""
    
    def __init__(self):
        self.issues = []
        self.warnings = []
        
        # 敏感信息模式
        self.sensitive_patterns = [
            (r'password\s*=\s*["\'][^"\']{8,}["\']', '可能的硬编码密码'),
            (r'key\s*=\s*["\'][A-Za-z0-9+/]{20,}["\']', '可能的硬编码密钥'),
            (r'secret\s*=\s*["\'][A-Za-z0-9+/]{20,}["\']', '可能的硬编码密钥'),
            (r'token\s*=\s*["\'][A-Za-z0-9+/]{20,}["\']', '可能的硬编码令牌'),
            (r'mysql://[^:]+:[^@]{8,}@[^/]+/\w+', '可能的真实MySQL连接字符串'),
            # 移除过于宽泛的模式，减少误报
            # (r'[A-Za-z0-9]{20,}', '可能的密钥或令牌（需人工确认）'),
        ]
        
        # 排除的文件和目录
        self.exclude_patterns = [
            r'\.git/',
            r'__pycache__/',
            r'\.pyc$',
            r'node_modules/',
            r'\.env$',  # 实际的.env文件应该被排除
            r'scripts/security_check\.py$',  # 排除自己
        ]
        
        # 测试文件模式（这些文件中的测试数据是安全的）
        self.test_file_patterns = [
            r'test.*\.py$',
            r'.*test\.py$',
            r'test-data/',
            r'\.dev\.',
            r'docker-compose\.dev\.yml$',
        ]

        # 文档文件模式（这些文件中的示例是安全的）
        self.doc_file_patterns = [
            r'README\.md$',
            r'.*\.md$',
            r'examples/',
            r'docs/',
        ]
    
    def is_excluded(self, file_path):
        """检查文件是否应该被排除"""
        file_str = str(file_path)
        for pattern in self.exclude_patterns:
            if re.search(pattern, file_str):
                return True
        return False
    
    def is_test_file(self, file_path):
        """检查是否为测试文件"""
        file_str = str(file_path)
        for pattern in self.test_file_patterns:
            if re.search(pattern, file_str):
                return True
        return False

    def is_doc_file(self, file_path):
        """检查是否为文档文件"""
        file_str = str(file_path)
        for pattern in self.doc_file_patterns:
            if re.search(pattern, file_str):
                return True
        return False
    
    def check_file(self, file_path):
        """检查单个文件"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            is_test = self.is_test_file(file_path)
            is_doc = self.is_doc_file(file_path)

            for pattern, description in self.sensitive_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    matched_text = match.group()

                    # 检查是否为明显的示例或占位符
                    if self.is_placeholder(matched_text):
                        continue

                    issue = {
                        'file': str(file_path),
                        'line': line_num,
                        'pattern': description,
                        'text': matched_text[:50] + '...' if len(matched_text) > 50 else matched_text,
                        'is_test': is_test,
                        'is_doc': is_doc
                    }

                    if is_test or is_doc:
                        self.warnings.append(issue)
                    else:
                        self.issues.append(issue)
                        
        except Exception as e:
            print(f"警告: 无法读取文件 {file_path}: {e}")
    
    def is_placeholder(self, text):
        """检查是否为占位符或示例"""
        placeholder_indicators = [
            'your_',
            'example',
            'placeholder',
            'testuser',
            'testpass',
            'localhost',
            'user:pass',
            'username:password',
            'admin:password',
            'key_id_here',
            'application_key_here',
            'bucket_here',
            'never_do_this',
            'never_hardcode',
            'secretpass123',  # 明显的示例密码
            'prod-db.com',    # 示例域名
            'maindb',         # 示例数据库名
        ]

        text_lower = text.lower()
        for indicator in placeholder_indicators:
            if indicator in text_lower:
                return True
        return False
    
    def check_env_files(self):
        """检查环境变量文件"""
        env_files = ['.env', '.env.local', '.env.production']
        
        for env_file in env_files:
            if os.path.exists(env_file):
                self.issues.append({
                    'file': env_file,
                    'line': 0,
                    'pattern': '环境变量文件存在',
                    'text': '请确保此文件不包含在版本控制中',
                    'is_test': False
                })
    
    def check_git_status(self):
        """检查Git状态"""
        if os.path.exists('.git'):
            try:
                import subprocess
                result = subprocess.run(['git', 'status', '--porcelain'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    untracked = [line for line in result.stdout.split('\n') 
                               if line.startswith('??') and '.env' in line]
                    if untracked:
                        for line in untracked:
                            file_name = line[3:].strip()
                            self.warnings.append({
                                'file': file_name,
                                'line': 0,
                                'pattern': '未跟踪的环境文件',
                                'text': '请确保添加到.gitignore',
                                'is_test': False
                            })
            except:
                pass  # Git不可用或其他错误
    
    def scan_directory(self, directory='.'):
        """扫描目录"""
        print(f"扫描目录: {directory}")
        
        for root, dirs, files in os.walk(directory):
            # 排除特定目录
            dirs[:] = [d for d in dirs if not any(re.search(pattern, os.path.join(root, d)) 
                                                 for pattern in self.exclude_patterns)]
            
            for file in files:
                file_path = Path(root) / file
                
                if self.is_excluded(file_path):
                    continue
                
                # 只检查文本文件
                if file_path.suffix in ['.py', '.yml', '.yaml', '.json', '.txt', '.md', '.env', '.sh']:
                    self.check_file(file_path)
        
        # 检查环境文件
        self.check_env_files()
        
        # 检查Git状态
        self.check_git_status()
    
    def print_results(self):
        """打印检查结果"""
        print("\n" + "="*60)
        print("安全检查结果")
        print("="*60)
        
        if not self.issues and not self.warnings:
            print("✅ 未发现安全问题")
            return
        
        if self.issues:
            print(f"\n🚨 发现 {len(self.issues)} 个潜在安全问题:")
            for i, issue in enumerate(self.issues, 1):
                print(f"\n{i}. {issue['pattern']}")
                print(f"   文件: {issue['file']}:{issue['line']}")
                print(f"   内容: {issue['text']}")
        
        if self.warnings:
            print(f"\n⚠️  发现 {len(self.warnings)} 个警告（测试/文档文件）:")
            for i, warning in enumerate(self.warnings, 1):
                file_type = "文档" if warning.get('is_doc') else "测试"
                print(f"\n{i}. {warning['pattern']} ({file_type}文件)")
                print(f"   文件: {warning['file']}:{warning['line']}")
                print(f"   内容: {warning['text']}")
        
        print("\n" + "="*60)
        print("安全建议:")
        print("1. 确保所有敏感信息都通过环境变量传递")
        print("2. 将.env文件添加到.gitignore")
        print("3. 定期轮换密钥和令牌")
        print("4. 使用最小权限原则")
        print("5. 在生产环境中禁用调试模式")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="安全检查脚本")
    parser.add_argument("--directory", "-d", default=".", help="要扫描的目录")
    parser.add_argument("--strict", action="store_true", help="严格模式，将警告也视为错误")
    
    args = parser.parse_args()
    
    checker = SecurityChecker()
    checker.scan_directory(args.directory)
    checker.print_results()
    
    # 返回适当的退出码
    if checker.issues or (args.strict and checker.warnings):
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
