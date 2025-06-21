# Dockerfile
FROM python:3.11-slim

# 1) System deps for Chrome
RUN apt-get update && \
    apt-get install -y \
      wget unzip xvfb \
      libglib2.0-0 libnss3 libatk1.0-0 libx11-xcb1 \
      libxrandr2 libasound2 libpangocairo-1.0-0 libcups2 libgtk-3-0 \
    && rm -rf /var/lib/apt/lists/*

# 2) Install Google Chrome
RUN wget -q -O /tmp/chrome.deb \
      https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
    apt-get update && apt-get install -y /tmp/chrome.deb && \
    rm /tmp/chrome.deb

WORKDIR /app

# 3) Copy application code + requirements
COPY server.py countries.py requirements.txt ./

# 4) Install Python dependencies
#    Make sure your requirements.txt pins selenium>=4.7
RUN pip install --no-cache-dir -r requirements.txt

# 5) Runtime
ENV API_KEY=changeme

# Expose the port Railway assigns (fallback to 8000 locally)
EXPOSE ${PORT:-8000}

# Launch Uvicorn on the correct port
CMD ["sh", "-c", "uvicorn server:app --host 0.0.0.0 --port ${PORT:-8000}"]
