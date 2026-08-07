FROM python:3.12-slim

WORKDIR /camplux/weaver

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && python -m spacy download es_core_news_sm

COPY . .

EXPOSE 5005
CMD ["python", "app.py"]
