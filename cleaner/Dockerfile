FROM python:3.12-slim

WORKDIR /camplux/cleaner

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5003
CMD ["python", "app.py"]
