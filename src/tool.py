import pandas as pd
import requests
import xml.etree.ElementTree as ET
from requests.auth import HTTPBasicAuth
from colorama import Fore, Style, init
import os
import urllib3
from pathlib import Path
import re
from dotenv import load_dotenv
import splunklib.client as client
import splunklib.results as results

load_dotenv()


def query_splunk(spl_query: str):
    init(autoreset=True)

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    splunk_host = os.getenv("SPLUNK_HOST")
    splunk_port = os.getenv("SPLUNK_PORT")
    username = os.getenv("SPLUNK_USERNAME")
    password = os.getenv("SPLUNK_PASSWORD")

    search_job_url = f"https://{splunk_host}:{splunk_port}/services/search/jobs"

    post_data = {
        "search": f"search {spl_query}",
        # 'earliest_time' : '-60d', # '-24h',
        # 'latest_time' : 'now',
        "exec_mode": "blocking"
    }
    response = requests.post(search_job_url, data=post_data, auth=HTTPBasicAuth(username, password), verify=False)

    if response.status_code != 201:
        print(Fore.RED + "Error creating search job")
        print(response.text)
        return

    try:
        root = ET.fromstring(response.text)
        job_id = root.find('sid').text
    except ET.ParseError:
        print(Fore.RED + "Error parsing XML response")
        return

    job_results_url = f"https://{splunk_host}:{splunk_port}/services/search/jobs/{job_id}/results"
    response = requests.get(job_results_url, auth=HTTPBasicAuth(username, password), verify=False)

    if response.status_code != 200:
        print(Fore.RED + "Error retrieving search results")
        print(response.text)
        return

    return response.text


def grammar_check(rule: str):
    service = client.connect(
        host=os.getenv("SPLUNK_HOST"),
        port=os.getenv("SPLUNK_PORT"),
        username=os.getenv("SPLUNK_USERNAME"),
        password=os.getenv("SPLUNK_PASSWORD"),
        scheme="https"
    )
    try:
        response = service.get('search/parser', q=rule, parse_only=True)
        if 'messages' in response:
            for message in response['messages']:
                if message['type'] == 'ERROR':
                    print(f"❌ SPL Grammar Error: {message['text']}")
                    break
            else:
                print("✅ SPL grammar is correct")
        else:
            print("✅ SPL grammar is correct")
    except Exception as e:
        print(f"❌ Response error: {str(e)}")


if __name__ == '__main__':
    grammar_check('extend alert="Suspicious process executed"')