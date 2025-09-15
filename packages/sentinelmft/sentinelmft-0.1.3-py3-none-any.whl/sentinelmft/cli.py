import click, os
from .config import load_config, load_key
from .crypto.aesgcm import encrypt_file, decrypt_file
from .transfer.local import copy_local
from .transfer.gcs import upload_to_gcs, download_from_gcs
from .ai.anomaly import train_anomaly, score_anomaly
from .firewall.policy import ip_allowed
from .logging_utils import log

@click.group()
def app():
    """SentinelMFT CLI — secure MFT with AES-GCM and anomaly detection."""

@app.command()
@click.option("--config", required=True, help="Path to YAML/JSON config")
@click.option("--src", required=True)
@click.option("--dst", required=True)
@click.option("--encrypt", is_flag=True, help="Encrypt src before transfer (local only)")
def transfer(config, src, dst, encrypt):
    cfg = load_config(config)
    if encrypt:
        assert cfg.security.keyfile, "keyfile required in config.security.keyfile"
        key = load_key(cfg.security.keyfile)
        enc_path = src + ".enc"
        encrypt_file(src, enc_path, key)
        src = enc_path
        log("encrypted_source_ready", path=src)

    if dst.startswith("gs://"):
        _, bucket, *rest = dst.replace("gs://","").split("/", 1) + [""]
        dest_blob = rest[0]
        upload_to_gcs(src, bucket, dest_blob, cfg.gcs.project)
    elif src.startswith("gs://"):
        _, bucket, *rest = src.replace("gs://","").split("/", 1) + [""]
        blob = rest[0]
        download_from_gcs(bucket, blob, dst, cfg.gcs.project)
    else:
        copy_local(src, dst)

@app.command("encrypt")
@click.option("--keyfile", required=True)
@click.option("--src", required=True)
@click.option("--dst", required=True)
def do_encrypt(keyfile, src, dst):
    key = load_key(keyfile)
    encrypt_file(src, dst, key)
    log("encrypt_done", src=src, dst=dst)

@app.command("decrypt")
@click.option("--keyfile", required=True)
@click.option("--src", required=True)
@click.option("--dst", required=True)
def do_decrypt(keyfile, src, dst):
    key = load_key(keyfile)
    decrypt_file(src, dst, key)
    log("decrypt_done", src=src, dst=dst)

@app.command("ai-train")
@click.option("--logfile", required=True, help="CSV with file_size_mb, transfer_time_sec")
@click.option("--model-out", default="anomaly_if.joblib")
def ai_train(logfile, model_out):
    out = train_anomaly(logfile, model_out)
    log("ai_train_done", model=out)

@app.command("ai-score")
@click.option("--logfile", required=True)
@click.option("--model", default="anomaly_if.joblib")
@click.option("--out", default="scores.csv")
def ai_score(logfile, model, out):
    df = score_anomaly(logfile, model)
    df.to_csv(out, index=False)
    log("ai_score_done", output=out, anomalies=int(df["is_anomaly"].sum()))

@app.command("firewall-check")
@click.option("--ip", required=True)
@click.option("--config", required=True)
def fw_check(ip, config):
    cfg = load_config(config)
    allowed = ip_allowed(ip, cfg.security.allow_ips)
    log("firewall_check", ip=ip, allowed=allowed)
    click.echo("ALLOW" if allowed else "BLOCK")
