import json
import os
import signal
import subprocess
import sys
import time
from threading import Lock, Thread

import daemon
import daemon.pidfile
from lockfile import AlreadyLocked
from loguru import logger

from pm5.argparsers.pm5 import get_app_args

LOCK_FILE = "process_lock.json"  # File to store process IDs to manage process locking
PID_FILE = ".daemon.pid"  # File to store the PID of the daemon

lock = Lock()  # Lock to handle thread synchronization

shutdown = False  # Global flag to indicate if the system is shutting down


# Global list to keep track of running processes and a dictionary to map process IDs to service names
processes = []
process_service_map = {}


# Function to read the ecosystem configuration from a JSON file
def read_config(file_path):
    with open(file_path, "r") as file:
        return json.load(file)


# Function to start a service instance
def start_service(service, instance_id):
    # Construct the command to start the service
    command = [service["interpreter"]] + service.get("interpreter_args", [])
    if service["script"]:
        command.append(service["script"])
    command += service.get("args", [])

    env = os.environ.copy()  # Copy current environment variables

    env.update(
        {k: str(v) for k, v in service.get("env", {}).items()}
    )  # Update with service-specific environment variables

    cwd = service.get(
        "cwd", os.getcwd()
    )  # Use specified cwd or current working directory if not set

    process = subprocess.Popen(
        command, env=env, cwd=cwd, preexec_fn=os.setsid
    )  # Start the process

    with lock:  # Ensure thread-safe access
        processes.append(process)  # Add process to the list

        process_service_map[process.pid] = service[
            "name"
        ]  # Map process ID to service name

        update_lock_file()  # Update the lock file with running process IDs

    logger.info(
        f"Starting instance {instance_id} of service '{service['name']}' with command: {' '.join(command)} (PID: {process.pid}) in directory: {cwd}"
    )

    return process


# Function to monitor a service and restart it if necessary
def monitor_service(service, process, instance_id):
    global shutdown

    max_restarts = service.get(
        "max_restarts", 0
    )  # Get maximum number of restarts allowed

    restarts = 0  # Initialize restart count

    while restarts <= max_restarts and not shutdown:
        process.wait()  # Wait for the process to finish

        with lock:
            if process in processes:
                processes.remove(process)  # Remove process from the list

                update_lock_file()  # Update the lock file

        if shutdown:
            break

        if process.returncode != 0:  # If the process exited with an error
            logger.error(
                f"Instance {instance_id} of service '{service['name']}' exited with error code {process.returncode}"
            )

        if restarts < max_restarts and service.get("autorestart", False):
            logger.info(
                f"Restarting instance {instance_id} of service '{service['name']}' (Restart {restarts + 1})"
            )

            process = start_service(service, instance_id)  # Restart the service

            restarts += 1  # Increment restart count

        elif restarts == max_restarts:
            if process.returncode != 0:
                logger.warning(
                    f"Instance {instance_id} of service '{service['name']}' has exceeded the maximum number of restarts ({max_restarts}). Stopping all services."
                )

                handle_exit(signal.SIGTERM, None)  # Exit if max restarts exceeded

        else:
            if process.returncode != 0:
                logger.error(
                    f"Instance {instance_id} of service '{service['name']}' has exited with an error and will not be restarted"
                )

            break


# Function to clean up all running processes
def cleanup_processes():
    global shutdown

    if shutdown is True:
        logger.warning("Shutting down all services. Please hold...")

        return

    shutdown = True

    with lock:
        for process in processes:
            service_name = process_service_map.get(process.pid, "Unknown service")

            try:
                logger.info(
                    f"Sending SIGTERM to process group {os.getpgid(process.pid)} of service '{service_name}'"
                )

                os.killpg(
                    os.getpgid(process.pid), signal.SIGTERM
                )  # Send SIGTERM to process group

            except Exception as e:
                logger.info(
                    f"Error sending SIGTERM to process group {os.getpgid(process.pid)} of service '{service_name}': {e}"
                )

        logger.info("Cleaning up services...")

        time.sleep(1)  # Give some time for processes to terminate gracefully

        for process in processes:
            service_name = process_service_map.get(process.pid, "Unknown service")

            if process.poll() is None:  # Check if process is still running
                try:
                    logger.info(
                        f"Sending SIGKILL to process group {os.getpgid(process.pid)} of service '{service_name}'"
                    )

                    os.killpg(
                        os.getpgid(process.pid), signal.SIGKILL
                    )  # Send SIGKILL to process group

                except Exception as e:
                    logger.info(
                        f"Error sending SIGKILL to process group {os.getpgid(process.pid)} of service '{service_name}': {e}"
                    )

        for process in processes:
            try:
                process.wait(timeout=5)  # Wait for process to terminate

            except subprocess.TimeoutExpired:
                service_name = process_service_map.get(process.pid, "Unknown service")

                logger.warning(
                    f"Process {process.pid} of service '{service_name}' did not terminate in time"
                )

        clear_lock_file()  # Clear the lock file

    logger.info("Service cleanup complete.")


# Function to handle script exit
def handle_exit(signum, frame):
    global shutdown

    if shutdown is True:
        return

    logger.info("Terminating services...")

    cleanup_processes()

    with lock:
        if len(processes) > 0:
            for process in processes:
                if process.poll() is None:
                    logger.warning(
                        f"Process {process.pid} is still running, forcing exit..."
                    )

                    os.killpg(
                        os.getpgid(process.pid), signal.SIGKILL
                    )  # Force kill remaining processes

    os._exit(1)  # Force exit with error


# Function to read the lock file containing process IDs
def read_lock_file():
    if os.path.exists(LOCK_FILE):
        with open(LOCK_FILE, "r") as file:
            try:
                return json.load(file)

            except json.JSONDecodeError:
                return []

    return []


# Function to update the lock file with current process IDs
def update_lock_file():
    pids = [process.pid for process in processes]

    with open(LOCK_FILE, "w") as file:
        json.dump(pids, file)


# Function to clear the lock file
def clear_lock_file():
    if os.path.exists(LOCK_FILE):
        os.remove(LOCK_FILE)


# Function to terminate existing processes from the lock file
def terminate_existing_processes():
    pids = read_lock_file()
    active_pids = []

    for pid in pids:
        try:
            # Verify if the process group is still running
            os.killpg(pid, 0)
            logger.info(f"Terminating existing process group with pid: {pid}")
            os.killpg(pid, signal.SIGTERM)
            active_pids.append(pid)
        except ProcessLookupError:
            logger.warning(f"No process group found with pid: {pid}")
        except PermissionError:
            logger.warning(
                f"Permission denied to terminate process group with pid: {pid}"
            )

    # Update the lock file with only the active pids, if any, or clear it
    if active_pids:
        with open(LOCK_FILE, "w") as file:
            json.dump(active_pids, file)
    else:
        clear_lock_file()


# Main function to start the process manager
def main(**kwargs):
    # Print the PID of the current Python process
    logger.debug(f"The process manager process id is: {os.getpid()}")

    # Register signal handlers for graceful exit
    signal.signal(signal.SIGTERM, handle_exit)
    signal.signal(signal.SIGINT, handle_exit)

    # Terminate any existing processes from previous runs
    terminate_existing_processes()

    # Read the ecosystem configuration file
    config = read_config(kwargs["config_file"])
    services = config["services"]

    # Start all service instances
    total_cpus = os.cpu_count()

    services_started = False

    for service in services:
        if service.get("disabled", False):
            logger.info(f"Service '{service['name']}' is disabled. Skipping...")

            continue

        instances = service.get("instances", 1)

        if instances < 0:
            instances = max(
                1, total_cpus - abs(instances)
            )  # Ensure at least 1 instance

        for i in range(instances):
            process = start_service(service, i)

            services_started = True

            if service.get("wait_ready", False):
                thread = Thread(target=monitor_service, args=(service, process, i))

                thread.start()

    if not services_started:
        logger.error("Error: No services to start. Exiting...")

        sys.exit(1)

    # Wait for script termination
    try:
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        logger.info("Terminating services via keyboard exit...")
        cleanup_processes()
        sys.exit(0)


def daemon_main():
    main(**get_app_args())


def start_daemon():
    try:
        with daemon.DaemonContext(
            working_directory=os.getcwd(),
            umask=0o002,
            pidfile=daemon.pidfile.TimeoutPIDLockFile(PID_FILE),
            stdout=sys.stdout,
            stderr=sys.stderr,
        ):
            daemon_main()
    except AlreadyLocked:
        logger.error("Daemon is already running.")
    except Exception as e:
        logger.exception("Error starting daemon.")


def stop_daemon():
    try:
        with open(PID_FILE, "r") as f:
            pid = int(f.read().strip())
            os.kill(pid, signal.SIGTERM)
            logger.info("Daemon stopped successfully.")
            # Clear the PID file
            os.remove(PID_FILE)
    except FileNotFoundError:
        logger.error("PID file not found. Is the daemon running?")
    except ProcessLookupError:
        logger.error("No such process. The daemon may have already stopped.")
    except Exception as e:
        logger.error(f"Error stopping daemon: {e}")


def app():
    args = get_app_args()

    if args["command"] == "start":
        if args["debug"]:
            main(**args)
        else:
            start_daemon()
    elif args["command"] == "stop":
        stop_daemon()
    else:
        logger.error("Unknown command. Use 'start' or 'stop'.")
