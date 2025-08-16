FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1
ENV PORT 8080

WORKDIR /code
COPY requirements.txt /code/
RUN pip install -r requirements.txt
COPY . /code/

CMD exec python manage.py runserver 0.0.0.0:$PORT
# CMD ["flask", "run", "--host=0.0.0.0", "--port=8080"]