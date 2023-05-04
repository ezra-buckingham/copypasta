# CopyPasta

Simple python application written by WJDigby and whooly refactored to use only flask.

# Why?

Copying and pasting when you use VMs is awful, go deploy this in a container and away you go.


## Usage

```
docker run --name copypasta -d -p 443:443 -v "/opt/copypasta:/opt/copypasta/uploads" copypasta
```
