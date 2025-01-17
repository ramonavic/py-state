FROM python:3.13

WORKDIR /opt/py-state

# Install Poetry
RUN set eux; \
    curl -sSL https://install.python-poetry.org | POETRY_HOME=/opt/poetry python; \
    cd /usr/local/bin; \
    ln -s /opt/poetry/bin/poetry; \
    poetry config virtualenvs.create false; \
    poetry self add poetry-plugin-sort

COPY ./pyproject.toml ./poetry.lock /opt/py-state/

RUN poetry install --no-root

COPY . /opt/py-state
ENV PYTHONPATH=/opt/py-state
