FROM python:3

# Bundle app source
COPY . /src/
WORKDIR /src/

# Install requirements
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "run.py"]
