import subprocess, sys
result = subprocess.run(
    ["/workspace/Just_A_Suggestion_Game/.venv/bin/python", "-c", "import main; print('OK')"],
    cwd="/workspace/Just_A_Suggestion_Game",
    capture_output=True, text=True
)
print("STDOUT:", result.stdout)
print("STDERR:", result.stderr)
print("CODE:", result.returncode)
