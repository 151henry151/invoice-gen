#!/bin/bash

# Prompt for server IP if not provided
if [ -z "$1" ]; then
    read -p "Enter server IP address: " SERVER_IP
else
    SERVER_IP=$1
fi

# Prompt for domain name
read -p "Enter domain name (e.g., example.com): " DOMAIN

APP_DIR="/opt/invoice_gen"
LOCATION="/invoice"

# Create deployment package
echo "Creating deployment package..."
tar -czf deploy.tar.gz \
    app.py \
    requirements.txt \
    static/ \
    templates/ \
    Invoice.xlsx

# Copy files to server
echo "Copying files to server..."
scp deploy.tar.gz root@$SERVER_IP:/tmp/

# SSH into server and run setup
ssh root@$SERVER_IP << EOF
    # Update system
    apt-get update
    apt-get upgrade -y

    # Install required packages
    apt-get install -y python3 python3-pip python3-venv nginx certbot python3-certbot-nginx

    # Create application directory
    mkdir -p $APP_DIR
    cd $APP_DIR

    # Extract deployment package
    tar -xzf /tmp/deploy.tar.gz -C $APP_DIR
    rm /tmp/deploy.tar.gz

    # Create virtual environment
    python3 -m venv venv
    source venv/bin/activate

    # Install Python dependencies
    pip install -r requirements.txt

    # Create systemd service
    cat > /etc/systemd/system/invoice-gen.service << EOL
[Unit]
Description=Invoice Generator Service
After=network.target

[Service]
User=root
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
ExecStart=$APP_DIR/venv/bin/python3 $APP_DIR/app.py
Restart=always

[Install]
WantedBy=multi-user.target
EOL

    # Configure Nginx
    cat > /etc/nginx/sites-available/$DOMAIN << EOL
server {
    listen 80;
    server_name $DOMAIN;

    location $LOCATION {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Add trailing slash if missing
        rewrite ^$LOCATION$ $LOCATION/ permanent;
    }

    # Serve static files directly
    location $LOCATION/static {
        alias $APP_DIR/static;
    }
}
EOL

    # Enable Nginx configuration
    ln -sf /etc/nginx/sites-available/$DOMAIN /etc/nginx/sites-enabled/
    rm -f /etc/nginx/sites-enabled/default

    # Get SSL certificate
    certbot --nginx -d $DOMAIN --non-interactive --agree-tos --email admin@$DOMAIN

    # Start services
    systemctl daemon-reload
    systemctl enable invoice-gen
    systemctl start invoice-gen
    systemctl restart nginx

    # Set permissions
    chown -R root:root $APP_DIR
    chmod -R 755 $APP_DIR
EOF

echo "Deployment complete! The application is now running at https://$DOMAIN$LOCATION" 