from utils.aws_helpers import (
    get_kms_keys,
    check_key_rotation,
    enable_key_rotation,
)
from utils.logger import log_action


class KMSAgent:
    """
    The KMS agent checks every customer-managed key to ensure:
      1️⃣ Key rotation is enabled.
    If disabled, it automatically enables it.
    """

    def __init__(self):
        self.findings = []

    def run(self):
        keys = get_kms_keys()   # returns: ["key-id-1", "key-id-2"]

        for key_id in keys:
            key_result = {
                "key_id": key_id,
                "rotation_enabled": None,
                "actions": []
            }

            rotation_status = check_key_rotation(key_id)
            key_result["rotation_enabled"] = rotation_status

            if not rotation_status:
                log_action(f"🔄 Enabling key rotation for key {key_id}")
                enable_key_rotation(key_id)
                key_result["actions"].append("Enabled key rotation")

            self.findings.append(key_result)

        log_action("✅ Completed KMS audit.")
        return self.findings
