FROM python:3.11.0a3-alpine3.15

ADD copypasta.py /srv/copypasta.py

EXPOSE 8080

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir web.py jinja2

WORKDIR "/srv/"

CMD ["python3", "/srv/copypasta.py"]
