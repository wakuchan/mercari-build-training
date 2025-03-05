FROM python:3.10-alpine

RUN addgroup -S mercari && adduser -S trainee -G mercari

WORKDIR /app
COPY . /app/
RUN mv db /db
RUN chown -R trainee:mercari /db

USER trainee

RUN pip install -r python/requirements.txt

CMD /home/trainee/.local/bin/uvicorn main:app --reload --port 9000
