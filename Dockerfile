FROM python:3.10

WORKDIR /usr/app

RUN pip install --upgrade pip
RUN pip install poetry

COPY pyproject.toml /usr/app/
COPY poetry.lock /usr/app/

RUN poetry config virtualenvs.create false
RUN poetry install --no-interaction --no-ansi --no-dev

COPY . /usr/app/