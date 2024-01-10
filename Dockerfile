ARG PYTHON_VERSION=3.11.7
FROM python:${PYTHON_VERSION} as builder

WORKDIR /app 

COPY . .

RUN pip install --no-cache-dir poetry==1.7.1 && poetry install && poetry build

# 3.18 due to pip being externally managed on 3.19
FROM alpine:3.18

RUN apk add --no-cache py3-pip

WORKDIR /ss13tools

COPY --from=builder /app/dist/*.whl ./

RUN pip3 install --no-cache-dir *.whl

# Don't use ENTRYPOINT here, so that a different command can be run if desired.
CMD ["ss13tools"]