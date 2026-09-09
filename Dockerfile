FROM ubuntu:latest
LABEL authors="mat"

ENTRYPOINT ["top", "-b"]