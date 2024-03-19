FROM python:3.10

WORKDIR /
RUN pip install --upgrade pip

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .

ARG REDIS_IP
ARG REDIS_PORT
ARG MULTI_ITERATIONS=10
ARG MULTI_NUM=10
ARG MULTI_SIMPLE=False
ARG DYNAMIC_ITER=10
ARG DYNAMIC_NUM=10
ARG DYNAMIC_SIMPLE=False

ENV EXECUTION_HOST 0.0.0.0

RUN printf "[MULTI]\nnum = ${MULTI_NUM}\niter = ${MULTI_ITERATIONS}\nsimple = ${MULTI_SIMPLE}\n\n[DYNAMIC]\nnum = ${DYNAMIC_NUM}\niter = ${DYNAMIC_ITER}\nsimple = ${DYNAMIC_SIMPLE}\nredis_ip = ${REDIS_IP}\nredis_port = ${REDIS_PORT}\n" > config.ini

CMD ["python", "app.py"]
EXPOSE ${port}
