from utils.aws_helpers import (
    get_s3_buckets,
    check_s3_versioning,
    check_s3_encryption,
    enable_versioning,
    enable_encryption,
    is_public_access_enabled,
    block_public_access
)
from utils.logger import log_action


class S3Agent:
    """
    The S3 agent checks each S3 bucket for:
      1️⃣ Versioning
      2️⃣ Default encryption
      3️⃣ Public access configuration

    It AUTO-FIXES:
      ✔ Enables versioning if disabled
      ✔ Enables encryption if disabled
      ✔ Blocks public access if enabled
    """

    def __init__(self):
        self.findings = []

    def run(self):
        buckets = get_s3_buckets()

        for bucket_name in buckets:
            bucket_result = {
                "bucket": bucket_name,
                "checks": {},
                "actions": []
            }

            # 1️⃣ VERSIONING
            versioning = check_s3_versioning(bucket_name)
            bucket_result["checks"]["versioning"] = versioning

            if not versioning:
                log_action(f"⚠️  Versioning disabled for {bucket_name} — enabling...")
                enable_versioning(bucket_name)
                bucket_result["actions"].append("Enabled versioning")

            # 2️⃣ ENCRYPTION
            encryption = check_s3_encryption(bucket_name)
            bucket_result["checks"]["encryption"] = encryption

            if not encryption:
                log_action(f"⚠️  Encryption disabled for {bucket_name} — enabling AES256...")
                enable_encryption(bucket_name)
                bucket_result["actions"].append("Enabled AES256 encryption")

            # 3️⃣ PUBLIC ACCESS
            public_status = is_public_access_enabled(bucket_name)
            bucket_result["checks"]["public_access"] = public_status

            if public_status:
                log_action(f"🛑 Public access ENABLED for {bucket_name} — blocking...")
                block_public_access(bucket_name)
                bucket_result["actions"].append("Blocked public access")

            self.findings.append(bucket_result)

        log_action("✅ Completed S3 audit.")
        return self.findings
