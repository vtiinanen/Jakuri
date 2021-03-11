FROM python:alpine

#install python dependecies
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

#copy python scripts
COPY worker-client.py .
COPY server-coordinator.py .