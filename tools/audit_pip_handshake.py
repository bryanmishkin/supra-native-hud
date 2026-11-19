#!/usr/bin/env python3
"""Correlate saved DisplaySink subscriptions with selection/completion traffic.
Offline evidence only: no network, producer ownership or drawing authorization.
"""
import argparse
import json
from pathlib import Path
from audit_pip_sink import audit as tcp_audit
from audit_pip_discovery import audit as sd_audit


def audit(path):
    tcp, sd = tcp_audit(path), sd_audit(path)
    rows = []
    for event in tcp['events']:
        if event['type'] != 'selection':
            continue
        server, server_port, client, client_port = event['flow']
        stamp = event['timestamp_us']
        def valid_lease(row):
            return row['ttl'] > 0 and row['timestamp_us'] <= stamp < row['timestamp_us'] + row['ttl'] * 1000000
        subscriptions = [row for row in sd['events'] if row['kind'] == 6 and
                         row['source'] == client and row['destination'] == server and
                         row['ip'] == client and row['port'] == client_port and valid_lease(row)]
        acknowledgments = [row for row in sd['events'] if row['kind'] == 7 and
                           row['source'] == server and row['destination'] == client and valid_lease(row)]
        completions = [row for row in tcp['events'] if row['type'] == 'completion' and
                       row['flow'] == [client, client_port, server, server_port] and
                       row['selection'] == event['selection'] and
                       stamp <= row['timestamp_us'] <= stamp + 3000000]
        rows.append(dict(selection=event,
                         matching_subscription_observed=bool(subscriptions),
                         server_ack_in_valid_interval=bool(acknowledgments),
                         completion_within_3s=bool(completions)))
    return dict(pcap_sha256=tcp['pcap_sha256'], selections=rows,
                discovery_events=len(sd['events']), tcp_events=len(tcp['events']),
                other_b009_sd_packets=sd['other_b009_sd_packets'], errors=tcp['errors'],
                pixel_delivery_proven=False, producer_ownership_proven=False,
                limitation='Same-server ACK and lease interval are observations, not unique subscription-counter correlation. No event can mean activity was outside the recorded interval. Selection1 is the retained Kombi mapping; this audit never grants HUD drawing readiness.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pcap', type=Path)
    print(json.dumps(audit(parser.parse_args().pcap), indent=2))
