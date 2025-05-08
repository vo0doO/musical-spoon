FROM python:3.13-alpine AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/

WORKDIR /tmp

COPY ./pyproject.toml ./uv.lock* /tmp/

RUN uv pip compile pyproject.toml -o requirements.txt


FROM python:3.13-alpine

WORKDIR /app

COPY --from=builder /tmp/requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY ./src /app

RUN pip install --no-cache-dir --upgrade ./

CMD ["uvicorn", "orders.entrypoints.fastapi.main:app", "--host", "0.0.0.0", "--port", "80"]

EXPOSE 80