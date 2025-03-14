# Use an official Python runtime as a parent image
FROM python:3.11.9-slim

# Set the working directory in the container
WORKDIR /app

# Install any needed packages specified in requirements.txt
COPY requirements.txt ./

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY src ./src

# Set PYTHONPATH to include the src directory
ENV PYTHONPATH "/app"

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Command to run the server
CMD ["python3", "src/main.py"]
