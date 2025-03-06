FROM python:3.10-alpine

RUN addgroup -S mercari && adduser -S trainee -G mercari

WORKDIR /app
COPY . /app/

RUN chown -R trainee:mercari /app

USER trainee

RUN pip install --user -r requirements.txt

ENV PATH="/home/trainee/.local/bin:${PATH}"


CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "9000"]