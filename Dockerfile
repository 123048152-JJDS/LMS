FROM python:3.13-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .

RUN python -m pip install --upgrade pip
RUN python -m pip install -r requirements.txt

COPY . .

RUN mkdir -p uploads/materiales

EXPOSE 5001

CMD ["flask", "--app", "app", "run", "--host=0.0.0.0", "--port=5001", "--debug"]