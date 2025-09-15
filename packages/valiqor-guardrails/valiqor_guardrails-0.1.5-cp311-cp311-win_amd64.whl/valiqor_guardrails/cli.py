import argparse
import json
from valiqor_guardrails.checker import GuardrailChecker

def main():
    parser = argparse.ArgumentParser(description="Run GPT-5 guardrail checks.")
    parser.add_argument("--api_key", required=True)
    parser.add_argument("--user_input", required=True)
    parser.add_argument("--agent_output", required=True)
    parser.add_argument("--conversation_file", help="Path to conversation memory (optional)", default=None)

    args = parser.parse_args()

    conversation_memory = ""
    if args.conversation_file:
        with open(args.conversation_file, "r") as f:
            conversation_memory = f.read()

    checker = GuardrailChecker(api_key=args.api_key)
    report = checker.run(args.user_input, args.agent_output, conversation_memory)

    print(json.dumps(report, indent=2))
