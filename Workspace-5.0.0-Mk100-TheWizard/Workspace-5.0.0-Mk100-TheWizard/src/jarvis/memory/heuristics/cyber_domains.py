"""Cybersecurity domain mappings.

Covers threat intelligence, network security, identity & access management,
security operations, compliance, vulnerability management, and security tools.
"""

from __future__ import annotations

from typing import Dict

# Keyword-based classification for cybersecurity
CYBER_KEYWORD_MAP: Dict[str, str] = {
    # General Security (existing from old map)
    "cyber security": "cyber.security",
    "cybersecurity": "cyber.security",
    "information security": "cyber.security",
    "infosec": "cyber.security",
    "security policy": "cyber.security",
    "security framework": "cyber.security",

    # Threat Intelligence (existing + expansion)
    "mitre att&ck": "cyber.threat_intel",
    "mitre attack": "cyber.threat_intel",
    "mitre d3fend": "cyber.threat_intel",
    "threat intelligence": "cyber.threat_intel",
    "threat actor": "cyber.threat_intel",
    "apt ": "cyber.threat_intel",
    "advanced persistent threat": "cyber.threat_intel",
    "indicator of compromise": "cyber.threat_intel",
    "ioc ": "cyber.threat_intel",
    "threat hunting": "cyber.threat_intel",

    # STIX/TAXII (from firstResults.md)
    "stix ": "cyber.stix",
    "stix 2": "cyber.stix",
    "stix 2.1": "cyber.stix",
    "structured threat information": "cyber.stix",
    "taxii": "cyber.stix",
    "threat intelligence platform": "cyber.stix",
    "tip ": "cyber.stix",

    # Network Security (existing + expansion)
    "firewall": "cyber.network_security",
    "intrusion detection": "cyber.network_security",
    "intrusion prevention": "cyber.network_security",
    "ids ": "cyber.network_security",
    "ips ": "cyber.network_security",
    "network segmentation": "cyber.network_security",
    "zero trust": "cyber.network_security",
    "network access control": "cyber.network_security",
    "nac ": "cyber.network_security",
    "vpn ": "network.vpn",
    "ipsec": "network.vpn",

    # PKI & Cryptography (from firstResults.md SSL/TLS queries)
    "pki ": "cyber.pki",
    "public key infrastructure": "cyber.pki",
    "certificate authority": "cyber.pki",
    "ca ": "cyber.pki",
    "ssl ": "cyber.pki",
    "tls ": "cyber.pki",
    "x.509": "cyber.pki",
    "certificate": "cyber.pki",
    "encryption": "cyber.pki",
    "cryptography": "cyber.pki",
    "symmetric encryption": "cyber.pki",
    "asymmetric encryption": "cyber.pki",
    "key management": "cyber.pki",

    # Identity & Access Management
    "iam ": "cyber.iam",
    "identity and access": "cyber.iam",
    "identity management": "cyber.iam",
    "access control": "cyber.iam",
    "authentication": "cyber.iam",
    "authorization": "cyber.iam",
    "single sign-on": "cyber.iam",
    "sso ": "cyber.iam",
    "multi-factor authentication": "cyber.iam",
    "mfa ": "cyber.iam",
    "oauth": "cyber.iam",
    "saml": "cyber.iam",
    "ldap": "cyber.iam",
    "active directory": "cyber.iam",

    # SIEM & SOC
    "siem": "cyber.siem",
    "security information and event": "cyber.siem",
    "log management": "cyber.siem",
    "security monitoring": "cyber.siem",
    "splunk": "cyber.siem",
    "elk stack": "cyber.siem",
    "soc ": "cyber.soc",
    "security operations center": "cyber.soc",
    "security analyst": "cyber.soc",
    "security orchestration": "cyber.soc",
    "soar": "cyber.soc",

    # Incident Response & Forensics
    "incident response": "cyber.incident_response",
    "incident handling": "cyber.incident_response",
    "digital forensics": "cyber.incident_response",
    "forensic analysis": "cyber.incident_response",
    "malware analysis": "cyber.incident_response",
    "threat response": "cyber.incident_response",
    "breach investigation": "cyber.incident_response",

    # Vulnerability Management (from Tenable references)
    "vulnerability management": "cyber.vulnerability",
    "vulnerability scan": "cyber.vulnerability",
    "vulnerability assessment": "cyber.vulnerability",
    "penetration test": "cyber.vulnerability",
    "pen test": "cyber.vulnerability",
    "security audit": "cyber.vulnerability",
    "patch management": "cyber.vulnerability",
    "cve ": "cyber.vulnerability",
    "cvss": "cyber.vulnerability",
    "tenable": "cyber.tenable",
    "nessus": "cyber.tenable",
    "tenable.sc": "cyber.tenable",
    "tenable.io": "cyber.tenable",

    # Compliance & Governance
    "security compliance": "cyber.compliance",
    "iso 27001": "cyber.compliance",
    "nist ": "cyber.compliance",
    "nist cybersecurity framework": "cyber.compliance",
    "pci dss": "cyber.compliance",
    "pci-dss": "cyber.compliance",
    "gdpr": "cyber.compliance",
    "hipaa": "cyber.compliance",
    "sox ": "cyber.compliance",
    "sarbanes-oxley": "cyber.compliance",
    "security audit": "cyber.compliance",

    # Cisco Security (from conversation index + firstResults)
    "cisco asa": "cyber.cisco_security",
    "cisco firepower": "cyber.cisco_security",
    "cisco umbrella": "cyber.cisco_security",
    "cisco secure": "cyber.cisco_security",
}
