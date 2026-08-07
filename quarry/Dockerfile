FROM python:3.12-slim

# WORKDIR mirrors the monorepo's real layout (camplux/quarry, sibling to
# camplux/vault) on purpose -- quarry/local_db.py finds Vault's archive via
# a relative "../vault/data" path, unmodified from how it works outside
# Docker. See docker-compose.yml: both services mount the same named volume
# at /camplux/vault/data.
WORKDIR /camplux/quarry
RUN mkdir -p /camplux/vault/data

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5002
CMD ["python", "app.py"]
