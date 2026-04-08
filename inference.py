import os
import subprocess

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    subprocess.run(
        [
            "uvicorn",
            "server.app:app",
            "--host",
            "0.0.0.0",
            "--port",
            str(port),
        ]
    )