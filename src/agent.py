from dotenv import load_dotenv
from pathlib import Path
from src.rule import RuleGenerator, model, client
from src.tool import query_splunk, grammar_check
from typing import List, Dict
import pandas as pd
import openai
import os
import json
import re
import logging
import time

PROJECT_ROOT = Path(__file__).resolve().parent.parent
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.StreamHandler()
                    ])
load_dotenv()


def _call_openai_api(messages: list, response_format: str = "text", function_call: bool = False,
                     max_retries=5, delay=2) -> str:
    retries = 0
    while retries < max_retries:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                response_format={"type": response_format},

            )
            return response.choices[0].message.content
        except Exception as e:
            retries += 1
            print(f"Attempt {retries} failed with error: {e}")
            time.sleep(delay)
    raise Exception(f"All {max_retries} attempts failed.")


class SecurityRuleAgent:
    def __init__(self, model_name="gpt-3.5-turbo"):
        self.model_name = model_name
        self.dsl_fragments = None
        self.rule_raw = None
        self.final_rule = None

    def optimize_rule(self, rule: str, reflection_scores: Dict[str, float], description) -> str:
        """
        """
        low_score_dimensions = []
        for dim in ["logical_coherence", "syntax_validation", "execution_feasibility"]:
            if reflection_scores.get(dim, 1.0) < 0.6:
                low_score_dimensions.append(dim)

        if not low_score_dimensions:
            return rule

        improved_rule = rule
        for dim in low_score_dimensions:
            if dim == "syntax_validation":
                syntax_feedback = grammar_check(improved_rule)
                from src.prompt import RULE_OPTIMIZE_PROMPT
                user_prompt = f'''
                The following is the rule to be optimized:
                {rule}
                The following is the description of the rule:
                {description}
                The following is the feedback from the syntax validation tool:
                {syntax_feedback}
                '''
                messages = [{"role": "system", "content": RULE_OPTIMIZE_PROMPT}, {"role": "user", "content": user_prompt}]
                improved_rule = _call_openai_api(messages)
            elif dim == "execution_feasibility":
                exec_feedback = query_splunk(improved_rule)
                from src.prompt import RULE_OPTIMIZE_PROMPT
                user_prompt = f'''
                The following is the rule to be optimized:
                {rule}
                The following is the description of the rule:
                {description}
                The following is the feedback from the execution feasibility tool (Splunk API):
                {exec_feedback}
                '''
                messages = [{"role": "system", "content": RULE_OPTIMIZE_PROMPT}, {"role": "user", "content": user_prompt}]
                improved_rule = _call_openai_api(messages)
            elif dim == "logical_coherence":
                from src.prompt import RULE_OPTIMIZE_PROMPT
                dsl = RuleGenerator.generate_dsl_rule(description, rule_type='splunk', stream=False)
                dsl = next(dsl)
                user_prompt = f'''
                                The following is the rule to be optimized:
                                {rule}
                                The following is the description of the rule:
                                {description}
                                The following is the feedback from the execution feasibility tool (Splunk API):
                                {dsl}
                                '''
                messages = [{"role": "system", "content": RULE_OPTIMIZE_PROMPT},
                            {"role": "user", "content": user_prompt}]
                refined_text = _call_openai_api(messages)
                improved_rule = refined_text.strip()

        return improved_rule

    def run_agent(self, description: str, max_iterations: int = 3, rule_type: str = 'splunk',
                  required_fields: str = None, log_demo: str = None) -> str:

        logging.info("=== [1] Analyse Phase ===")
        dsl_rule = RuleGenerator.generate_dsl_rule(description, rule_type, required_fields, log_demo, stream=False)
        dsl_rule = next(dsl_rule)
        self.dsl_fragments = dsl_rule

        logging.info("\n=== [2] Generation Phase ===")
        self.rule_raw = RuleGenerator.generate_rule_from_dsl(description, self.dsl_fragments, rule_type,
                                                             required_fields)
        logging.info(f"Initial rule (R_raw):\n{self.rule_raw}")

        current_rule = self.rule_raw
        for iteration in range(max_iterations):
            logging.info(f"\n=== [3] Reflection Iteration {iteration + 1} ===")
            scores = self.reflect_and_score_rule(current_rule, description)
            logging.info(f"Scores => {scores}")

            if all(scores.get(dim, 0.0) >= 0.6 for dim in
                   ["logical_coherence", "syntax_validation", "execution_feasibility"]):
                logging.info("All scores are acceptable. Rule is considered final.")
                self.final_rule = current_rule
                break
            else:
                logging.info("Scores below threshold, optimizing rule...")
                current_rule = self.optimize_rule(current_rule, scores, description)
        else:
            logging.warning("Max iterations reached, output the last version as final.")
            self.final_rule = current_rule

        logging.info("\n=== Final Rule Output ===")
        logging.info(self.final_rule)
        return self.final_rule

    def reflect_and_score_rule(self, rule: str, description: str) -> Dict[str, float]:

        from src.prompt import SCORE_PROMPT
        prompt = SCORE_PROMPT.format(rule=rule, description=description)
        message = [{"role": "system", "content": prompt}]
        reflection_result = _call_openai_api(message, response_format="json")

        import json
        try:
            scores = json.loads(reflection_result)
        except Exception as e:
            scores = {
                "logical_coherence": 1.0,
                "syntax_validation": 1.0,
                "execution_feasibility": 1.0,
                "comment": "Failed to parse reflection result, assume pass."
            }
        return scores
