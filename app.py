import streamlit as st
import os
from src.rule import RuleGenerator, RuleConverter


def main_page():
    st.title('RulePilot')
    api_key_openai = st.sidebar.text_input(
        "OpenAI API Key",
        st.session_state.get("OPENAI_API_KEY", ""),
        type="password",
    )
    model_openai = st.sidebar.selectbox(
        "OpenAI Model",
        ("gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"),
    )
    settings = {
        "model": model_openai,
        "model_provider": "openai",
        "temperature": 0.3,
    }
    st.session_state["OPENAI_API_KEY"] = api_key_openai
    os.environ["OPENAI_API_KEY"] = st.session_state["OPENAI_API_KEY"]
    os.environ["MODEL_NAME"] = settings["model"]
    # Load existing .env first
    from dotenv import load_dotenv
    load_dotenv(override=False)

    # Initialize session state from .env
    st.session_state["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "")
    st.session_state["DEFAULT_MODEL"] = os.getenv("MODEL_NAME", "gpt-4-turbo")

    # Sync UI changes to .env
    if api_key_openai or model_openai != st.session_state["DEFAULT_MODEL"]:
        with open(".env", "w", encoding="utf-8") as f:
            f.write(f'OPENAI_API_KEY={api_key_openai}\n')
            f.write(f'MODEL_NAME={model_openai}\n')
    page_rule_generation()


def page_rule_generation():
    if "rule_type" not in st.session_state:
        st.session_state.rule_type = "Splunk"

    st.subheader("Select Rule Type:")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("Splunk", key="splunk_button"):
            st.session_state.rule_type = "Splunk"

    with col2:
        if st.button("Microsoft Sentinel", key="sentinel_button"):
            st.session_state.rule_type = "Microsoft Sentinel"

    with col3:
        if st.button("Elastic", key="elastic_button"):
            st.session_state.rule_type = "Elastic"

    rule_description = st.text_area("Enter Rule Description:",
                                    placeholder="Describe the rule here...")

    required_fields = st.text_area("Enter Required Fields:",
                                   placeholder="List the required fields here...")

    # if st.button("Generate Rule"):
    #     if rule_description and required_fields:
    #         generated_rule = RuleGenerator.generate_rule(rule_description, st.session_state.rule_type, required_fields)["rule"]
    #         st.success("✅ Rule Generated Successfully!")
    #
    #         st.subheader("Generated Rule:")
    #         st.markdown(generated_rule)
    use_agent = st.checkbox("Use Agent", help="Use AI Agent to generate and optimze the rule step by step",)
    
    if st.button("Generate Rule"):
        st.write("Generating rule...")
        st.session_state.use_agent = use_agent

        output_area = st.empty()
        progress_bar = st.progress(0)

        dsl_rules_output = ""
        steps_count = 16

        for idx, (step, result) in enumerate(
                RuleGenerator.web_rule_generator(rule_description, st.session_state.rule_type, required_fields)):
            if step == "FINAL_RULE":
                dsl_rules_output += f"\n\n### **Final Generated Rule:**\n{result}"
            elif step == "FINAL_RESULT":
                dsl_rules_output += f"\n\n### **Optimized DSL Rule:**\n{result}"
            else:
                dsl_rules_output += f"\n**{step.replace('_', ' ').title()}**:\n{result}\n"

            output_area.markdown(dsl_rules_output)
            progress_bar.progress((idx + 1) / (steps_count + 2))


def page_rule_conversion():
    if "rule_type" not in st.session_state:
        st.session_state.rule_type = "Splunk"

    st.subheader("Select Rule Type:")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("Splunk", key="splunk_button"):
            st.session_state.rule_type = "Splunk"

    with col2:
        if st.button("Microsoft Sentinel", key="sentinel_button"):
            st.session_state.rule_type = "Microsoft Sentinel"

    with col3:
        if st.button("Elastic", key="elastic_button"):
            st.session_state.rule_type = "Elastic"

    rule_description = st.text_area("Enter Rule Description:",
                                    placeholder="Describe the rule here...")

    required_fields = st.text_area("Enter Required Fields:",
                                   placeholder="List the required fields here...")

    if st.button("Generate Rule"):
        if rule_description and required_fields:
            generated_rule = RuleConverter.convert_rule(rule_description, st.session_state.rule_type)["rule"]
            st.success("✅ Rule Generated Successfully!")

            st.subheader("Generated Rule:")
            st.markdown(generated_rule)


if __name__ == '__main__':
    main_page()
