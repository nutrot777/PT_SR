# Base image
FROM python:3.10

# Set the working directory
WORKDIR /app

# Copy the application code to the container
COPY . /app

# Install dependencies
RUN pip install -r requirements.txt

# Expose the port for Cloud Run
EXPOSE 8080

# Start the application
CMD ["python", "app.py"]