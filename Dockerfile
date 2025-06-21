# Dockerfile
FROM python:3.11-slim

# 1) System deps + Chrome dependencies
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

# 3) Install matching Chromedriver (major-only lookup)
RUN set -eux; \
    # grab Chrome major version, e.g. "114" from "Google Chrome 114.0.5735.199" \
    CHROME_MAJOR="$(google-chrome --version | awk '{print $3}' | cut -d. -f1)"; \
    # query the latest driver for that major version \
    DRIVER_VER="$(wget -qO- "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_MAJOR}")"; \
    echo "Installing Chromedriver $DRIVER_VER (for Chrome major $CHROME_MAJOR)"; \
    wget -qO /tmp/chromedriver.zip \
      "https://chromedriver.storage.googleapis.com/${DRIVER_VER}/chromedriver_linux64.zip"; \
    unzip /tmp/chromedriver.zip -d /usr/local/bin; \
    chmod +x /usr/local/bin/chromedriver; \
    rm /tmp/chromedriver.zip

WORKDIR /app

# 4) Copy code + requirements
COPY server.py countries.py requirements.txt ./

# 5) Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 6) Runtime settings
ENV API_KEY=changeme
EXPOSE 8000

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
