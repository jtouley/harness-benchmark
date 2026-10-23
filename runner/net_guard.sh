#!/usr/bin/env bash
# Close the Docker bridge to everything but the proxy relay, for run_trial.sh --auth proxy.
#
#   sudo runner/net_guard.sh [PORT]      # PORT: the relay port (default 3129, as run_trial.sh uses)
#
# A container on the default bridge can open any port the host listens on at 0.0.0.0, through the
# bridge's gateway, and with IP forwarding on it may route further. These rules let traffic from the
# bridge reach the relay port on the host and nothing else: no other host port and no forwarding. They are
# added once and stay until the host's firewall is reset; running this again adds nothing. run_trial.sh
# --auth proxy does not depend on them being there: it probes the network from a container and refuses
# to start a trial that can reach anything but the relay.
set -euo pipefail
PORT=${1:-3129}
BRIDGE=${HB_BRIDGE:-docker0}
add() { local chain=$1; shift; iptables -C "$chain" "$@" 2>/dev/null || iptables "${ADD:--A}" "$chain" "$@"; }
ADD=-I add INPUT -i "$BRIDGE" -p tcp --dport "$PORT" -j ACCEPT
add INPUT -i "$BRIDGE" -j REJECT
ADD=-I add FORWARD -i "$BRIDGE" -j REJECT
echo "net_guard: from $BRIDGE, only tcp port $PORT on the host is open"
