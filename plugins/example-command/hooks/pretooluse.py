import sys
import json

def run_hook():
    # Example logic mapping to Claude Code's expected IO hook format
    input_data = sys.stdin.read()
    try:
        data = json.loads(input_data)
        if "rm -rf" in str(data):
            print("Block execution: Detected dangerous command.")
            sys.exit(1)
            
        print("PreToolUse check passed safely - proceeding.")
        sys.exit(0)
    except Exception as e:
        sys.exit(0)

if __name__ == "__main__":
    run_hook()
