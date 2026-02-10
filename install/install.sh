#!/bin/bash
set -e
source .venv/bin/activate
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'
DAEMON_LOG_FILE="/var/log/landserm/landserm-daemon.log"
echo -e "${GREEN}=== Landserm Installation Script ===${NC}"
if [[ $EUID -ne 0 ]]; then 
    echo -e "${RED}This script must be run as root${NC}"
    exit 1
fi
if ! id -u landserm &> /dev/null; then
    echo -e "${YELLOW}Creating landserm user...${NC}"
    useradd --system --no-create-home --shell /usr/sbin/nologin landserm
    echo -e "${GREEN} User created!${NC}"
else
    echo -e "${YELLOW}User landserm already exists${NC}"
fi

echo -e "${YELLOW}Creating directories...${NC}"
mkdir -p /opt/landserm
mkdir -p /var/log/landserm
mkdir -p /etc/landserm

touch "$DAEMON_LOG_FILE"

if [ -d "config-template" ]; then
    cp -rn config-template/* /etc/landserm 2>/dev/null || true
    echo -e "${GREEN} Configuration template (folders and files) are now in /etc/landserm ${NC}"
fi

echo -e "${YELLOW} Setting permissions...${NC}"
chown -R landserm /opt/landserm
chown -R landserm /var/log/landserm
chown -R landserm /etc/landserm
chmod 755 /opt/landserm
chmod 755 /var/log/landserm
chmod 750 /etc/landserm

chmod 640 "$DAEMON_LOG_FILE"
chown landserm:landserm "$DAEMON_LOG_FILE"
echo -e "${GREEN} Log file ready at $DAEMON_LOG_FILE ${NC}"

echo -e "${YELLOW}Installing \"landserm\" Python package...${NC}"
pip install .
echo -e "${GREEN}Package installed!${NC}"
echo -e "${YELLOW}Installing systemd service...${NC}"
cp install/landserm.service /etc/systemd/system
systemctl daemon-reload
echo -e "${GREEN}Service Installed!${NC}"
read -p "Do you want to enable and start the service now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    systemctl enable landserm.service
    systemctl start landserm.service
    echo -e "${GREEN}Service enabled and started${NC}"
    echo -e "${YELLOW}Check status with: systemctl status landserm${NC}"
else
    echo -e "${YELLOW}To start later, run:${NC}"
    echo "systemctl enable landserm.service"
    echo "systemctl start landserm.service"
fi

echo -e "${GREEN}=== Installation complete ===${NC}"