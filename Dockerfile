FROM python:3.11-slim

# Install SSH client so lunch_server.sh can SSH to the host
RUN apt-get update && apt-get install -y openssh-client && rm -rf /var/lib/apt/lists/*

# Create a non-root user to run the bot
RUN useradd -m -u 1006 -s /bin/bash watchrat

# Set working directory
WORKDIR /home/watchrat/watchrat

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot code
COPY . .

# Create SSH directory and set permissions
RUN mkdir -p /home/watchrat/.ssh && \
    chmod 700 /home/watchrat/.ssh && \
    chown -R watchrat:watchrat /home/watchrat

# Make lunch_server.sh executable
RUN chmod +x lunch_server.sh

# Run as botuser, not root
USER watchrat

CMD ["python", "main.py"]