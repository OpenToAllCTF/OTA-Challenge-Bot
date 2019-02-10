FROM python:3

WORKDIR /src

# Copy requirements
COPY ./requirements.txt /src

# Install requirements
RUN pip install --no-cache-dir -r requirements.txt

# Copy rest of source
COPY . /src

CMD ["python", "run.py"]
