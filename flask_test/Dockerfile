FROM python:3.6-alpine

ADD . /code

WORKDIR /code

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

CMD ["python", "app.py"]
