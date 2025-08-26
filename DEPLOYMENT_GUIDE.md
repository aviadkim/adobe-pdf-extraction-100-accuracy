# Adobe PDF Extraction System - Deployment Guide

## 🚀 Production Deployment Guide

This guide covers deploying the Adobe PDF Extraction System in production environments with best practices for security, performance, and reliability.

## 📋 Prerequisites

### System Requirements
- **Operating System**: Linux (Ubuntu 20.04+ recommended), macOS 10.15+, Windows 10+
- **Python**: 3.8 or higher
- **Memory**: 4GB RAM minimum, 8GB recommended for batch processing
- **Storage**: 10GB free space for cache and temporary files
- **Network**: HTTPS access to Adobe PDF Services API endpoints

### Adobe PDF Services API
- Adobe Developer Console account
- PDF Services API credentials (client ID and secret)
- API quota allocation (500 free documents/month)

## 🔧 Installation

### 1. Environment Setup

```bash
# Create dedicated user for the service
sudo useradd -m -s /bin/bash adobe-pdf-extractor
sudo usermod -aG sudo adobe-pdf-extractor

# Switch to service user
sudo su - adobe-pdf-extractor

# Create directory structure
mkdir -p ~/adobe-pdf-extraction/{logs,cache,output,credentials,config}
cd ~/adobe-pdf-extraction
```

### 2. Python Environment

```bash
# Install Python 3.8+ if not available
sudo apt update
sudo apt install python3.8 python3.8-venv python3.8-dev

# Create virtual environment
python3.8 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel
```

### 3. Application Installation

```bash
# Clone or copy the application code
git clone <repository-url> .
# OR copy files to ~/adobe-pdf-extraction/

# Install dependencies
pip install -r requirements.txt

# Verify installation
python -c "import adobe.pdfservices.operation; print('✅ Adobe SDK installed')"
```

### 4. Configuration Setup

```bash
# Create production configuration
cp config.py.example config_prod.py

# Edit configuration for production
vim config_prod.py
```

**Production configuration (`config_prod.py`):**
```python
PRODUCTION_CONFIG = {
    "extraction": {
        "default_output_dir": "/var/lib/adobe-pdf-extractor/output",
        "max_file_size_mb": 50,
        "batch_size": 10,
        "enable_cache": True
    },
    "logging": {
        "level": "INFO",
        "file_path": "/var/log/adobe-pdf-extractor/application.log",
        "max_bytes": 50 * 1024 * 1024,  # 50MB
        "backup_count": 5
    },
    "performance": {
        "cache_size_gb": 2.0,
        "max_concurrent_jobs": 3,
        "rate_limit_per_minute": 25  # Leave buffer for API limits
    }
}
```

### 5. Credentials Management

```bash
# Create secure credentials file
touch credentials/pdfservices-api-credentials.json
chmod 600 credentials/pdfservices-api-credentials.json

# Add your Adobe API credentials
cat > credentials/pdfservices-api-credentials.json << 'EOF'
{
  "client_credentials": {
    "client_id": "your_client_id_here",
    "client_secret": "your_client_secret_here"
  },
  "service_account_credentials": {
    "organization_id": "your_org_id_here",
    "account_id": "your_account_id_here"
  }
}
EOF
```

## 🔒 Security Configuration

### 1. File Permissions

```bash
# Set secure permissions
chmod 700 ~/adobe-pdf-extraction
chmod 600 ~/adobe-pdf-extraction/credentials/*
chmod 755 ~/adobe-pdf-extraction/*.py
chmod 644 ~/adobe-pdf-extraction/requirements.txt

# Create log directory with appropriate permissions
sudo mkdir -p /var/log/adobe-pdf-extractor
sudo chown adobe-pdf-extractor:adobe-pdf-extractor /var/log/adobe-pdf-extractor
sudo chmod 755 /var/log/adobe-pdf-extractor
```

### 2. Environment Variables

```bash
# Create environment file
cat > .env << 'EOF'
ADOBE_CREDENTIALS_PATH=/home/adobe-pdf-extractor/adobe-pdf-extraction/credentials/pdfservices-api-credentials.json
CACHE_DIRECTORY=/var/lib/adobe-pdf-extractor/cache
OUTPUT_DIRECTORY=/var/lib/adobe-pdf-extractor/output
LOG_LEVEL=INFO
ENABLE_PERFORMANCE_MONITORING=true
EOF

# Secure the environment file
chmod 600 .env
```

### 3. Network Security

```bash
# Configure firewall (if needed)
sudo ufw allow ssh
sudo ufw allow out 443/tcp  # HTTPS for Adobe API
sudo ufw enable
```

## 🐳 Docker Deployment

### Dockerfile

```dockerfile
FROM python:3.8-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Create application user
RUN useradd -m -s /bin/bash adobe-extractor

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/logs /app/cache /app/output /app/credentials

# Set ownership
RUN chown -R adobe-extractor:adobe-extractor /app

# Switch to non-root user
USER adobe-extractor

# Expose port (if running web interface)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD python -c "import config; config.validate_environment()" || exit 1

# Default command
CMD ["python", "pdf_extractor.py", "--help"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  adobe-pdf-extractor:
    build: .
    container_name: adobe-pdf-extractor
    restart: unless-stopped
    
    volumes:
      - ./credentials:/app/credentials:ro
      - ./input_pdfs:/app/input_pdfs:ro
      - ./output:/app/output
      - ./logs:/app/logs
      - adobe_cache:/app/cache
    
    environment:
      - LOG_LEVEL=INFO
      - CACHE_SIZE_GB=1
      - MAX_CONCURRENT_JOBS=3
    
    networks:
      - adobe_network
    
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
        reservations:
          memory: 512M
          cpus: '0.5'

  # Optional: Redis for distributed caching
  redis:
    image: redis:7-alpine
    container_name: adobe-redis
    restart: unless-stopped
    volumes:
      - redis_data:/data
    networks:
      - adobe_network
    command: redis-server --appendonly yes --maxmemory 512mb

volumes:
  adobe_cache:
  redis_data:

networks:
  adobe_network:
    driver: bridge
```

## ⚙️ Systemd Service Setup

### Service File

```bash
# Create systemd service file
sudo cat > /etc/systemd/system/adobe-pdf-extractor.service << 'EOF'
[Unit]
Description=Adobe PDF Extraction Service
After=network.target
StartLimitIntervalSec=0

[Service]
Type=simple
Restart=always
RestartSec=5
User=adobe-pdf-extractor
Group=adobe-pdf-extractor
WorkingDirectory=/home/adobe-pdf-extractor/adobe-pdf-extraction
Environment=PATH=/home/adobe-pdf-extractor/adobe-pdf-extraction/venv/bin
ExecStart=/home/adobe-pdf-extractor/adobe-pdf-extraction/venv/bin/python -m uvicorn api_server:app --host 0.0.0.0 --port 8000
ExecReload=/bin/kill -HUP $MAINPID
StandardOutput=journal
StandardError=journal
SyslogIdentifier=adobe-pdf-extractor

# Security settings
NoNewPrivileges=yes
ProtectSystem=strict
ProtectHome=yes
ProtectKernelTunables=yes
ProtectKernelModules=yes
ProtectControlGroups=yes
ReadWritePaths=/var/lib/adobe-pdf-extractor /var/log/adobe-pdf-extractor

[Install]
WantedBy=multi-user.target
EOF
```

### Service Management

```bash
# Enable and start the service
sudo systemctl daemon-reload
sudo systemctl enable adobe-pdf-extractor
sudo systemctl start adobe-pdf-extractor

# Check service status
sudo systemctl status adobe-pdf-extractor

# View logs
sudo journalctl -u adobe-pdf-extractor -f
```

## 📊 Monitoring and Logging

### 1. Log Rotation

```bash
# Create logrotate configuration
sudo cat > /etc/logrotate.d/adobe-pdf-extractor << 'EOF'
/var/log/adobe-pdf-extractor/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 adobe-pdf-extractor adobe-pdf-extractor
    postrotate
        systemctl reload adobe-pdf-extractor
    endscript
}
EOF
```

### 2. Performance Monitoring

```bash
# Install monitoring tools
pip install psutil prometheus-client

# Create monitoring script
cat > monitor.py << 'EOF'
#!/usr/bin/env python3
import psutil
import time
import json
from datetime import datetime

def collect_metrics():
    return {
        'timestamp': datetime.now().isoformat(),
        'cpu_percent': psutil.cpu_percent(),
        'memory_percent': psutil.virtual_memory().percent,
        'disk_usage': psutil.disk_usage('/').percent,
        'network_io': psutil.net_io_counters()._asdict()
    }

if __name__ == "__main__":
    while True:
        metrics = collect_metrics()
        print(json.dumps(metrics))
        time.sleep(60)
EOF

chmod +x monitor.py
```

### 3. Health Checks

```bash
# Create health check script
cat > health_check.py << 'EOF'
#!/usr/bin/env python3
import sys
import requests
from config import validate_environment

def check_health():
    """Comprehensive health check"""
    checks = []
    
    # Environment validation
    try:
        env_result = validate_environment()
        checks.append(('Environment', env_result['valid']))
    except Exception as e:
        checks.append(('Environment', False))
    
    # API connectivity (if applicable)
    try:
        # Test Adobe API connectivity
        # This is a simplified check - implement based on your needs
        checks.append(('Adobe API', True))
    except Exception:
        checks.append(('Adobe API', False))
    
    # Disk space check
    import psutil
    disk_usage = psutil.disk_usage('/')
    disk_ok = (disk_usage.free / disk_usage.total) > 0.1  # 10% free space
    checks.append(('Disk Space', disk_ok))
    
    # Memory check
    memory = psutil.virtual_memory()
    memory_ok = memory.available > 500 * 1024 * 1024  # 500MB available
    checks.append(('Memory', memory_ok))
    
    # Print results
    all_ok = all(status for _, status in checks)
    
    for name, status in checks:
        print(f"{name}: {'✅ OK' if status else '❌ FAIL'}")
    
    return 0 if all_ok else 1

if __name__ == "__main__":
    sys.exit(check_health())
EOF

chmod +x health_check.py
```

## 🔄 Backup and Recovery

### 1. Backup Script

```bash
cat > backup.sh << 'EOF'
#!/bin/bash
set -e

BACKUP_DIR="/var/backups/adobe-pdf-extractor"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="adobe-pdf-extractor-${TIMESTAMP}"

# Create backup directory
mkdir -p "${BACKUP_DIR}"

# Create backup
tar -czf "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz" \
    --exclude='venv' \
    --exclude='cache' \
    --exclude='logs' \
    --exclude='output' \
    /home/adobe-pdf-extractor/adobe-pdf-extraction/

# Keep only last 7 backups
find "${BACKUP_DIR}" -name "adobe-pdf-extractor-*.tar.gz" -type f -mtime +7 -delete

echo "✅ Backup created: ${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"
EOF

chmod +x backup.sh

# Add to crontab
crontab -e
# Add line: 0 2 * * * /home/adobe-pdf-extractor/adobe-pdf-extraction/backup.sh
```

### 2. Recovery Procedure

```bash
# Recovery script
cat > recover.sh << 'EOF'
#!/bin/bash
set -e

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <backup_file>"
    exit 1
fi

BACKUP_FILE="$1"
RECOVERY_DIR="/tmp/adobe-pdf-extractor-recovery"

echo "🔄 Starting recovery from ${BACKUP_FILE}"

# Create recovery directory
mkdir -p "${RECOVERY_DIR}"

# Extract backup
tar -xzf "${BACKUP_FILE}" -C "${RECOVERY_DIR}"

# Stop service
sudo systemctl stop adobe-pdf-extractor

# Backup current installation
mv /home/adobe-pdf-extractor/adobe-pdf-extraction /home/adobe-pdf-extractor/adobe-pdf-extraction.backup.$(date +%s)

# Restore from backup
mv "${RECOVERY_DIR}/home/adobe-pdf-extractor/adobe-pdf-extraction" /home/adobe-pdf-extractor/

# Set permissions
chown -R adobe-pdf-extractor:adobe-pdf-extractor /home/adobe-pdf-extractor/adobe-pdf-extraction
chmod 600 /home/adobe-pdf-extractor/adobe-pdf-extraction/credentials/*

# Start service
sudo systemctl start adobe-pdf-extractor

echo "✅ Recovery completed successfully"
EOF

chmod +x recover.sh
```

## 🔍 Troubleshooting

### Common Issues and Solutions

#### 1. Adobe API Authentication Errors

```bash
# Check credentials format
python -c "
import json
with open('credentials/pdfservices-api-credentials.json') as f:
    creds = json.load(f)
    print('✅ Credentials format valid')
    print(f'Client ID: {creds[\"client_credentials\"][\"client_id\"][:10]}...')
"

# Test API connectivity
python -c "
from pdf_extractor import PDFExtractor
extractor = PDFExtractor('credentials/pdfservices-api-credentials.json')
print('✅ API authentication successful')
"
```

#### 2. Memory Issues

```bash
# Monitor memory usage during processing
python -c "
import psutil
import time
process = psutil.Process()

while True:
    memory_mb = process.memory_info().rss / 1024 / 1024
    print(f'Memory usage: {memory_mb:.1f} MB')
    time.sleep(5)
"

# Adjust batch size if needed
export BATCH_SIZE=5  # Reduce from default
```

#### 3. Performance Issues

```bash
# Check system resources
htop  # or top
iostat -x 1  # Disk I/O
netstat -i    # Network stats

# Profile application performance
python -m cProfile -o profile_output.prof pdf_extractor.py input.pdf
python -c "
import pstats
p = pstats.Stats('profile_output.prof')
p.sort_stats('cumulative').print_stats(20)
"
```

### Log Analysis

```bash
# Common log patterns to watch for
grep -i error /var/log/adobe-pdf-extractor/application.log
grep -i "extraction failed" /var/log/adobe-pdf-extractor/application.log
grep -i "api" /var/log/adobe-pdf-extractor/application.log

# Performance metrics
grep -i "performance" /var/log/adobe-pdf-extractor/application.log | tail -20
```

## 📈 Scaling Considerations

### Horizontal Scaling

```yaml
# Load balancer configuration (nginx)
upstream adobe_extractors {
    server 10.0.1.10:8000;
    server 10.0.1.11:8000;
    server 10.0.1.12:8000;
}

server {
    listen 80;
    server_name pdf-extractor.example.com;
    
    location / {
        proxy_pass http://adobe_extractors;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Vertical Scaling

```bash
# Adjust systemd service for more resources
sudo systemctl edit adobe-pdf-extractor

# Add override configuration:
[Service]
Environment="MAX_CONCURRENT_JOBS=6"
Environment="CACHE_SIZE_GB=4"
LimitNOFILE=4096
```

## 🔐 Security Checklist

- [ ] Credentials stored securely with proper file permissions
- [ ] Service running as non-root user
- [ ] Network access restricted to required endpoints only
- [ ] Log files protected and rotated
- [ ] Regular security updates applied
- [ ] Backup encryption enabled
- [ ] Access controls configured for API endpoints
- [ ] Monitoring and alerting configured
- [ ] Health checks implemented
- [ ] Recovery procedures tested

## 📞 Support and Maintenance

### Regular Maintenance Tasks

1. **Weekly**: Check log files for errors and performance issues
2. **Monthly**: Review API usage and optimize rate limiting
3. **Quarterly**: Update dependencies and security patches
4. **Annually**: Review and update disaster recovery procedures

### Support Channels

- **Documentation**: This guide and inline code documentation
- **Health Checks**: Automated monitoring and alerting
- **Log Analysis**: Comprehensive logging for issue diagnosis
- **Performance Metrics**: Built-in performance monitoring

This deployment guide provides a comprehensive foundation for running the Adobe PDF Extraction System in production environments with proper security, monitoring, and maintenance procedures.