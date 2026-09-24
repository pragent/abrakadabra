# Dockerfile для локального тестування Git Call середовища
# Відтворює умови виконання Corezoid Git Call (Python 3.12, Alpine)

FROM python:3.12-alpine

WORKDIR /app
COPY usercode.py .
COPY requirements.txt .

# Обов'язкова вимога Corezoid — user/group 501:501, read-only container
RUN addgroup -g 501 usercode && \
    adduser -u 501 -G usercode -s /bin/sh -D usercode

USER usercode

CMD ["python", "usercode.py"]
