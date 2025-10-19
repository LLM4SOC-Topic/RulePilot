from abc import ABC, abstractmethod
from dotenv import load_dotenv
from pathlib import Path
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

client = openai.OpenAI(api_key=os.environ['OPENAI_API_KEY'])
model = os.environ['OPENAI_MODEL_NAME']


def switch_llm_provider(provider="openai"):

    global client, model

    providers = {
        "openai": {
            "api_key": os.getenv("OPENAI_API_KEY"),
            "base_url": os.getenv("OPENAI_BASE_URL"),
            "model": os.getenv("OPENAI_MODEL_NAME")
        },
        "deepseek": {
            "api_key": os.getenv("DEEPSEEK_API_KEY"),
            "base_url": os.getenv("DEEPSEEK_BASE_URL"),
            "model": os.getenv("DEEPSEEK_MODEL_NAME")
        },
        "llama": {
            "api_key": os.getenv("LLAMA_API_KEY"),
            "base_url": os.getenv("LLAMA_BASE_URL"),
            "model": os.getenv("LLAMA_MODEL_NAME")
        }
    }

    if provider not in providers:
        raise ValueError(f"Unknown provider: {provider}")

    config = providers[provider]

    client = openai.OpenAI(api_key=config["api_key"], base_url=config["base_url"])
    model = config["model"]
    logging.info(f"Switched to {provider} provider.")


switch_llm_provider("openai")

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler(os.path.join(PROJECT_ROOT, "output.log")),
                        logging.StreamHandler()
                    ])


class Rule(ABC):
    def __init__(self, rule_type: str, rule_content: str):
        self.rule_type = rule_type
        self.rule_content = rule_content

    @abstractmethod
    def preprocess(self):
        pass

    @classmethod
    @abstractmethod
    def from_convert_result(cls, *args, **kwargs):
        pass

    def __str__(self):
        return f"Rule Type: {self.rule_type}\nRule Content: {self.rule_content}"


class SplunkRule(Rule):
    def __init__(self, rule_content: str):
        super().__init__('splunk', rule_content)
        self.pipes = []
        self.preprocess()

    def preprocess(self):
        self.pipes = []
        pipes = self.rule_content.split("|")
        for pipe in pipes:
            pipe_info = extract_info_from_pipe(pipe)
            pipe_info['pipe'] = pipe
            self.pipes.append(pipe_info)

    def show_pipes(self):
        preprocessed_data = self.pipes
        if isinstance(preprocessed_data, list) and all(isinstance(i, dict) for i in preprocessed_data):
            df = pd.DataFrame(preprocessed_data)
            print("Preprocessed Data Table:")
            print(df.to_string(index=False))
        else:
            print("Preprocessed data is not in the expected format: list of dictionaries")

    @classmethod
    def from_convert_result(cls, pipes: list) -> Rule:
        rule_content = " | ".join([pipe for pipe in pipes])
        return cls(rule_content=rule_content)


class SentinelRule(Rule):
    def __init__(self, rule_content: str):
        super().__init__('Sentinel', rule_content)
        self.pipes = []
        self.preprocess()

    def preprocess(self):
        self.pipes = []
        pipes = self.rule_content.split("|")
        for pipe in pipes:
            pipe_info = extract_info_from_pipe(pipe)
            pipe_info['pipe'] = pipe
            self.pipes.append(pipe_info)

    @classmethod
    def from_convert_result(cls, pipes: list) -> Rule:
        rule_content = " | ".join([pipe for pipe in pipes])
        return cls(rule_content=rule_content)


class RuleConverter:
    RULE_CLASSES = {
        "splunk": SplunkRule,
        "sentinel": SentinelRule
    }

    @classmethod
    def convert_rule(cls, input_rule: Rule, target_rule_type: str) -> Rule:
        target_rule_type = target_rule_type.lower()
        if target_rule_type not in cls.RULE_CLASSES:
            raise ValueError(f"Rule type {target_rule_type} is not supported.")
        target_rule_class = cls.RULE_CLASSES[target_rule_type]
        target_rule_pipes = []
        from src.prompt import RULE_CONVERSION_PROMPT
        sys_prompt = RULE_CONVERSION_PROMPT.format(target_rule_type=target_rule_type)
        if isinstance(input_rule, SplunkRule):
            messages = [{"role": "system", "content": sys_prompt}]
            for pipe in input_rule.pipes:
                user_prompt = f'''
                The following is a part of a Splunk rule:
                {pipe['pipe']}
                The operation type is {pipe['operation_type']}
                '''  # todo: add input and output fields
                messages.append({"role": "user", "content": user_prompt})
                response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    response_format={"type": "json_object"}
                )
                converted_rule = response.choices[0].message.content
                target_rule_pipes.append(json.loads(converted_rule)['result'])
                messages.append({"role": "assistant", "content": converted_rule})
        elif isinstance(input_rule, SentinelRule):
            messages = [{"role": "system", "content": sys_prompt}]
            for pipe in input_rule.pipes:
                user_prompt = f'''
                            The following is a part of a Microsoft Sentinel rule:
                            {pipe['pipe']}
                            The operation type is {pipe['operation_type']}
                            '''  # todo: add input and output fields
                messages.append({"role": "user", "content": user_prompt})
                response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    response_format={"type": "json_object"}
                )
                converted_rule = response.choices[0].message.content
                target_rule_pipes.append(json.loads(converted_rule)['result'])
                messages.append({"role": "assistant", "content": converted_rule})
        return target_rule_class.from_convert_result(target_rule_pipes)


def extract_info_from_pipe(pipe_str: str) -> dict:
    from src.prompt import PREPROCESSING_PROMPT
    sys_prompt = PREPROCESSING_PROMPT
    user_prompt = f'''
    The following is a part of a Splunk rule:
    {pipe_str}
    '''
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content)


def safe_chat_completion(messages, max_retries=5, delay=2):
    retries = 0
    while retries < max_retries:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
            )
            return response
        except Exception as e:
            retries += 1
            print(f"Attempt {retries} failed with error: {e}")
            time.sleep(delay)
    raise Exception(f"All {max_retries} attempts failed.")


class RuleGenerator:
    @classmethod
    def web_rule_generator(cls, description: str, rule_type: str, required_fields: str = None,
                           log_demo: str = None):
        dsl_rule_collected = ""
        for step, result in cls.generate_dsl_rule(description, rule_type, required_fields, log_demo, stream=True):
            yield step, result
            if step == "FINAL_RESULT":
                dsl_rule_collected = result

        final_rule = cls.generate_rule_from_dsl(description, dsl_rule_collected, rule_type)
        yield "FINAL_RULE", final_rule

    @classmethod
    def generate_rule(cls, description: str, rule_type: str, required_fields: str = None,
                      log_demo: str = None):
        logging.info("Generating DSL rule...")
        dsl_rule = cls.generate_dsl_rule(description, rule_type, required_fields, log_demo, stream=False)
        dsl_rule = next(dsl_rule)
        logging.info("Generating rule from DSL...")
        rule = cls.generate_rule_from_dsl(description, dsl_rule, rule_type)
        logging.info("Optimizing rule...")
        optimized_rule = cls.optimize_rule(rule, description)
        return optimized_rule

    @classmethod
    def generate_rule_simple(cls, description: str, rule_type: str, required_fields: str = None,
                             log_demo: str = None) -> str:
        # analyse_result = cls._analyse_rule_description(description, rule_type)
        from src.prompt import RULE_GENERATE_PROMPT_SIMPLE
        sys_prompt = RULE_GENERATE_PROMPT_SIMPLE.format(rule_type=rule_type)
        user_prompt = f'''
        The following is the {rule_type} rule description:
        {description}
        The following are the required fields:
        {required_fields}
        '''
        messages = [{"role": "system", "content": sys_prompt}, {"role": "user", "content": user_prompt}]
        # try several times to get the response
        response = safe_chat_completion(messages)
        return response.choices[0].message.content

    @classmethod
    def optimize_rule(cls, rule: str, description: str) -> str:
        from src.prompt import RULE_OPTIMIZE_PROMPT
        sys_prompt = RULE_OPTIMIZE_PROMPT
        user_prompt = f'''
        The following is the rule to be optimized:
        {rule}
        The following is the description of the rule:
        {description}
        '''
        messages = [{"role": "system", "content": sys_prompt}, {"role": "user", "content": user_prompt}]
        response = safe_chat_completion(messages)
        rule_message = re.search(r'```spl\n(.*?)\n```', response.choices[0].message.content, re.DOTALL).group(1)
        return rule_message

    @classmethod
    def _analyse_rule_description(cls, description: str, rule_type: str):
        from src.prompt import DESCRIPTION_ANALYSE_PROMPT

        system_prompt = DESCRIPTION_ANALYSE_PROMPT.format(rule_type=rule_type)
        user_prompt = f"""
                The following is a description of the {rule_type} rule:
                {description}
                """
        messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]
        analyse_response = client.chat.completions.create(model=model, messages=messages, )
        analyse_result = analyse_response.choices[0].message.content
        return analyse_result

    @classmethod
    def generate_dsl_rule(cls, description: str, rule_type: str, required_fields: str = None,
                          log_demo: str = None, stream: bool = False):
        from src.prompt import TASK_BREAKDOWN_PROMPTS
        from src.prompt import DSL_GENERATION_PROMPT
        from src.data import DSL_KEYWORD
        keyword = "\n".join(f'{k}: {v}' for k, v in DSL_KEYWORD.items())
        sys_prompt = DSL_GENERATION_PROMPT.format(rule_type=rule_type, rule_description=description, keyword=keyword)
        # if it has required fields, add to the prompt
        if required_fields:
            sys_prompt += f'\nBelow are the required fields:\n{required_fields}'
        if log_demo:
            sys_prompt += f'\nBelow is a demo log:\n{log_demo}'
        dsl_msgs = [{"role": "system", "content": sys_prompt}]
        breakdown_msgs = []
        background_prompt = TASK_BREAKDOWN_PROMPTS['BACKGROUND'].format(rule_type=rule_type, description=description)
        breakdown_msgs.append({"role": "system", "content": background_prompt})

        dsl_rules = []
        steps = [
            'UNDERSTANDING_PROBLEM', 'IDENTIFY_DATA_SOURCE', 'DEFINE_INITIAL_FILTERS',
            'EXTRACT_RELEVANT_FIELDS', 'PERFORM_DATA_AGGREGATION', 'CALCULATE_DERIVED_METRICS',
            'FILTER_ANOMALIES', 'OPTIMIZE_OUTPUT'
        ]

        for step in steps:
            _, step_output = cls._analyse_subtask(breakdown_msgs, dsl_msgs, step)
            dsl_rules.extend(step_output)

            if stream:
                yield step, _
                yield step, step_output

        print(dsl_rules)
        # optimize the dsl rules
        dsl_rules_str_optimized = cls._optimize_dsl_rule(dsl_rules, description)
        print(dsl_rules_str_optimized)
        if stream:
            yield "FINAL_RESULT", dsl_rules_str_optimized
        else:
            yield dsl_rules_str_optimized

    @classmethod
    def _analyse_subtask(cls, breakdown_msgs: list, dsl_msgs: list, subtask_name: str) -> tuple:
        from src.prompt import TASK_BREAKDOWN_PROMPTS
        subtask_prompt = TASK_BREAKDOWN_PROMPTS[subtask_name]
        breakdown_msgs.append({"role": "user", "content": subtask_prompt})
        try:
            response = client.chat.completions.create(model=model, messages=breakdown_msgs)
        except Exception as e:
            logging.error(f"Error: {e}")
            return '', ''
        analyse_message = response.choices[0].message.content
        breakdown_msgs.append({"role": "assistant", "content": analyse_message})

        dsl_msgs.append({"role": "user", "content": subtask_name.replace('_', ' ') + ':\n' + analyse_message})
        try:
            response = client.chat.completions.create(model=model, messages=dsl_msgs)
        except Exception as e:
            logging.error(f"Error: {e}")
            return '', ''
        dsl_message = response.choices[0].message.content
        dsl_msgs.append({"role": "assistant", "content": dsl_message})
        # use re to extract the text between ```plaintext and ```
        dsl_message = re.search(r'```plaintext\n(.*?)\n```', dsl_message, re.DOTALL).group(1)
        # split the dsl message by \n and remove the empty lines
        dsl_rules = [line for line in dsl_message.split('\n') if line.strip()]
        print(subtask_name.replace('_', ' ') + ':\n' + analyse_message)
        print(dsl_rules)
        return analyse_message, dsl_rules

    @classmethod
    def _optimize_dsl_rule(cls, dsl_rules, rule_description) -> str:
        from src.data import DSL_KEYWORD
        from src.prompt import DSL_OPTIMIZE_PROMPT
        dsl_rules_str = "\n".join(dsl_rules)
        sys_prompt = DSL_OPTIMIZE_PROMPT.format(keyword="\n".join(f'{k}: {v}' for k, v in DSL_KEYWORD.items()))
        user_prompt = f'## DSL Rules:\n{dsl_rules_str}\n\n## Rule Description:\n{rule_description}'
        messages = [{"role": "system", "content": sys_prompt}, {"role": "user", "content": user_prompt}]
        try:
            response = client.chat.completions.create(model=model, messages=messages)
        except Exception as e:
            logging.error(f"Error: {e}")
            return ''
        response_message = response.choices[0].message.content
        dsl_message = re.search(r'```plaintext\n(.*?)\n```', response_message, re.DOTALL).group(1)
        return dsl_message

    @classmethod
    def generate_rule_from_dsl(cls, description: str, dsl_rule: str, rule_type: str, required_fields: list = None) -> str:
        from src.prompt import RULE_GENERATE_FROM_DSL_PROMPT
        from src.data import DSL_KEYWORD
        sys_prompt = RULE_GENERATE_FROM_DSL_PROMPT.format(rule_type=rule_type, keyword="\n".join(
            f'{k}: {v}' for k, v in DSL_KEYWORD.items()))
        if required_fields:
            sys_prompt += f'\n## Below are the required fields:\n{required_fields}'
        user_prompt = f'## DSL Rule:\n{dsl_rule} \n\n ## Rule Description:\n{description}'
        messages = [{"role": "system", "content": sys_prompt}, {"role": "user", "content": user_prompt}]
        response = safe_chat_completion(messages)
        return response.choices[0].message.content


if __name__ == '__main__':
    #     splunk_rule = '''
    #     index=wineventlog EventCode=4688
    # | search (ProcessName="powershell.exe" OR Process_Name="cmd.exe" OR Process_Name="wscript.exe")
    # | search (CommandLine="*Invoke-Expression*" OR CommandLine="*EncodedCommand*" OR CommandLine="*DownloadFile*") | rename _time as TimeBin
    # | table TimeBin, Hostname, ProcessName, CommandLine
    # '''
    #     splunk_rule_obj = SplunkRule("splunk", splunk_rule)
    #     splunk_rule_obj.show_pipes()
    #     sentinel_rule_obj = RuleConverter.convert_rule(splunk_rule_obj, "sentinel")
    #     print(sentinel_rule_obj)
    rule_description_demo = "This analytic is designed to identify attempts to exploit a server-side template injection vulnerability in CrushFTP, designated as CVE-2024-4040. This severe vulnerability enables unauthenticated remote attackers to access and read files beyond the VFS Sandbox, circumvent authentication protocols, and execute arbitrary commands on the affected server. The issue impacts all versions of CrushFTP up to 10.7.1 and 11.1.0 on all supported platforms. It is highly recommended to apply patches immediately to prevent unauthorized access to the system and avoid potential data compromises. The search specifically looks for patterns in the raw log data that match the exploitation attempts, including READ or WRITE actions, and extracts relevant information such as the protocol, session ID, user, IP address, HTTP method, and the URI queried. It then evaluates these logs to confirm traces of exploitation based on the presence of specific keywords and the originating IP address, counting and sorting these events for further analysis."
    rule_type_demo = "splunk"
    required_fields_demo = '''required_fields:
    - _time
    - dest
    - source
    - src_ip
    - http_method
    - uri_query
    - user
    - action
    - message'''
    generated_rule = RuleGenerator.generate_rule(rule_description_demo, rule_type_demo, required_fields_demo)
    print(generated_rule)
    generated_rule_simple = RuleGenerator.generate_rule_simple(rule_description_demo, rule_type_demo,
                                                               required_fields_demo)
    print('-----------------')
    print(generated_rule_simple)
