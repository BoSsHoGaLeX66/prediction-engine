FROM python:3.11

WORKDIR /fastapi_test

COPY ./requirments.txt /fastapi_test/requirments.txt

RUN pip install --no-cache-dir --upgrade -r requirments.txt

COPY . /main.py /fastapi_test/

EXPOSE 3100

CMD ["gunicorn", "main:app"]
