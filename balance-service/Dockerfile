FROM python:3.9-slim

ENV PORT 80
ENV APPDIR /app

WORKDIR $APPDIR

COPY . $APPDIR

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

CMD exec gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 30 main:app