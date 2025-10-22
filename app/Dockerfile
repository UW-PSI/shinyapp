# Use an official Python runtime as a parent image
FROM python:3.9-slim-buster

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container at /app
COPY . .

# Expose the port that Shiny for Python listens on (default is 8000 or 8080)
EXPOSE 8000

# Command to run the Shiny app
CMD ["python", "-m", "shiny.run", "--port", "8000", "--host", "0.0.0.0", "app.py"]