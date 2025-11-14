"""
AI-Routed Master Agent
Handles EC2, S3, and KMS agents with conversational input.
No forced linear LangGraph chain.
"""
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).parent / "config" / "settings.env"
load_dotenv(dotenv_path=env_path)

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from utils.logger import get_logger
from utils.memory import AgentMemory
from agents.ec2_agent import EC2Agent
from agents.s3_agent import S3Agent
from agents.kms_agent import KMSAgent
from dotenv import load_dotenv
import json, os

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")


class MasterAgent:

    def __init__(self, use_ai=True):
        self.use_ai = use_ai
        self.llm = ChatOpenAI(model="gpt-4o-mini", api_key=openai_api_key)
        self.logger = get_logger("MasterAgent")

        self.agent_memory = AgentMemory()

        # Sub-agents
        self.ec2_agent = EC2Agent()
        self.s3_agent = S3Agent()
        self.kms_agent = KMSAgent()

    # -----------------------------------------------------
    # 1️⃣ AI-based Router
    # -----------------------------------------------------
    def decide_agents(self, prompt: str):
        """
        Robust AI router with JSON validation + retry fallback.
        """

        decision_prompt = f"""
        You are an AWS Audit Router.
        Decide which agents should run based on this user request:

        "{prompt}"

        Agents:
        - EC2
        - S3
        - KMS

        IMPORTANT RULES:
        - Output ONLY valid JSON.
        - DO NOT add explanations outside the JSON.
        - DO NOT add comments.
        - DO NOT add markdown.
        - DO NOT say "Here is the JSON".
        - JUST return pure JSON.

        JSON FORMAT (strict):
        {{
            "run_ec2": true/false,
            "run_s3": true/false,
            "run_kms": true/false,
            "reason": "short reason"
        }}
        """

        response = self.llm.invoke(decision_prompt)
        text = response.content.strip()

        # 1️⃣ First attempt to parse JSON
        try:
            return json.loads(text)
        except Exception:
            self.logger.error(f"Router returned invalid JSON:\n{text}")

        # 2️⃣ Fallback: ask the LLM to convert into JSON
        fix_prompt = f"""
        Convert the following text to strict JSON only.
        Do NOT add any extra text.

        Input:
        {text}
        """
        fixed = self.llm.invoke(fix_prompt).content.strip()

        try:
            return json.loads(fixed)
        except Exception as e:
            self.logger.error("Router failed second JSON fix as well!")
            self.logger.error(f"Invalid JSON: {fixed}")

        # 3️⃣ Final fallback: safe defaults
        return {
            "run_ec2": True,
            "run_s3": True,
            "run_kms": True,
            "reason": "Fallback: failed to parse JSON"
        }


    # -----------------------------------------------------
    # 2️⃣ Main Run Method – AI Decides Actions
    # -----------------------------------------------------
    def run(self, prompt: str):
        self.logger.info(f"🧠 MasterAgent Prompt Received: {prompt}")

        # Save chat message
        self.agent_memory.save_message("user", prompt)

        # If AI enabled → ask router
        if self.use_ai:
            decision = self.decide_agents(prompt)
            self.logger.info(f"🤖 Router decision: {decision}")
        else:
            decision = {"run_ec2": True, "run_s3": True, "run_kms": True}

        results = {}

        # Execute selected agents
        if decision["run_ec2"]:
            results["EC2"] = self.ec2_agent.run()

        if decision["run_s3"]:
            results["S3"] = self.s3_agent.run()

        if decision["run_kms"]:
            results["KMS"] = self.kms_agent.run()

        # Prepare summary
        summary_prompt = ChatPromptTemplate.from_template("""
        Summarize the AWS audit results clearly and simply:

        {results}
        """)
        formatted = summary_prompt.format(results=results)
        summary = self.llm.invoke(formatted).content

        # Save to conversation memory & persistent memory
        self.agent_memory.save_message("assistant", summary)
        self.agent_memory.save_run("MasterAgent", summary)

        return summary

    # -----------------------------------------------------
    # 3️⃣ Chat interface (for /chat endpoint)
    # -----------------------------------------------------
    def chat(self, message: str):
        self.agent_memory.save_message("user", message)

        history = self.agent_memory.get_history_as_text()
        prompt = f"{history}\nUser: {message}\nAssistant: "

        response = self.llm.invoke(prompt).content
        self.agent_memory.save_message("assistant", response)

        return response
    # -----------------------------------------------------
    # Debug Router
    # -----------------------------------------------------
    def debug_router(self, prompt: str):
        """Return only the router JSON output without executing agents."""
        decision = self.decide_agents(prompt)
        return {
            "prompt": prompt,
            "router_decision": decision
        }
# ============================================================