ARG PYTHON_VERSION=3.12

FROM python:${PYTHON_VERSION}-alpine AS base

RUN apk update && apk upgrade --no-cache

FROM base AS builder

WORKDIR /code/

COPY src/ Pipfile Pipfile.lock /code/

RUN ls -la

RUN pip3 install --root-user-action ignore --no-cache-dir --disable-pip-version-check pipenv
RUN python3 -m pipenv requirements > requirements.txt


FROM base AS runtime

LABEL description="A Free Software Media System"
LABEL website="https://jarklin.github.io/"

RUN apk add --no-cache ffmpeg

WORKDIR /opt/jarklin/

COPY --from=builder /code/requirements.txt .
COPY --from=builder /code/jarklin/ .

RUN pip3 install --root-user-action ignore --no-cache-dir --disable-pip-version-check -r requirements.txt
RUN rm -- requirements.txt

COPY build-files/jarklin.run /opt/jarklin/
RUN chmod +x /opt/jarklin/jarklin.run

RUN pip install --root-user-action ignore --no-cache-dir --disable-pip-version-check better-exceptions
ENV BETTER_EXCEPTIONS 1

VOLUME ["/media/"]
WORKDIR /media/

EXPOSE 9898

ENTRYPOINT ["/opt/jarklin/jarklin.run"]
CMD ["run"]
