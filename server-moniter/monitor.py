import paramiko
import json
from datetime import datetime

class SSHAgent:
    def __init__(self, host_ip, username, password, port=22):
        self.host_ip = host_ip
        self.username = username
        self.password = password
        self.port = port
        self.client = None
    
    def connect(self):
        """建立SSH连接"""
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.client.connect(
                self.host_ip,
                port=self.port,
                username=self.username,
                password=self.password,
                timeout=10
            )
            return True, "连接成功"
        except Exception as e:
            return False, f"SSH连接失败: {str(e)}"
    
    def execute_command(self, command):
        """执行远程命令"""
        try:
            stdin, stdout, stderr = self.client.exec_command(command)
            output = stdout.read().decode('utf-8').strip()
            error = stderr.read().decode('utf-8').strip()
            return output, error
        except Exception as e:
            return "", f"命令执行失败: {str(e)}"
    
    def get_system_info(self):
        """获取系统监控数据"""
        # CPU使用率命令
        cpu_cmd = "top -bn1 | grep 'Cpu(s)' | sed 's/.*, *\\([0-9.]*\\)%* id.*/\\1/' | awk '{print 100 - $1}'"
        # 内存使用率命令
        mem_cmd = "free | grep Mem | awk '{print $3/$2 * 100.0}'"
        # 磁盘使用率命令
        disk_cmd = "df / | tail -1 | awk '{print $5}' | sed 's/%//'"
        
        cpu_output, cpu_error = self.execute_command(cpu_cmd)
        mem_output, mem_error = self.execute_command(mem_cmd)
        disk_output, disk_error = self.execute_command(disk_cmd)
        
        # 解析结果
        try:
            cpu_usage = float(cpu_output) if cpu_output else 0
            memory_usage = float(mem_output) if mem_output else 0
            disk_usage = float(disk_output) if disk_output else 0
        except ValueError:
            cpu_usage = memory_usage = disk_usage = 0
        
        return {
            'cpu_usage': round(cpu_usage, 2),
            'memory_usage': round(memory_usage, 2),
            'disk_usage': round(disk_usage, 2),
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def close(self):
        """关闭SSH连接"""
        if self.client:
            self.client.close()
