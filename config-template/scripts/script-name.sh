#!/bin/bash
# This is just an example. This will be shown in the daemon when a policy matches with an event
# and when the policy has the rule to execute this script with its 5 given arguments
echo "===== LandSerM Event ====="
echo "Domain: $1"
echo "Subject: $2"
echo "Kind: $3"
echo "ACTIVE: $4"
echo "SUBSTATE: $5"
echo "Timestamp: $(date)"
echo "=========================="