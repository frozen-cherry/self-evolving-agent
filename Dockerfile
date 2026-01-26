FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . .

# 创建工具目录（确保存在）
RUN mkdir -p tools/_custom

# 设置环境变量
ENV PYTHONUNBUFFERED=1

# 启动命令
CMD ["python", "bot.py"]
