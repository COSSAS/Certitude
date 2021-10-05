FROM python:slim

RUN apt-get update && apt-get install -y whois

COPY . /app

WORKDIR /app

RUN pip install .

ENTRYPOINT ["python", "-m", "certitude"]
CMD [ "-h" ]
