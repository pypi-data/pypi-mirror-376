# SentinelMFT

AI-powered secure managed file transfer for Google Cloud — with AES-256-GCM encryption, resilient transfers, and anomaly detection.

## Features
- AES-256-GCM encrypt/decrypt files
- Google Cloud Storage uploads/downloads (resumable)
- Isolation Forest anomaly detection on transfer logs
- CLI for transfer, encrypt/decrypt, train/score

## Install
```bash
pip install sentinelmft

# Quick Start

# Encrypt a file
sentinelmft encrypt --keyfile ./aes.key --src input.bin --dst input.bin.enc

# Transfer local→GCS (configure project/bucket in config)
sentinelmft transfer --config ./config.yaml --src ./input.bin.enc --dst gs://my-bucket/secure/input.bin.enc

# Train anomaly model
sentinelmft ai-train --logfile transfers.csv

Config.yml
```
gcs:
  project: my-gcp-project
  bucket: my-bucket
security:
  keyfile: ./aes.key
  allow_ips: ["203.0.113.10"]

