#!/usr/bin/env python3
"""
Server Startup Script for ToolboxAI Roblox Environment

Starts both FastAPI (port 8008) and Flask (port 5001) servers in the correct order
and with proper error handling and monitoring.
"""

import os
import sys
import time
import signal
import subprocess
import threading
import logging
from pathlib import Path
from typing import List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ServerManager:
    """Manages the startup and shutdown of both servers"""

    def __init__(self):
        self.processes: List[subprocess.Popen] = []
        self.shutdown_event = threading.Event()

        # Register signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down servers...")
        self.shutdown_event.set()
        self.stop_servers()
        sys.exit(0)

    def start_flask_server(self) -> Optional[subprocess.Popen]:
        """Start Flask bridge server"""
        try:
            logger.info("Starting Flask bridge server on port 5001...")

            # Get the path to roblox_server.py
            server_path = Path(__file__).parent / "roblox_server.py"

            process = subprocess.Popen(
                [sys.executable, str(server_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            # Give it time to start
            time.sleep(2)

            # Check if process is still running
            if process.poll() is None:
                logger.info("Flask bridge server started successfully")
                return process
            else:
                logger.error("Flask bridge server failed to start")
                return None

        except Exception as e:
            logger.error(f"Failed to start Flask server: {e}")
            return None

    def start_fastapi_server(self) -> Optional[subprocess.Popen]:
        """Start FastAPI main server"""
        try:
            logger.info("Starting FastAPI main server on port 8008...")

            # Get the path to main.py
            main_path = Path(__file__).parent / "main.py"

            process = subprocess.Popen(
                [sys.executable, str(main_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            # Give it time to start
            time.sleep(3)

            # Check if process is still running
            if process.poll() is None:
                logger.info("FastAPI main server started successfully")
                return process
            else:
                logger.error("FastAPI main server failed to start")
                return None

        except Exception as e:
            logger.error(f"Failed to start FastAPI server: {e}")
            return None

    def check_dependencies(self) -> bool:
        """Check if required dependencies are available"""
        try:
            import fastapi
            import flask
            import redis
            import openai
            import langchain

            logger.info("All required dependencies are available")
            return True
        except ImportError as e:
            logger.error(f"Missing dependency: {e}")
            logger.error("Please run: pip install -r requirements.txt")
            return False

    def check_environment(self) -> bool:
        """Check environment configuration"""
        required_vars = ["OPENAI_API_KEY"]
        missing_vars = []

        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)

        if missing_vars:
            logger.warning(f"Missing environment variables: {missing_vars}")
            logger.warning("Some features may not work properly")
            return False

        return True

    def start_servers(self):
        """Start both servers in the correct order"""
        logger.info("Starting ToolboxAI Roblox Environment servers...")

        # Check dependencies
        if not self.check_dependencies():
            logger.error("Dependencies check failed. Exiting.")
            return False

        # Check environment
        self.check_environment()

        # Start Flask server first (bridge server)
        flask_process = self.start_flask_server()
        if flask_process:
            self.processes.append(flask_process)
        else:
            logger.error("Failed to start Flask server. Exiting.")
            return False

        # Wait a bit for Flask to fully initialize
        time.sleep(2)

        # Start FastAPI server
        fastapi_process = self.start_fastapi_server()
        if fastapi_process:
            self.processes.append(fastapi_process)
        else:
            logger.error("Failed to start FastAPI server. Stopping Flask server.")
            self.stop_servers()
            return False

        logger.info("All servers started successfully!")
        logger.info("FastAPI server: http://127.0.0.1:8008")
        logger.info("Flask bridge server: http://127.0.0.1:5001")
        logger.info("API Documentation: http://127.0.0.1:8008/docs")
        logger.info("Press Ctrl+C to stop all servers")

        return True

    def monitor_servers(self):
        """Monitor server processes and restart if needed"""
        while not self.shutdown_event.is_set():
            try:
                # Check if processes are still running
                for i, process in enumerate(self.processes.copy()):
                    if process.poll() is not None:
                        logger.warning(
                            f"Server process {i} has died. Return code: {process.poll()}"
                        )

                        # Get stderr output
                        try:
                            stderr_output = (
                                process.stderr.read().decode() if process.stderr else "No stderr"
                            )
                            if stderr_output and stderr_output != "No stderr":
                                logger.error(f"Server stderr: {stderr_output}")
                        except (IOError, OSError, AttributeError) as e:
                            logger.debug(f"Could not read stderr from process: {e}")

                        # Remove dead process
                        self.processes.remove(process)

                # If all processes are dead, exit
                if not self.processes:
                    logger.error("All server processes have died. Exiting.")
                    self.shutdown_event.set()
                    break

                # Wait before next check
                time.sleep(5)

            except Exception as e:
                logger.error(f"Error monitoring servers: {e}")
                time.sleep(5)

    def stop_servers(self):
        """Stop all server processes"""
        logger.info("Stopping all servers...")

        for i, process in enumerate(self.processes):
            try:
                logger.info(f"Stopping server process {i}...")
                process.terminate()

                # Wait for graceful shutdown
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    logger.warning(f"Process {i} didn't terminate gracefully, killing...")
                    process.kill()
                    process.wait()

                logger.info(f"Server process {i} stopped")

            except Exception as e:
                logger.error(f"Error stopping process {i}: {e}")

        self.processes.clear()
        logger.info("All servers stopped")

    def run(self):
        """Main run method"""
        if self.start_servers():
            try:
                # Start monitoring in a separate thread
                monitor_thread = threading.Thread(target=self.monitor_servers, daemon=True)
                monitor_thread.start()

                # Wait for shutdown signal
                self.shutdown_event.wait()

            except KeyboardInterrupt:
                logger.info("Received keyboard interrupt, shutting down...")
            finally:
                self.stop_servers()
        else:
            logger.error("Failed to start servers")
            return 1

        return 0


def main():
    """Main entry point"""
    try:
        manager = ServerManager()
        return manager.run()
    except Exception as e:
        logger.error(f"Startup script error: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
