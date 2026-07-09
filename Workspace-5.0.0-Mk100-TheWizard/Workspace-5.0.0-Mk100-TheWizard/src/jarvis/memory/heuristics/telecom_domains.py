"""Telecom and networking domain mappings.

Covers carrier-grade networking, telecom protocols, OSS/BSS systems,
network telemetry, SDN, routing protocols, and vendor-specific platforms
(Cisco, Nokia, etc.).
"""

from __future__ import annotations

from typing import Dict

# Keyword-based classification for telecom & networking
TELECOM_KEYWORD_MAP: Dict[str, str] = {
    # Generic Networking
    "networking": "network.core",
    "network infrastructure": "network.core",
    "network architecture": "network.core",
    "network design": "network.core",

    # Cisco (from conversation index - Telemetry TLS Configuration)
    "cisco": "network.cisco",
    "cisco ios": "network.cisco",
    "cisco nexus": "network.cisco",
    "cisco catalyst": "network.cisco",
    "cisco asa": "network.cisco.asa",  # Firewall (keep existing)
    "cisco telemetry": "network.cisco.telemetry",
    "cisco tls": "network.cisco.telemetry",
    "cisco router": "network.cisco",
    "cisco switch": "network.cisco",

    # Nokia (from conversation index - Nokia SR OS Telemetry)
    "nokia": "network.nokia",
    "nokia sros": "network.nokia.sros",
    "sr os": "network.nokia.sros",
    "service router": "network.nokia.sros",
    "nokia telemetry": "network.nokia",

    # Network Telemetry (from conversation index - RAM/CPU Telemetry)
    "network telemetry": "network.telemetry",
    "telemetry streaming": "network.telemetry",
    "telemetry collector": "network.telemetry",
    "snmp": "network.telemetry",
    "netflow": "network.telemetry",
    "sflow": "network.telemetry",
    "ipfix": "network.telemetry",
    "grpc telemetry": "network.telemetry",
    "model-driven telemetry": "network.telemetry",
    "yang model": "network.telemetry",

    # Routing Protocols
    "bgp": "network.bgp",
    "border gateway protocol": "network.bgp",
    "bgp routing": "network.bgp",
    "ospf": "network.ospf",
    "open shortest path first": "network.ospf",
    "isis": "network.isis",
    "is-is": "network.isis",
    "intermediate system": "network.isis",
    "rip ": "network.routing",
    "eigrp": "network.routing",
    "routing protocol": "network.routing",
    "static route": "network.routing",

    # MPLS & Carrier Technologies
    "mpls": "network.mpls",
    "multi-protocol label switching": "network.mpls",
    "label switching": "network.mpls",
    "vpls": "network.mpls",
    "vrf ": "network.mpls",
    "vpn ": "network.vpn",  # Keep existing
    "ipsec": "network.vpn",  # Keep existing
    "l2vpn": "network.mpls",
    "l3vpn": "network.mpls",

    # SDN & Network Automation
    "sdn ": "network.sdn",
    "software-defined network": "network.sdn",
    "openflow": "network.sdn",
    "network automation": "network.sdn",
    "network orchestration": "network.sdn",
    "nfv ": "network.sdn",
    "network function virtualization": "network.sdn",

    # Overlay Networks
    "vxlan": "network.vxlan",
    "vx lan": "network.vxlan",
    "geneve": "network.overlay",
    "nvgre": "network.overlay",
    "overlay network": "network.overlay",

    # QoS & Traffic Engineering
    "qos ": "network.qos",
    "quality of service": "network.qos",
    "traffic shaping": "network.qos",
    "traffic policing": "network.qos",
    "traffic engineering": "network.qos",
    "diffserv": "network.qos",
    "intserv": "network.qos",

    # OSS/BSS (from "OSS IP Providers" background)
    "oss ": "telecom.oss",
    "operations support": "telecom.oss",
    "network management": "telecom.oss",
    "fault management": "telecom.oss",
    "configuration management": "telecom.oss",
    "performance management": "telecom.oss",
    "bss ": "telecom.bss",
    "business support": "telecom.bss",
    "billing system": "telecom.bss",
    "mediation": "telecom.bss",

    # Carrier-Grade Systems
    "carrier grade": "telecom.carrier",
    "carrier network": "telecom.carrier",
    "metro ethernet": "telecom.carrier",
    "dwdm": "telecom.carrier",
    "optical network": "telecom.carrier",
    "fiber optic": "telecom.carrier",

    # 5G & Mobile Networks
    "5g ": "telecom.5g",
    "5g network": "telecom.5g",
    "5g core": "telecom.5g",
    "ran ": "telecom.5g",
    "radio access network": "telecom.5g",
    "lte ": "telecom.mobile",
    "4g ": "telecom.mobile",
    "mobile network": "telecom.mobile",
}
