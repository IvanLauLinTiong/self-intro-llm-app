FROM python:3.9.11-slim-buster

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . /app

EXPOSE 7860

CMD ["chainlit", "run", "app.py", "--port", "7860"]