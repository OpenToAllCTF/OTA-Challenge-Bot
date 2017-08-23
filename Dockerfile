FROM python:3

# Install requirements
RUN pip install --no-cache-dir -r requirements.txt

# Bundle app source
COPY . /src/

CMD ["python", "/src/run.py"]
