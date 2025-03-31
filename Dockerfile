FROM python:3.11-slim

WORKDIR /app

COPY . .

RUN pip install requests
RUN pip install python-dotenv
RUN pip install mcp

CMD ["python", "-u", "server.py"]