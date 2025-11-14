import os
import boto3
from datetime import datetime, timedelta
from botocore.exceptions import ClientError
from utils.logger import get_logger
from botocore.exceptions import BotoCoreError, ClientError
from dotenv import load_dotenv
load_dotenv()

logger = get_logger("AWSHelpers")

# Global DRY_RUN mode (read from environment)
DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"
REGION = os.getenv("AWS_REGION", "ap-south-1")

# Initialize AWS clients
ec2 = boto3.client("ec2", region_name=REGION)
cw = boto3.client("cloudwatch", region_name=REGION)
s3 = boto3.client("s3", region_name=REGION)
kms = boto3.client("kms", region_name=REGION)


# ============================================================
# EC2 Helper Functions
# ============================================================

def get_all_instances():
    """Return list of running EC2 instances (ID + Name tag)."""
    instances = []
    try:
        resp = ec2.describe_instances(Filters=[{"Name": "instance-state-name", "Values": ["running"]}])
        for reservation in resp["Reservations"]:
            for instance in reservation["Instances"]:
                name = next((t["Value"] for t in instance.get("Tags", []) if t["Key"] == "Name"), "Unnamed")
                instances.append({"InstanceId": instance["InstanceId"], "Name": name})
    except ClientError as e:
        logger.error(f"Error fetching EC2 instances: {e}")
    return instances


def get_average_cpu_utilization(instance_id: str, hours: int = 48) -> float:
    """Fetch average CPU utilization over the past `hours` from CloudWatch."""
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=hours)
    try:
        metrics = cw.get_metric_statistics(
            Namespace="AWS/EC2",
            MetricName="CPUUtilization",
            Dimensions=[{"Name": "InstanceId", "Value": instance_id}],
            StartTime=start_time,
            EndTime=end_time,
            Period=3600,
            Statistics=["Average"]
        )
        datapoints = metrics.get("Datapoints", [])
        if not datapoints:
            return 0.0
        avg_cpu = sum(d["Average"] for d in datapoints) / len(datapoints)
        return avg_cpu
    except ClientError as e:
        logger.error(f"Error fetching CPU for {instance_id}: {e}")
        return 0.0


def terminate_instance(instance_id: str):
    """Terminate an instance if DRY_RUN=False."""
    if DRY_RUN:
        logger.info(f"[DRY_RUN] Would terminate instance {instance_id}")
        return
    try:
        ec2.terminate_instances(InstanceIds=[instance_id])
        logger.info(f"Instance {instance_id} terminated successfully.")
    except ClientError as e:
        logger.error(f"Error terminating {instance_id}: {e}")


# ============================================================
# S3 Helper Functions
# ============================================================
def get_s3_buckets(profile: str = None, region: str = None) -> list:
    """
    Return a list of S3 bucket names. Optional profile and region arguments
    allow running under a specific AWS profile or region.
    """
    try:
        session = boto3.Session(profile_name=profile) if profile else boto3.Session()
        s3 = session.client("s3", region_name=region)
        resp = s3.list_buckets()
        buckets = [b["Name"] for b in resp.get("Buckets", [])]
        return buckets
    except (BotoCoreError, ClientError) as e:
        logger.error(f"get_s3_buckets: failed to list buckets: {e}")
        return []
    
def list_buckets():
    """List all S3 buckets."""
    try:
        resp = s3.list_buckets()
        return [b["Name"] for b in resp["Buckets"]]
    except ClientError as e:
        logger.error(f"Error listing S3 buckets: {e}")
        return []


def check_s3_versioning(bucket: str) -> bool:
    """Return True if versioning is enabled."""
    try:
        resp = s3.get_bucket_versioning(Bucket=bucket)
        return resp.get("Status") == "Enabled"
    except ClientError as e:
        logger.error(f"Error checking versioning for {bucket}: {e}")
        return False


def enable_versioning(bucket: str):
    """Enable versioning if DRY_RUN=False."""
    if DRY_RUN:
        logger.info(f"[DRY_RUN] Would enable versioning on {bucket}")
        return
    try:
        s3.put_bucket_versioning(Bucket=bucket, VersioningConfiguration={"Status": "Enabled"})
        logger.info(f"Enabled versioning for {bucket}")
    except ClientError as e:
        logger.error(f"Error enabling versioning for {bucket}: {e}")


def check_s3_encryption(bucket: str) -> bool:
    """Return True if default encryption is enabled."""
    try:
        s3.get_bucket_encryption(Bucket=bucket)
        return True
    except ClientError as e:
        if "ServerSideEncryptionConfigurationNotFoundError" in str(e):
            return False
        logger.error(f"Error checking encryption for {bucket}: {e}")
        return False


def enable_encryption(bucket: str):
    """Enable AES256 encryption if DRY_RUN=False."""
    if DRY_RUN:
        logger.info(f"[DRY_RUN] Would enable encryption on {bucket}")
        return
    try:
        s3.put_bucket_encryption(
            Bucket=bucket,
            ServerSideEncryptionConfiguration={
                "Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}]
            }
        )
        logger.info(f"Enabled AES256 encryption for {bucket}")
    except ClientError as e:
        logger.error(f"Error enabling encryption for {bucket}: {e}")

def is_public_access_enabled(bucket: str) -> bool:
    """Check if public access is currently allowed for a bucket."""
    try:
        resp = s3.get_public_access_block(Bucket=bucket)
        config = resp["PublicAccessBlockConfiguration"]
        # If any flag is False, public access might be open
        if not all(config.values()):
            return True
        return False
    except ClientError as e:
        if "NoSuchPublicAccessBlockConfiguration" in str(e):
            return True  # No configuration = public access allowed
        logger.error(f"Error checking public access for {bucket}: {e}")
        return True

def block_public_access(bucket: str):
    """Check if public access is enabled; if yes, block it."""
    try:
        if not is_public_access_enabled(bucket):
            logger.info(f"{bucket} already has public access blocked.")
            return

        if DRY_RUN:
            logger.info(f"[DRY_RUN] Would block public access for {bucket}")
            return

        s3.put_public_access_block(
            Bucket=bucket,
            PublicAccessBlockConfiguration={
                "BlockPublicAcls": True,
                "IgnorePublicAcls": True,
                "BlockPublicPolicy": True,
                "RestrictPublicBuckets": True,
            },
        )
        logger.info(f"✅ Blocked public access for {bucket}")
    except ClientError as e:
        logger.error(f"Error blocking public access for {bucket}: {e}")


# ============================================================
# KMS Helper Functions
# ============================================================

def get_kms_keys():
    """List all KMS key IDs."""
    try:
        keys = kms.list_keys()["Keys"]
        return [k["KeyId"] for k in keys]
    except ClientError as e:
        logger.error(f"Error listing KMS keys: {e}")
        return []


def check_key_rotation(key_id: str) -> bool:
    """Return True if key rotation is enabled."""
    try:
        resp = kms.get_key_rotation_status(KeyId=key_id)
        return resp["KeyRotationEnabled"]
    except ClientError as e:
        logger.error(f"Error checking rotation for {key_id}: {e}")
        return False


def enable_key_rotation(key_id: str):
    """Enable rotation if DRY_RUN=False."""
    if DRY_RUN:
        logger.info(f"[DRY_RUN] Would enable rotation for {key_id}")
        return
    try:
        kms.enable_key_rotation(KeyId=key_id)
        logger.info(f"Rotation enabled for KMS key {key_id}")
    except ClientError as e:
        logger.error(f"Error enabling rotation for {key_id}: {e}")
