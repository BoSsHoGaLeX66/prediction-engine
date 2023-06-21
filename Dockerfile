FROM python:3.11

WORKDIR /fastapi_test

COPY ./requirments.txt /fastapi_test/requirments.txt

RUN pip install --no-cache-dir --upgrade -r requirments.txt

COPY . /main.py /fastapi_test/

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
