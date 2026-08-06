FROM python:3.12.11

# OS user
RUN groupadd -r lens && useradd -r -g lens lens -u 1000 \
    && usermod -d /usr/src/app lens

ENV GNUPGHOME /usr/src/app/.gnupg

# Install OS packages and security patches
RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends \
        gnupg \
        nano \
        mariadb-client \
        xmlsec1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create an app directory and set permissions.
RUN mkdir -p /usr/src/app/kbank_withdraw_files \
    && chown -R lens:lens /usr/src/app

WORKDIR /usr/src/app

ENV PIP_NO_CACHE_DIR false
RUN pip install --upgrade pip && \
    pip install pipenv

# ADD Pipfile.lock .
ADD Pipfile .

RUN pipenv lock
RUN pipenv install --system --deploy --ignore-pipfile

RUN pip install uWSGI==2.0.30
RUN pip install --upgrade pip "setuptools>=82.0.0" "msgpack>=1.2.1" wheel djangoql \
    "cryptography>=50.0.0" pyopenssl jaraco.context "pysaml2==7.5.0" \
     && pip install --no-deps grafana-django-saml2-auth==3.20.0

# Source code copy
COPY . .

RUN mkdir -p /usr/src/app/lens/static \
    && chown -R lens:lens /usr/src/app
RUN python manage.py collectstatic --noinput

EXPOSE 8000

ENV DJANGO_SETTINGS_MODULE=lens.settings.defaults

USER lens

ENTRYPOINT [ "/usr/local/bin/uwsgi", "--master", "--enable-threads", "--die-on-term", "--module", "lens.wsgi", "--chdir", "/usr/src/app", "--pythonpath", "/usr/src/app", "--http-socket", ":8000", "--log-4xx", "--log-5xx", "--disable-logging", "--static-map", "/static=/usr/src/app/lens/static" ]
CMD [ "--processes", "4" ]