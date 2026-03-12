# Deployment Guide - Driver AI Co-Pilot Unified Application

## Overview
This guide covers deploying the unified Driver AI Co-Pilot application where the Flask backend serves the React frontend as a single integrated application.

## Architecture
```
┌─────────────────────────────────────────┐
│           Flask Server (Port 5000)      │
├─────────────────────────────────────────┤
│  ┌─────────────────┐ ┌─────────────────┐│
│  │   React App     │ │   API Routes    ││
│  │  (Static Files) │ │   (/api/...)    ││
│  │                 │ │                 ││
│  │ • Dashboard     │ │ • Authentication││
│  │ • Auth Pages    │ │ • Vision AI     ││
│  │ • Settings      │ │ • Database      ││
│  └─────────────────┘ └─────────────────┘│
└─────────────────────────────────────────┘
```

## Prerequisites

### System Requirements
- **Python 3.8+** with pip
- **Node.js 16+** with npm
- **Webcam** for real-time monitoring
- **4GB RAM** minimum (8GB recommended)
- **2GB disk space** for dependencies

### Dependencies
```bash
# Check versions
python --version  # Should be 3.8+
node --version    # Should be 16+
npm --version     # Should be 8+
```

## Local Development Setup

### 1. Clone and Setup
```bash
git clone <repository-url>
cd driver-ai-copilot
```

### 2. Install Dependencies
```bash
# Option A: Automated (Recommended)
npm run install:all

# Option B: Manual
npm install
cd frontend && npm install
cd ../backend && pip install -r requirements.txt
```

### 3. Build and Run
```bash
# Quick start
python start.py
# or
start.bat  # Windows

# Manual
npm run build
npm start
```

### 4. Access Application
- **URL**: http://localhost:5000
- **API**: http://localhost:5000/api/health

## Production Deployment

### Option 1: Single Server Deployment

#### 1. Server Setup (Ubuntu/CentOS)
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.8+
sudo apt install python3 python3-pip python3-venv -y

# Install Node.js 18 LTS
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs -y

# Install system dependencies for OpenCV
sudo apt install libgl1-mesa-glx libglib2.0-0 libsm6 libxext6 libxrender-dev libgomp1 -y
```

#### 2. Application Deployment
```bash
# Create application directory
sudo mkdir -p /opt/driver-ai-copilot
sudo chown $USER:$USER /opt/driver-ai-copilot
cd /opt/driver-ai-copilot

# Clone repository
git clone <repository-url> .

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
npm run install:all

# Build frontend
npm run build

# Test the application
python test_integration.py
```

#### 3. Production Server Setup (Gunicorn)
```bash
# Install Gunicorn
pip install gunicorn

# Create Gunicorn config
cat > gunicorn.conf.py << EOF
bind = "0.0.0.0:5000"
workers = 4
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2
max_requests = 1000
max_requests_jitter = 100
preload_app = True
EOF

# Start with Gunicorn
cd backend
gunicorn --config ../gunicorn.conf.py run:app
```

#### 4. Systemd Service (Linux)
```bash
# Create service file
sudo tee /etc/systemd/system/driver-ai-copilot.service << EOF
[Unit]
Description=Driver AI Co-Pilot Application
After=network.target

[Service]
Type=exec
User=$USER
WorkingDirectory=/opt/driver-ai-copilot/backend
Environment=PATH=/opt/driver-ai-copilot/venv/bin
ExecStart=/opt/driver-ai-copilot/venv/bin/gunicorn --config ../gunicorn.conf.py run:app
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable driver-ai-copilot
sudo systemctl start driver-ai-copilot
sudo systemctl status driver-ai-copilot
```

### Option 2: Docker Deployment

#### 1. Create Dockerfile
```dockerfile
FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./
COPY frontend/package*.json ./frontend/
COPY backend/requirements.txt ./backend/

# Install dependencies
RUN npm install
RUN cd frontend && npm install
RUN cd backend && pip install -r requirements.txt

# Copy application code
COPY . .

# Build frontend
RUN npm run build

# Expose port
EXPOSE 5000

# Start application
CMD ["python", "backend/run.py"]
```

#### 2. Docker Compose
```yaml
version: '3.8'
services:
  driver-ai-copilot:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - ./data:/app/backend/instance
    environment:
      - FLASK_ENV=production
      - SECRET_KEY=your-secret-key-here
    restart: unless-stopped
```

#### 3. Build and Run
```bash
# Build image
docker build -t driver-ai-copilot .

# Run container
docker run -p 5000:5000 -v $(pwd)/data:/app/backend/instance driver-ai-copilot

# Or use Docker Compose
docker-compose up -d
```

## Reverse Proxy Setup (Nginx)

### 1. Install Nginx
```bash
sudo apt install nginx -y
```

### 2. Configure Nginx
```bash
sudo tee /etc/nginx/sites-available/driver-ai-copilot << EOF
server {
    listen 80;
    server_name your-domain.com;

    client_max_body_size 10M;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # WebSocket support (if needed)
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Static files caching
    location /assets/ {
        proxy_pass http://127.0.0.1:5000;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/driver-ai-copilot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## SSL/HTTPS Setup (Let's Encrypt)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Get SSL certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

## Environment Variables

### Production Environment
```bash
# Create .env file in backend directory
cat > backend/.env << EOF
FLASK_ENV=production
SECRET_KEY=your-super-secret-key-change-this
DATABASE_URL=sqlite:///instance/driver_monitor.db
CORS_ORIGINS=https://your-domain.com
EOF
```

## Monitoring and Logs

### 1. Application Logs
```bash
# Systemd logs
sudo journalctl -u driver-ai-copilot -f

# Application logs
tail -f /opt/driver-ai-copilot/backend/app.log
```

### 2. Health Monitoring
```bash
# Create health check script
cat > /opt/driver-ai-copilot/health_check.sh << EOF
#!/bin/bash
curl -f http://localhost:5000/health || exit 1
EOF

chmod +x /opt/driver-ai-copilot/health_check.sh

# Add to crontab for monitoring
crontab -e
# Add: */5 * * * * /opt/driver-ai-copilot/health_check.sh
```

## Performance Optimization

### 1. Frontend Optimization
- Gzip compression enabled in Nginx
- Static asset caching
- CDN for static files (optional)

### 2. Backend Optimization
- Gunicorn with multiple workers
- Database connection pooling
- Redis for session storage (optional)

### 3. System Optimization
```bash
# Increase file limits
echo "* soft nofile 65536" >> /etc/security/limits.conf
echo "* hard nofile 65536" >> /etc/security/limits.conf

# Optimize Python
export PYTHONUNBUFFERED=1
export PYTHONDONTWRITEBYTECODE=1
```

## Backup Strategy

### 1. Database Backup
```bash
# Create backup script
cat > /opt/driver-ai-copilot/backup.sh << EOF
#!/bin/bash
DATE=\$(date +%Y%m%d_%H%M%S)
cp /opt/driver-ai-copilot/backend/instance/driver_monitor.db \
   /opt/driver-ai-copilot/backups/db_backup_\$DATE.db
find /opt/driver-ai-copilot/backups -name "db_backup_*.db" -mtime +7 -delete
EOF

chmod +x /opt/driver-ai-copilot/backup.sh

# Schedule daily backups
crontab -e
# Add: 0 2 * * * /opt/driver-ai-copilot/backup.sh
```

## Troubleshooting

### Common Issues

1. **Port 5000 already in use**
   ```bash
   sudo lsof -i :5000
   sudo kill -9 <PID>
   ```

2. **Camera access issues**
   - Check browser permissions
   - Ensure HTTPS for production
   - Verify camera device availability

3. **MediaPipe installation issues**
   ```bash
   pip uninstall mediapipe
   pip install --no-cache-dir mediapipe
   ```

4. **Frontend not loading**
   ```bash
   # Rebuild frontend
   cd frontend
   rm -rf dist node_modules
   npm install
   npm run build
   ```

## Security Considerations

1. **Change default secret key**
2. **Use HTTPS in production**
3. **Implement rate limiting**
4. **Regular security updates**
5. **Firewall configuration**
6. **Database security**

## Support

For issues and support:
1. Check logs: `sudo journalctl -u driver-ai-copilot -f`
2. Run health check: `curl http://localhost:5000/health`
3. Test integration: `python test_integration.py`
4. Check system resources: `htop`, `df -h`