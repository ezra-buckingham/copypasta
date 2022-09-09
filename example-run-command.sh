docker run -d \
    --name copypasta \
    -p 8005:8080 \
    -e TZ="America/New_York" \
    -v "/copypasta/clipboard:/srv/clipboard" \
    -v "/copypasta/static/:/srv/static/" \
    --restart=unless-stopped \
    copypasta:latest

