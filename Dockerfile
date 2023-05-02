FROM python:3.9-slim-bullseye

COPY . /opt/copypasta

WORKDIR /opt/copypasta
RUN pip install -r requirements.txt
RUN openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -sha256 -days 3650 -nodes -subj "/C=US/ST=Montana/L=Billings/O=CopyPasta/OU=CopyPastaPasta/CN=CopyPastaPastaPasta"

EXPOSE 443

CMD ["gunicorn", "-w", "4", "--keyfile", "key.pem", "--certfile", "cert.pem", "-b", "0.0.0.0:443", "'copypasta:app'"]
