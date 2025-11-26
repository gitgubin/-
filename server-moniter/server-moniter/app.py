import os
from flask import Flask, render_template, request, jsonify, session, redirect, send_from_directory
from models import db, Host, MonitorData
from monitor import SSHAgent
import threading
import time
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////data/database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

def init_database():
    """初始化数据库"""
    with app.app_context():
        try:
            # 检查数据库文件是否存在
            db_path = '/data/database.db'
            if not os.path.exists(db_path) or os.path.getsize(db_path) == 0:
                print("数据库文件不存在或为空，重新创建...")
                db.create_all()
                print("数据库表结构创建完成")
            else:
                # 验证表结构
                from sqlalchemy import inspect
                inspector = inspect(db.engine)
                tables = inspector.get_table_names()
                print(f"数据库中的表: {tables}")
                
                if 'host' not in tables:
                    print("host表不存在，重新创建表结构...")
                    db.create_all()
        except Exception as e:
            print(f"数据库初始化错误: {e}")
            # 强制重新创建
            db.create_all()
            print("数据库强制重建完成")

# 在应用启动时初始化数据库
init_database()
# 全局变量存储监控数据
monitor_data_cache = {}

def collect_monitor_data():
    """后台监控数据采集线程 - 修复版"""
    while True:
        try:
            # 手动创建应用上下文
            with app.app_context():  
                hosts = Host.query.all()
                current_data = {}
                
                for host in hosts:
                    try:
                        # 建立SSH连接获取监控数据
                        ssh_agent = SSHAgent(
                            host.ip_address, 
                            host.ssh_username, 
                            host.ssh_password, 
                            host.ssh_port
                        )
                        
                        success, message = ssh_agent.connect()
                        if success:
                            system_info = ssh_agent.get_system_info()
                            ssh_agent.close()
                            
                            # 保存到数据库
                            monitor_record = MonitorData(
                                host_id=host.id,
                                cpu_usage=system_info['cpu_usage'],
                                memory_usage=system_info['memory_usage'],
                                disk_usage=system_info['disk_usage']
                            )
                            db.session.add(monitor_record)
                            db.session.commit()  # ✅ 在上下文中提交
                            
                            # 更新缓存
                            current_data[host.id] = system_info
                        else:
                            current_data[host.id] = {'error': message}
                            
                    except Exception as e:
                        print(f"处理主机 {host.ip_address} 时出错: {e}")
                        current_data[host.id] = {'error': str(e)}
                
                # 更新全局缓存
                monitor_data_cache.update(current_data)
                
        except Exception as e:
            print(f"监控数据采集错误: {e}")
        
        # 每30秒采集一次
        time.sleep(30)

# 路由定义
@app.route('/')
def index():
    """首页 - 监控大屏"""
    return render_template('index.html')

@app.route('/index.html')
def index_html():
    """兼容index.html访问"""
    return render_template('index.html')

@app.route('/host-management.html')
@app.route('/host_management.html') 
def host_management():
    """主机管理页面"""
    return render_template('host_management.html')

# 静态文件路由
@app.route('/css/<path:filename>')
def serve_css(filename):
    return send_from_directory('static/css', filename)

@app.route('/js/<path:filename>')
def serve_js(filename):
    return send_from_directory('static/js', filename)

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

# 如果文件不存在，返回空内容避免404
@app.route('/<path:invalid_path>')
def handle_invalid_path(invalid_path):
    """处理无效路径，避免404错误"""
    if invalid_path.endswith(('.css', '.js')):
        # 对于不存在的CSS/JS文件，返回空内容
        return '', 200
    # 对于其他不存在的页面，重定向到首页
    return redirect('/')

@app.route('/api/monitor/data')
def get_monitor_data():
    """获取监控数据API"""
    try:
        hosts = Host.query.all()
        result = []
        
        for host in hosts:
            host_data = host.to_dict()
            # 添加监控数据
            monitor_info = monitor_data_cache.get(host.id, {})
            host_data['monitor'] = monitor_info
            
            # 添加状态信息
            if 'error' in monitor_info:
                host_data['status'] = 'offline'
                host_data['status_text'] = '离线'
            else:
                host_data['status'] = 'online' 
                host_data['status_text'] = '在线'
            
            result.append(host_data)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/debug/request', methods=['GET', 'POST', 'DELETE'])
def debug_request():
    """调试路由，查看请求信息"""
    return jsonify({
        'method': request.method,
        'args': dict(request.args),
        'json': request.get_json(silent=True) or {},
        'headers': dict(request.headers)
    })
    
@app.route('/api/hosts', methods=['GET', 'POST', 'DELETE'])  # 添加DELETE方法
def manage_hosts():
    """统一处理主机的GET、POST、DELETE请求"""
    if request.method == 'GET':
        # 获取所有主机
        try:
            hosts = Host.query.all()
            return jsonify([host.to_dict() for host in hosts])
        except Exception as e:
            return jsonify({'success': False, 'message': f'获取主机列表失败: {str(e)}'}), 500
    
    elif request.method == 'POST':
        # 添加新主机
        try:
            data = request.get_json()
            
            # 验证必填字段
            required_fields = ['ip_address', 'ssh_username', 'ssh_password']
            for field in required_fields:
                if not data.get(field):
                    return jsonify({'success': False, 'message': f'缺少必填字段: {field}'}), 400
            
            # 检查主机是否已存在
            existing_host = Host.query.filter_by(ip_address=data['ip_address']).first()
            if existing_host:
                return jsonify({'success': False, 'message': '该主机已存在'}), 400
            
            # 测试SSH连接
            ssh_agent = SSHAgent(
                data['ip_address'],
                data['ssh_username'], 
                data['ssh_password'],
                data.get('ssh_port', 22)
            )
            
            success, message = ssh_agent.connect()
            ssh_agent.close()
            
            if not success:
                return jsonify({'success': False, 'message': f'SSH连接测试失败: {message}'}), 400
            
            # 创建新主机
            new_host = Host(
                ip_address=data['ip_address'],
                ssh_username=data['ssh_username'],
                ssh_password=data['ssh_password'],
                ssh_port=data.get('ssh_port', 22)
            )
            
            db.session.add(new_host)
            db.session.commit()
            
            return jsonify({
                'success': True, 
                'message': '主机添加成功', 
                'host': new_host.to_dict()
            })
            
        except Exception as e:
            return jsonify({'success': False, 'message': f'添加主机失败: {str(e)}'}), 500
    
    elif request.method == 'DELETE':
        # 删除主机
        try:
            host_id = request.args.get('id')
            if not host_id:
                return jsonify({'success': False, 'message': '缺少主机ID参数'}), 400
            
            host = Host.query.get(host_id)
            if not host:
                return jsonify({'success': False, 'message': '主机不存在'}), 404
            
            # 删除关联的监控数据
            MonitorData.query.filter_by(host_id=host_id).delete()
            db.session.delete(host)
            db.session.commit()
            
            return jsonify({'success': True, 'message': '主机删除成功'})
            
        except Exception as e:
            return jsonify({'success': False, 'message': f'删除主机失败: {str(e)}'}), 500
    
    else:
        return jsonify({'success': False, 'message': '不支持的请求方法'}), 405

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # 启动监控数据采集线程
        monitor_thread = threading.Thread(target=collect_monitor_data, daemon=True)
        monitor_thread.start()
    
    app.run(debug=True, host='0.0.0.0', port=5000)