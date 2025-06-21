# Dockerfile
FROM python:3.11-slim

# 1) System deps + Chrome
RUN apt-get update && \
    apt-get install -y wget unzip xvfb \
      libglib2.0-0 libnss3 libatk1.0-0 libx11-xcb1 \
      libxrandr2 libasound2 libpangocairo-1.0-0 libcups2 libgtk-3-0 && \
    rm -rf /var/lib/apt/lists/*

# 2) Install Chrome
RUN wget -q -O /tmp/chrome.deb \
      https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
    apt-get update && apt-get install -y /tmp/chrome.deb && \
    rm /tmp/chrome.deb

# 3) Install matching Chromedriver
RUN CHROME_VER=$(google-chrome --version | awk '{print $3}' | cut -d. -f1) && \
    wget -q -O /tmp/driver.zip \
      "https://chromedriver.storage.googleapis.com/${CHROME_VER}.0/chromedriver_linux64.zip" && \
    unzip /tmp/driver.zip -d /usr/local/bin && \
    rm /tmp/driver.zip

WORKDIR /app

# 4) Copy code + deps
COPY server.py countries.py requirements.txt ./

# 5) Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# 6) Runtime settings
ENV API_KEY=changeme
EXPOSE 8000
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
