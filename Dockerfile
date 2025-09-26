FROM python:3.10
WORKDIR /app
COPY . .
RUN rm -f .env
RUN pip install -r requirements.txt
CMD ["python", "run.py"]