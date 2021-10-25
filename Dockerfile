ARG PYVERSION=3.9-slim
FROM python:$PYVERSION

RUN apt-get update && apt-get install -y whois

COPY . /app

WORKDIR /app

RUN pip install .

ENTRYPOINT ["python", "-m", "certitude"]
CMD [ "-h" ]
