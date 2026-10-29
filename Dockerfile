FROM python:3.14-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
COPY requirements.lock ./
RUN pip install --no-cache-dir -r requirements.lock
COPY pyproject.toml README.md ./
COPY LICENSE THIRD_PARTY_NOTICES.md ./
COPY third_party/aiogram/LICENSE ./third_party/aiogram/LICENSE
COPY smartphone_bot ./smartphone_bot
RUN pip install --no-cache-dir --no-deps . && useradd --uid 10001 --create-home bot && mkdir /app/data && chown bot:bot /app/data
USER bot
CMD ["python", "-m", "smartphone_bot"]
