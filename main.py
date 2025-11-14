"""
app.py — FastAPI Entrypoint
Runs:
- Individual agent audit endpoints (EC2, S3, KMS)
- Master AI or LangGraph orchestration
- New READ-ONLY state endpoints
"""

from dotenv import load_dotenv
from pathlib import Path

# Load environment variables early
env_path = Path(__file__).parent / "config" / "settings.env"
load_dotenv(dotenv_path=env_path)

from fastapi import FastAPI, Query
import uvicorn
from pydantic import BaseModel

from agents.master_agent import MasterAgent
from agents.ec2_agent import EC2Agent
from agents.s3_agent import S3Agent
from agents.kms_agent import KMSAgent

# Read-only helpers (NO auto-remediation)
from utils.aws_helpers import (
    get_all_instances,
    get_average_cpu_utilization,
    get_s3_buckets,
    check_s3_versioning,
    check_s3_encryption,
    is_public_access_enabled,
    get_kms_keys,
    check_key_rotation
)

app = FastAPI(title="AWS Multi-Agent System", version="2.0")


# --------------------------------------------------------
#  MASTER AGENT /chat
# --------------------------------------------------------
@app.get("/chat")
def run_master_audit(
    prompt: str = Query("Audit my AWS resources"),
    use_ai: bool = Query(True)
):
    master = MasterAgent(use_ai=use_ai)
    result = master.run(prompt)
    return {"status": "success", "summary": result}


# --------------------------------------------------------
#  INDIVIDUAL AGENT AUDIT (with fixes)
# --------------------------------------------------------
@app.get("/ec2")
def run_ec2_audit():
    return {"service": "EC2", "result": EC2Agent().run()}


@app.get("/s3")
def run_s3_audit():
    return {"service": "S3", "result": S3Agent().run()}


@app.get("/kms")
def run_kms_audit():
    return {"service": "KMS", "result": KMSAgent().run()}


# --------------------------------------------------------
#  READ-ONLY STATE ENDPOINTS (NO FIXES)
# --------------------------------------------------------

@app.get("/ec2/state")
def ec2_state():
    """Read-only: show current EC2 CPU avg + instance list."""
    instances = get_all_instances()
    state = []

    for inst in instances:
        avg_cpu = get_average_cpu_utilization(inst["InstanceId"], hours=48)
        state.append({
            "instance_id": inst["InstanceId"],
            "name": inst["Name"],
            "cpu_48h_avg": avg_cpu
        })

    return {"service": "EC2", "state": state}


@app.get("/s3/state")
def s3_state():
    """Read-only: show versioning + encryption + public access."""
    buckets = get_s3_buckets()
    state = []

    for b in buckets:
        state.append({
            "bucket": b,
            "versioning": check_s3_versioning(b),
            "encryption": check_s3_encryption(b),
            "public_access": is_public_access_enabled(b)
        })

    return {"service": "S3", "state": state}


@app.get("/kms/state")
def kms_state():
    """Read-only: show KMS rotation statuses."""
    keys = get_kms_keys()
    state = []

    for key_id in keys:
        state.append({
            "key_id": key_id,
            "rotation_enabled": check_key_rotation(key_id)
        })

    return {"service": "KMS", "state": state}


# --------------------------------------------------------
#  ROUTER DEBUG ENDPOINT
# --------------------------------------------------------
class RouterRequest(BaseModel):
    prompt: str

master = MasterAgent()

@app.post("/router/debug")
def router_debug(req: RouterRequest):
    return master.debug_router(req.prompt)


# --------------------------------------------------------
#  MEMORY ENDPOINT
# --------------------------------------------------------
@app.get("/memory")
def memory_dump():
    return master.agent_memory.read_memory()


# --------------------------------------------------------
#  Server Entry Point
# --------------------------------------------------------
if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=3000, reload=True)
