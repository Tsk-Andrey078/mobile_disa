FROM python:3.10-slim

WORKDIR /app


RUN apt-get update && apt-get install -y\
    build-essential \
    libpq-dev \

    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY . /app
RUN python manage.py makemigrations && python manage.py collectstatic --noinput

EXPOSE 8000

#CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-w", "4", "-b", "0.0.0.0:8000", "mobile_prj.asgi:application", "--log-level=debug"]
CMD ["gunicorn", "-k", "gevent", "-w", "4", "-t", "900", "--bind", "0.0.0.0:8000", "mobile_prj.wsgi:application", "--log-level=debug"]
#CMD ["python", "-u", "manage.py", "runserver"]