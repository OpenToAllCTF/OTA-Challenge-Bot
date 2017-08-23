FROM python:3

# Bundle app source
COPY . /src/
WORKDIR /src/

# Install requirements
RUN pip install --no-cache-dir -r /src/requirements.txt

CMD ["python", "/src/run.py"]
