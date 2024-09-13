# Use official Python slim image
FROM python:3.10.12-slim

# Set working directory
WORKDIR /

# Copy current directory contents into the container at /app
COPY . .

# Install any necessary dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port on which your app runs
EXPOSE 8080

# Explicitly mention the working directory in the gunicorn command
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "wsgi:app"]
