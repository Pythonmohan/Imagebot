# Use the official Python image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy the necessary files
COPY app.py /app/
COPY requirements.txt /app/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port (if necessary, for web services)
EXPOSE 5000

# Run the bot when the container starts
CMD ["python", "app.py"]
