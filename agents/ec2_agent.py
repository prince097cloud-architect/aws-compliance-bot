from utils.aws_helpers import (
    get_all_instances,
    get_average_cpu_utilization,
    terminate_instance,
)
from utils.logger import get_logger

logger = get_logger("EC2Agent")


class EC2Agent:
    """
    EC2 agent checks for idle EC2 instances:
    - Fetches all running EC2 instances
    - Checks average CPU usage for last 48 hours
    - If CPU < 5%, terminates (or logs in DRY_RUN mode)
    """

    def __init__(self, threshold: float = 5.0):
        self.threshold = threshold

    def run(self):
        results = []
        logger.info("🚀 EC2 Agent started scanning...")
        instances = get_all_instances()

        if not instances:
            logger.info("No running EC2 instances found.")
            return {"ec2": "No running instances found."}

        for inst in instances:
            instance_id = inst["InstanceId"]
            name = inst["Name"]
            avg_cpu = get_average_cpu_utilization(instance_id, hours=48)

            if avg_cpu < self.threshold:
                logger.info(f"🧊 Instance {name} ({instance_id}) idle (CPU {avg_cpu:.2f}%) — terminating.")
                terminate_instance(instance_id)
                results.append({
                    "InstanceId": instance_id,
                    "Name": name,
                    "AvgCPU": avg_cpu,
                    "Action": "Terminated (or DRY_RUN)"
                })
            else:
                logger.info(f"🔥 Instance {name} ({instance_id}) active (CPU {avg_cpu:.2f}%) — skipping.")
                results.append({
                    "InstanceId": instance_id,
                    "Name": name,
                    "AvgCPU": avg_cpu,
                    "Action": "Active"
                })

        return {"ec2": results}
