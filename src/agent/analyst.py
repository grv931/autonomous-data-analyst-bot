import re
import json
import time
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from config import settings
from src.agent.models import llm_client
from src.agent.prompts import SYSTEM_DATA_ANALYST_PROMPT, CODE_GENERATION_PROMPT
from src.engine.dataset import dataset_manager
from src.engine.sandbox import sandbox, ExecutionResult
from src.storage.logger import audit_logger

@dataclass
class AgentResponse:
    text: str
    chart_bytes: Optional[bytes] = None
    chart_path: Optional[str] = None
    is_json: bool = False
    code_executed: Optional[str] = None
    duration_ms: float = 0.0

class DataAnalystAgent:
    """
    Autonomous Data Analyst Agent with ReAct reasoning, code execution,
    self-healing error recovery, and dual-mode JSON/Conversational response support.
    """
    def __init__(self):
        self.conversations: Dict[int | str, List[Dict[str, str]]] = {}

    def is_strict_json_request(self, text: str) -> bool:
        """Detect whether the incoming query is from an automated grader demanding strict JSON."""
        lower = text.lower()
        patterns = [
            r'reply with (?:only|just) this json',
            r'exact json object',
            r'\{\s*"answer"',
            r'reply with exactly one json',
            r'json object and absolutely nothing else',
            r'"log_url"',
        ]
        return any(re.search(p, lower) for p in patterns)

    def extract_code_block(self, text: str) -> Optional[str]:
        """Extract Python code block from LLM markdown response."""
        match = re.search(r'```(?:python)?\s*([\s\S]*?)```', text)
        if match:
            return match.group(1).strip()
        return None

    def clean_json_output(self, raw_text: str, default_log_url: str) -> str:
        """Ensure the response is strictly valid JSON with correct log_url."""
        text = raw_text.strip()
        # Remove markdown fences if model added them
        if text.startswith("```"):
            text = re.sub(r'^```(?:json)?\s*', '', text)
            text = re.sub(r'\s*```$', '', text)
            text = text.strip()

        # Find outer braces if surrounded by prose
        if not (text.startswith("{") and text.endswith("}")):
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1:
                text = text[start : end + 1]

        try:
            parsed = json.loads(text)
        except Exception:
            # Fallback wrapper
            parsed = {"answer": raw_text.strip()}

        # Ensure log_url is attached properly
        parsed["log_url"] = default_log_url
        return json.dumps(parsed, ensure_ascii=False)

    async def handle_query(self, chat_id: int | str, user_text: str) -> AgentResponse:
        start_time = time.time()
        is_json_mode = self.is_strict_json_request(user_text)
        default_log_url = f"{settings.public_base_url.rstrip('/')}/run.jsonl"

        # Manage multi-turn history
        history = self.conversations.setdefault(chat_id, [])
        history.append({"role": "user", "content": user_text})
        if len(history) > settings.max_history_turns * 2:
            history = history[-settings.max_history_turns * 2 :]
            self.conversations[chat_id] = history

        active_df = dataset_manager.get_dataset(chat_id)
        dataset_summary = dataset_manager.get_summary_text(chat_id)

        code_executed: Optional[str] = None
        chart_bytes: Optional[bytes] = None
        chart_path: Optional[str] = None
        final_answer: str = ""
        error_msg: Optional[str] = None

        try:
            # Check if user needs data computation or plot on uploaded dataset
            needs_code = active_df is not None or any(kw in user_text.lower() for kw in ["plot", "chart", "graph", "histogram", "calculate", "sum", "mean", "correlation", "regression"])

            if needs_code and active_df is not None:
                # 1. Ask LLM to generate Python execution code
                code_prompt = CODE_GENERATION_PROMPT.format(
                    dataset_summary=dataset_summary,
                    user_query=user_text,
                )
                raw_code_resp = llm_client.chat_completion(
                    messages=[
                        {"role": "system", "content": "You are a professional Python data science code generator."},
                        {"role": "user", "content": code_prompt},
                    ],
                    temperature=0.0,
                )
                code_to_run = self.extract_code_block(raw_code_resp) or raw_code_resp
                code_executed = code_to_run

                # 2. Execute in sandbox
                exec_res: ExecutionResult = sandbox.execute(code_to_run, chat_id=chat_id, df=active_df)

                # Self-healing retry if code crashed
                if not exec_res.success:
                    retry_prompt = (
                        f"The generated code encountered an error:\n{exec_res.error}\n\n"
                        f"Original Code:\n```python\n{code_to_run}\n```\n\n"
                        f"Please fix the code to accomplish the user request without errors."
                    )
                    fix_resp = llm_client.chat_completion(
                        messages=[
                            {"role": "system", "content": "Fix the Python code based on the runtime error."},
                            {"role": "user", "content": retry_prompt},
                        ],
                        temperature=0.0,
                    )
                    fixed_code = self.extract_code_block(fix_resp) or fix_resp
                    code_executed = fixed_code
                    exec_res = sandbox.execute(fixed_code, chat_id=chat_id, df=active_df)

                chart_bytes = exec_res.chart_bytes
                chart_path = exec_res.chart_path

                # 3. Formulate final response with the execution context
                system_instruction = SYSTEM_DATA_ANALYST_PROMPT
                exec_context = (
                    f"\n\n[EXECUTION CONTEXT]\n"
                    f"Code Executed:\n{code_executed}\n"
                    f"Standard Output:\n{exec_res.stdout}\n"
                    f"Result Variable:\n{exec_res.output_value}\n"
                    f"Chart Generated: {chart_bytes is not None}"
                )

                messages = [
                    {"role": "system", "content": system_instruction},
                ] + history[:-1] + [
                    {"role": "user", "content": user_text + exec_context}
                ]

                raw_final = llm_client.chat_completion(messages=messages, temperature=0.1)

            else:
                # Direct conversational or evaluation response
                messages = [
                    {"role": "system", "content": SYSTEM_DATA_ANALYST_PROMPT},
                ] + history

                raw_final = llm_client.chat_completion(messages=messages, temperature=0.1)

            # Format response
            if is_json_mode:
                final_answer = self.clean_json_output(raw_final, default_log_url)
            else:
                final_answer = raw_final

        except Exception as e:
            error_msg = str(e)
            if is_json_mode:
                final_answer = json.dumps({"answer": f"Error: {error_msg}", "log_url": default_log_url})
            else:
                final_answer = f"⚠️ **Analysis Error**: {error_msg}\n\nPlease verify your query or API configuration."

        duration_ms = (time.time() - start_time) * 1000
        history.append({"role": "assistant", "content": final_answer})

        # Log to run.jsonl
        audit_logger.log(
            event_type="interaction",
            chat_id=chat_id,
            user_message=user_text,
            answer=final_answer,
            code_executed=code_executed,
            duration_ms=duration_ms,
            has_chart=chart_bytes is not None,
            error=error_msg,
            metadata={"is_json_mode": is_json_mode},
        )

        return AgentResponse(
            text=final_answer,
            chart_bytes=chart_bytes,
            chart_path=chart_path,
            is_json=is_json_mode,
            code_executed=code_executed,
            duration_ms=duration_ms,
        )

analyst_agent = DataAnalystAgent()
