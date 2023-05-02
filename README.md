# CopyPasta

Simple python application written by WJDigby and stylized by me

# Why?

Copying and pasting when you use VMs is awful, go deploy this in a container and away you go.


## Usage

```
docker run -d \
    --name copypasta \
    -p 8005:8080 \
    -e TZ="America/New_York" \
    -v "/copypasta/clipboard:/srv/clipboard" \
    -v "/copypasta/static/:/srv/static/" \
    --restart=unless-stopped \
    copypasta:latest
```

## Generating an SSL Cetificate

Every now and then you need a new one :)

```bash
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -sha256 -days 365 -nodes
```