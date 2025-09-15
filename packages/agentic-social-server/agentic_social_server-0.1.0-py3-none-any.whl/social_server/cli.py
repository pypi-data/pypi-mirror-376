"""
Command Line Interface for Agentic Social Server
"""
import sys
import argparse
import subprocess
from pathlib import Path


def main():
    """Main CLI entry point for Agentic Social Server"""
    parser = argparse.ArgumentParser(
        description="Agentic Social Server - AI-powered social media platform for book lovers"
    )
    parser.add_argument(
        "page",
        nargs="?",
        default="feed",
        choices=["feed", "profile"],
        help="Page to launch (default: feed)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8503,
        help="Port to run the server on (default: 8503)"
    )

    args = parser.parse_args()

    # Get the package directory
    package_dir = Path(__file__).parent

    if args.page == "feed":
        streamlit_file = package_dir / "pages" / "22_AI_Social_Feed.py"
    elif args.page == "profile":
        streamlit_file = package_dir / "pages" / "23_Profile_Home.py"

    if not streamlit_file.exists():
        print(f"Error: Streamlit file not found: {streamlit_file}")
        sys.exit(1)

    # Launch streamlit
    cmd = [
        sys.executable, "-m", "streamlit", "run",
        str(streamlit_file),
        "--server.port", str(args.port)
    ]

    print(f"Starting Agentic Social Server on port {args.port}...")
    print(f"Running: {' '.join(cmd)}")

    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\nShutting down server...")
    except subprocess.CalledProcessError as e:
        print(f"Error running streamlit: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()