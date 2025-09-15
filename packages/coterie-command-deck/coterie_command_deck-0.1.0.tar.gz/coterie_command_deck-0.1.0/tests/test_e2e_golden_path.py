"""E2E Golden Path test for Coterie Command Deck."""

import subprocess


def run(cmd):
    print(f"$ {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(result.stderr)
    assert result.returncode == 0, f"Failed: {' '.join(cmd)}"


# 1. Assign a task
run(["deck", "assign", "Jet", "CleanWindows", "--priority", "high"])
# 2. Log a completed task
run(["deck", "log", "CleanWindows"])
# 3. Show board
run(["deck", "board"])
# 4. End job
run(["deck", "end_job", "Jet"])
# 5. Show history
run(["deck", "history", "--limit", "5"])
# 6. Replay last command
run(["deck", "replay", "1"])
# 7. Notify (DRY-RUN SMS)
run(["deck", "notify", "Job done", "--channel", "sms", "--to", "+18501234567"])
# 8. Notify (DRY-RUN Email)
run(["deck", "notify", "Summary", "--channel", "email", "--to", "you@example.com"])
# 9. Invoice (DRY-RUN Stripe)
run(
    [
        "deck",
        "invoice",
        "--client",
        "B&N Destin",
        "--amount",
        "187.50",
        "--memo",
        "Weekly",
    ]
)
