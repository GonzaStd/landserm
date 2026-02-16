#!/bin/bash
set -e
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'
echo -e "${GREEN}=== Landserm Installation Script ===${NC}"
SCRIPT_PATH="$(readlink -f "$0")"
SCRIPT_DIR="$(dirname "$SCRIPT_PATH")"
LANDSERM_ROOT="$(dirname "$SCRIPT_DIR")"
SETUP_DIR="$LANDSERM_ROOT/setup/"
DAEMON_LOG_FILE="/var/log/landserm/landserm-daemon.log"
VENV_PATH="${LANDSERM_ROOT}/.venv"
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

touch "${DAEMON_LOG_FILE}"
cp "${LANDSERM_ROOT}/.env.template" "/etc/landserm/.env"
cp -rn config-template/* /etc/landserm 2>/dev/null || true
echo -e "${GREEN} Configuration template (folders and files) are now in /etc/landserm ${NC}"
echo -e "${YELLOW} Setting permissions...${NC}"
chown -R landserm:landserm /opt/landserm
chown -R landserm:landserm /var/log/landserm
chown -R landserm:landserm /etc/landserm
chmod 755 /opt/landserm
chmod 755 /var/log/landserm
chmod 750 /etc/landserm
chmod 700 /etc/landserm/.env

if ls user/scripts/*.sh 1> /dev/null 2>&1; then
    chmod 755 user/scripts/*.sh
    echo -e "${GREEN}Scripts in user/scripts/ directory are now executable${NC}"
fi

chmod 640 "${DAEMON_LOG_FILE}"
chown landserm:landserm "${DAEMON_LOG_FILE}"
echo -e "${GREEN}Log file ready at ${DAEMON_LOG_FILE} ${NC}"
if ! [[ -d "$VENV_PATH" ]]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv .venv
    echo -e "${GREEN}.venv folder was sucessfully created!${NC}"
fi
chown -R landserm:landserm .venv
echo -e "${GREEN}.venv ownership set to landserm:landserm${NC}"
echo -e "${YELLOW}Connecting to virtual env...${NC}"
source "${VENV_PATH}/bin/activate"
echo -e "${GREEN}Sucessfully connected!${NC}"
echo -e "${GREEN}Virtual environment is installed and set!${NC}"
echo -e "${YELLOW}Updating dependencies for landserm package...${NC}"
python3 $SETUP_DIR/update_dependencies.py
echo -e "${GREEN}Dependencies are now up to date!${NC}"
echo -e "${YELLOW}Installing \"landserm\" Python package...${NC}"
sudo -u landserm .venv/bin/pip install --no-cache-dir .
chown -R landserm:landserm .venv
echo -e "${GREEN}Package installed!${NC}"
echo -e "${YELLOW}Copying landserm-daemon wrapper to /usr/local/bin...${NC}"
cp $SETUP_DIR/landserm-daemon /usr/local/bin/landserm-daemon
chmod 750 /usr/local/bin/landserm-daemon
chown landserm:landserm /usr/local/bin/landserm-daemon
echo -e "${GREEN}landserm-daemon script installed in /usr/local/bin with correct owner and permissions!${NC}"

echo -e "${YELLOW}Copying landserm CLI wrapper to /usr/local/bin...${NC}"
cp $SETUP_DIR/landserm /usr/local/bin/landserm
chmod 755 /usr/local/bin/landserm
chown root:root /usr/local/bin/landserm
echo -e "${GREEN}landserm CLI script installed in /usr/local/bin!${NC}"

echo -e "${YELLOW}Setting up bash completion for landserm...${NC}"
_LANDSERM_COMPLETE=bash_source /usr/local/bin/landserm | tee /etc/bash_completion.d/landserm > /dev/null
chmod 644 /etc/bash_completion.d/landserm
echo -e "${GREEN}Bash completion installed!${NC}"
echo -e "${YELLOW}Note: Reload your shell or run 'source /etc/bash_completion.d/landserm' to activate completion${NC}"

echo -e "${YELLOW}Installing systemd service...${NC}"
cp $SETUP_DIR/landserm.service /etc/systemd/system
systemctl daemon-reload
echo -e "${GREEN}Service Installed!${NC}"

echo -e "${YELLOW}Configuring sudoers for landserm CLI...${NC}"
cat > /etc/sudoers.d/landserm <<EOF
# Allow users in sudo/wheel group to run landserm CLI as landserm user without password
%sudo ALL=(landserm) NOPASSWD: /opt/landserm/.venv/bin/landserm
%wheel ALL=(landserm) NOPASSWD: /opt/landserm/.venv/bin/landserm
EOF
chmod 440 /etc/sudoers.d/landserm
echo -e "${GREEN}Sudoers configured!${NC}"

read -p "Do you want to enable and start the service now? (y/n) " -r
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