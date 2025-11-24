#!/bin/bash
# 一键执行数据采集脚本

# 创建输出目录（若不存在）
mkdir -p output

# 提示输入SSH密码（避免硬编码）
read -p "请输入远程主机SSH密码：" ssh_pwd

# 执行Ansible剧本（核心命令）
ansible-playbook -i ./hosts.ini  collect_data.yml \
  --extra-vars "ansible_ssh_pass=$ssh_pwd"  # 传入SSH密码变量

echo "采集完成，结果已保存到 output/ 目录"
