#!/bin/bash
set -e
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'
VENV_PATH="${LANDSERM_ROOT}/.venv"
DAEMON_LOG_FILE="/var/log/landserm/landserm-daemon.log"
echo -e "${GREEN}=== Landserm Installation Script ===${NC}"

# Ensure the script is inside /opt/landserm
SCRIPT_PATH="$(readlink -f "$0")"
SCRIPT_DIR="$(dirname "$SCRIPT_PATH")"
LANDSERM_ROOT="$(dirname "$SCRIPT_PARENT")"
cd $LANDSERM_ROOT
LANDSERM_ROOT="$(pwd)"
if [[ "$LANDSERM_ROOT" != "/opt/landserm" ]]; then
    echo -e "${RED}ERROR: The installer script must be inside /opt/landserm (current: $SCRIPT_PATH)${NC}"
    echo -e "${RED}Move the repository to /opt/landserm and run the script from there.${NC}"
    exit 1
fi
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
echo -e "${YELLOW}Adding landserm user to messagebus group (it might already be in it)...${NC}"
usermod -aG messagebus landserm
echo -e "${GREEN}Added correctly!${NC}"

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
chown -R landserm:landserm /opt/landserm
chown -R landserm:landserm /var/log/landserm
chown -R landserm:landserm /etc/landserm
chmod 755 /opt/landserm
chmod 755 /var/log/landserm
chmod 750 /etc/landserm

chmod 640 "${DAEMON_LOG_FILE}"
chown landserm:landserm "${DAEMON_LOG_FILE}"
echo -e "${GREEN}Log file ready at ${DAEMON_LOG_FILE} ${NC}"
if ! [[ -d "$VENV_PATH" ]]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv .venv
    echo -e "${GREEN}.venv folder was sucessfully created!${NC}"
fi
chown -R landserm:landserm "$VENV_PATH"
echo -e "${GREEN}.venv ownership set to landserm:landserm${NC}"
echo -e "${YELLOW}Connecting to virtual env...${NC}"
source .venv/bin/activate
echo -e "${GREEN}Sucessfully connected!${NC}"
echo -e "${GREEN}Virtual environment is installed and set!${NC}"
echo -e "${YELLOW}Installing \"landserm\" Python package...${NC}"
pip install .
echo -e "${GREEN}Package installed!${NC}"
echo -e "${YELLOW}Copying landserm-daemon wrapper to /usr/local/bin...${NC}"
cp install/landserm-daemon /usr/local/bin/landserm-daemon
chmod 750 /usr/local/bin/landserm-daemon
chown landserm:landserm /usr/local/bin/landserm-daemon
echo -e "${GREEN}landserm-daemon script installed in /usr/local/bin with correct owner and permissions!${NC}"

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