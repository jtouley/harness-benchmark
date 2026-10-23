#!/usr/bin/env bash
# Close the Docker bridge to everything on the host but the relay ports, for run_trial.sh --auth proxy.
#
#   sudo runner/net_guard.sh [PORTS]      # PORTS: the relay port range, FIRST:LAST (default 3129:3148,
#                                         # the range run_trial.sh picks a free port from)
#
# A container on the default bridge can open any port the host listens on at 0.0.0.0, through the
# bridge's gateway, and with IP forwarding on it may route further. These rules let traffic from the
# bridge reach the relay ports on the host and nothing else on the host, and nothing through forwarding.
#
# The rules are inserted at the top of their chains (-I 1), never appended: a distribution, ufw or a
# conntrack rule that already accepts docker0 traffic would otherwise sit above an appended REJECT and
# keep the bridge open. Forwarding is cut in DOCKER-USER when Docker has made that chain (Docker
# evaluates it before its own FORWARD rules), else in FORWARD. That cut takes egress from every
# container on docker0, trials and any other container alike, for as long as the rules stay; a
# container that needs the network must use another bridge. The rules are added once and stay until the
# host's firewall is reset; running this again adds nothing (each rule is checked with -C first).
# run_trial.sh --auth proxy does not depend on them being there: it probes the network from a container
# and refuses to start a trial that can reach anything but the relay.
set -euo pipefail
PORTS=${1:-3129:3148}
BRIDGE=${HB_BRIDGE:-docker0}
case "$PORTS" in
  *[!0-9:]*|'') echo "net_guard: PORTS must be FIRST:LAST or one port, got $PORTS" >&2; exit 2 ;;
esac
IPT=${HB_IPTABLES:-iptables}
# Insert at position 1 unless the rule is there already. Each later insert goes above the earlier ones,
# so the ACCEPT is inserted after the REJECT and ends up above it.
add() { local chain=$1; shift; "$IPT" -C "$chain" "$@" 2>/dev/null || "$IPT" -I "$chain" 1 "$@"; }
add INPUT -i "$BRIDGE" -j REJECT
add INPUT -i "$BRIDGE" -p tcp --dport "$PORTS" -j ACCEPT
if "$IPT" -L DOCKER-USER -n >/dev/null 2>&1; then
  add DOCKER-USER -i "$BRIDGE" -j REJECT
else
  add FORWARD -i "$BRIDGE" -j REJECT
fi
echo "net_guard: from $BRIDGE, only tcp ports $PORTS on the host are open, and nothing is forwarded"
