# RulePilot - AI-Powered Security Rule Generation

**Paper:** ICSE'26 (https://github.com/LLM4SOC-Topic/RulePilot/blob/main/Rule_Gen_ICSE.pdf)

## 🚀 Features
- **Multi-Platform Support**: Generate rules for Splunk and Microsoft Sentinel.
- **AI-Powered Optimization**: GPT-4 powered rule refinement with multi-stage validation
- **Context-Aware Generation**: Automatic field detection from log samples
- **Interactive Debugging**: Step-by-step rule generation process visualization
- **Cross-Platform Conversion**: Convert rules between different SIEM/SOAR systems

## 📦 Installation
```bash
# Clone repository
cd RulePilot

# Install dependencies
pip install -r requirements.txt

# Configure API keys
cp .env.example .env
```

## 🔧 Configuration
1. Get your [OpenAI API key](https://platform.openai.com/api-keys)
2. Add to `.env`:
```ini
OPENAI_API_KEY=sk-your-key-here
MODEL_NAME=gpt-4o
```

## 🛠️ Usage
```bash
# Start web UI
streamlit run app.py
```

### Key Workflows:
1. **Rule Generation**:
   - Select target platform (Splunk/Sentinel/Elastic)
   - Describe detection logic in natural language
   - Enable AI Agent for multi-step optimization

2. **Rule Conversion**:
   - Upload existing rules
   - Select target platform
   - Get automatically converted rules with dependency mapping


## 📄 License
MIT License | See [LICENSE](LICENSE) file
