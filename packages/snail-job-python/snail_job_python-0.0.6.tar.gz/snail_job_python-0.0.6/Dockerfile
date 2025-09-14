FROM python:3.9-alpine3.20

# 安装 snail-job-python 依赖
RUN pip install --no-cache-dir -v snail-job-python -i https://mirrors.aliyun.com/pypi/simple/

WORKDIR /app

# 把代码添加到工作目录
ADD example/main.py example/demo_job.py ./
COPY .env.example .env

CMD [ "python", "main.py" ]
