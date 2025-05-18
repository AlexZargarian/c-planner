# Dockerfile
FROM python:3.11-slim

# 1) set working dir
WORKDIR /app

# 2) copy & install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3) copy the rest of your app
COPY . .

# 4) default command
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
