# 1. Use the official lightweight Python 3.14 image
FROM python:3.14-slim

# 2. Set the working directory inside the container
WORKDIR /app

# 3. Copy the requirements file and install the packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy your Streamlit app code into the container
COPY app.py .

# 5. Expose Streamlit's default port
EXPOSE 8501

# 6. Command to run the app when the container starts
# (Setting address to 0.0.0.0 is required for Docker to allow outside traffic)
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]