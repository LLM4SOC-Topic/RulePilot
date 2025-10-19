from dotenv import load_dotenv
import pandas as pd
import openai
import os
import json
import yaml
from pathlib import Path
from src.rule import model

load_dotenv()
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def extract_info_from_markdown_table(markdown_table: str) -> dict:
    client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    from src.prompt import PREPROCESSING_PROMPT
    sys_prompt = PREPROCESSING_PROMPT
    user_prompt = f'''
    The following is a markdown table:
    {markdown_table}
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


def description_and_rule_generator(rule_type: str) -> dict:
    dataset_path = os.path.join(PROJECT_ROOT, f'dataset/descriptions/{rule_type}')
    for file in os.listdir(dataset_path):
        # read yaml file
        path = os.path.join(dataset_path, file)
        with open(path, 'r') as f:
            data = f.read()
        # parse yaml file
        data = yaml.load(data, Loader=yaml.FullLoader)
        yield path, data


def optimize_rule(rule: str, gt: str) -> str:
    client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    from src.prompt import OPTIMIZE_RULE_PROMPT
    sys_prompt = OPTIMIZE_RULE_PROMPT
    user_prompt = f'''
    The following is the rule to optimize:
    {rule}
    The following is the ground truth:
    {gt}
    '''
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return response.choices[0].message.content


def load_conversion_dataset(file_path: str) -> dict:
    with open(file_path, 'r') as f:
        data = f.read()
    return json.loads(data)
