FROM  ghcr.io/galilei2050/baski:latest

# Allow statements and log messages to immediately appear in the Knative logs
ENV PYTHONUNBUFFERED True
ENV APP_HOME /app

WORKDIR $APP_HOME

COPY ./app ./
COPY requirements.txt ./

# Install production dependencies.
RUN pip install --upgrade pip && pip install --use-pep517 --check-build-dependencies --no-cache-dir --compile -U \
    -r requirements.txt && rm requirements.txt


CMD exec python3 -m main