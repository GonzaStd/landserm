#!/bin/bash
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_PATH="${SCRIPT_DIR}/../.venv"
if [ -d "$VENV_PATH" ]; then
    source "${VENV_PATH}/bin/activate"
else
    echo "You don't have .venv"
    exit
fi

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}=== Landserm Uninstallation Script ===${NC}"

if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}This script must be run as root${NC}" 
   exit 1
fi

if systemctl is-active --quiet landserm; then
    echo -e "${YELLOW}Stopping service...${NC}"
    systemctl stop landserm.service
fi

if systemctl is-enabled --quiet landserm; then
    echo -e "${YELLOW}Disabling service...${NC}"
    systemctl disable landserm.service
fi

if [ -f "/etc/systemd/system/landserm.service" ]; then
    rm /etc/systemd/system/landserm.service
    systemctl daemon-reload
    echo -e "${GREEN}Service removed${NC}"
fi

pip uninstall -y landserm

read -p "Remove landserm program? (No configuration) (y/n) " -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -rf /opt/landserm
fi

read -p "Remove configuration? (y/n) " -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -rf /var/log/landserm
    rm -rf /etc/landserm
    echo -e "${GREEN}Data removed${NC}"
fi

read -p "Remove landserm user? (y/n) " -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    userdel landserm
    echo -e "${GREEN}User removed${NC}"
fi

echo -e "${GREEN}=== Uninstallation complete ===${NC}"