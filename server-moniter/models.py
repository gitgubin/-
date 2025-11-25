from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Host(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(15), nullable=False, unique=True)
    ssh_username = db.Column(db.String(50), nullable=False)
    ssh_password = db.Column(db.String(100), nullable=False)
    ssh_port = db.Column(db.Integer, default=22)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'ip_address': self.ip_address,
            'ssh_username': self.ssh_username,
            'ssh_port': self.ssh_port,
            'created_at': self.created_at.isoformat()
        }

class MonitorData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    host_id = db.Column(db.Integer, db.ForeignKey('host.id'), nullable=False)
    cpu_usage = db.Column(db.Float)  # CPU使用率百分比
    memory_usage = db.Column(db.Float)  # 内存使用率百分比
    disk_usage = db.Column(db.Float)  # 磁盘使用率百分比
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    host = db.relationship('Host', backref=db.backref('monitor_data', lazy=True))