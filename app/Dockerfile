FROM python:3.11

WORKDIR /fastapi_test

COPY ./requirements.txt /fastapi_test/app/requirements.txt

RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY . /main.py /fastapi_test/app/

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
