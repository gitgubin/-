FROM python:3.11-slim

# 安装系统依赖（包括SQLite3）
RUN apt-get update && apt-get install -y \
    sqlite3 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 复制requirements.txt并安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 设置环境变量 - 使用/data目录持久化存储
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV SQLALCHEMY_DATABASE_URI=sqlite:////data/database.db

# 暴露端口
EXPOSE 5000

# 创建启动脚本（修复版）
RUN echo '#!/bin/bash\n\
echo "=== 初始化数据库 === "\n\
# 确保数据目录存在\n\
mkdir -p /data\n\
# 检查数据库文件是否存在且不为空\n\
if [ ! -f /data/database.db ] || [ ! -s /data/database.db ]; then\n\
    echo "创建或重新初始化数据库文件..."\n\
    rm -f /data/database.db\n\
    sqlite3 /data/database.db ".databases"\n\
    echo "初始化数据库表结构..."\n\
    python << EOF\n\
from app import db, app\n\
with app.app_context():\n\
    db.create_all()\n\
    print("数据库表结构创建完成")\n\
EOF\n\
else\n\
    echo "使用现有数据库文件"\n\
fi\n\
# 验证表结构\n\
echo "验证数据库表结构..."\n\
python << EOF\n\
from app import db, app\n\
with app.app_context():\n\
    from sqlalchemy import inspect\n\
    inspector = inspect(db.engine)\n\
    tables = inspector.get_table_names()\n\
    print(f"数据库中的表: {tables}")\n\
    if "host" in tables:\n\
        from models import Host\n\
        count = Host.query.count()\n\
        print(f"主机表记录数: {count}")\n\
    else:\n\
        print("警告: host表不存在")\n\
EOF\n\
echo "=== 启动监控应用 === "\n\
python app.py' > /app/start.sh && chmod +x /app/start.sh

CMD ["/app/start.sh"]