import subprocess
import tempfile
import os
import re, shlex
import multiprocessing
import threading
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Dict, List, Any
from scientiflow_cli.services.status_updater import update_job_status, update_stopped_at_node, update_current_node, get_job_status, get_current_node
from scientiflow_cli.services.request_handler import make_auth_request
from scientiflow_cli.services.rich_printer import RichPrinter

printer = RichPrinter()

def execute_background_command_standalone(command: str, log_file_path: str):
    """Execute a command in background without real-time output display - standalone function for multiprocessing."""
    try:
        proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output, _ = proc.communicate()
        
        result = output.decode(errors="replace")
        
        # Log the output to the specific log file
        with open(log_file_path, 'a') as f:
            f.write(result + "\n")
        
        if proc.returncode != 0:
            with open(log_file_path, 'a') as f:
                f.write(f"[ERROR] Command failed with return code {proc.returncode}\n")
            return False
        
        return True
        
    except Exception as e:
        with open(log_file_path, 'a') as f:
            f.write(f"[ERROR] An unexpected error occurred: {e}\n")
        return False

class PipelineExecutor:
    def __init__(self, base_dir: str, project_id: int, project_job_id: int, project_title: str, job_dir_name: str, nodes: List[Dict[str, Any]], edges: List[Dict[str, str]], environment_variables: Dict[str, str], start_node: str = None, end_node: str = None, job_status: str = None, current_node_from_config: str = None):
        self.base_dir = base_dir
        self.project_id = project_id
        self.project_job_id = project_job_id
        self.project_title = project_title
        self.job_dir_name = job_dir_name
        self.nodes = nodes
        self.edges = edges
        self.environment_variables = environment_variables
        self.start_node = start_node
        self.end_node = end_node
        self.current_node = None
        self.job_status = job_status
        self.current_node_from_config = current_node_from_config
        self.background_executors = []  # Keep track of background executors
        self.background_jobs_count = 0  # Track number of active background jobs
        self.background_jobs_completed = 0  # Track completed background jobs
        self.background_jobs_lock = threading.Lock()  # Thread-safe counter updates

        # Set up job-specific log file
        self.log_file_path = os.path.join(self.base_dir, self.project_title, self.job_dir_name, "logs", "output.log")
        os.makedirs(os.path.dirname(self.log_file_path), exist_ok=True)

        # Create mappings for efficient execution
        self.nodes_map = {node['id']: node for node in nodes}
        self.adj_list = {node['id']: [] for node in nodes}
        for edge in edges:
            self.adj_list[edge['source']].append(edge['target'])

        # Identify root nodes (nodes with no incoming edges)
        all_nodes = set(self.nodes_map.keys())
        target_nodes = {edge['target'] for edge in edges}
        self.root_nodes = all_nodes - target_nodes

        # Initialize log file
        self.init_log()

    def init_log(self):
        """Initialize the log file."""
        try:
            # If job is running (resuming), append to existing log file
            # Otherwise, create a fresh log file
            if self.job_status == "running":
                # Check if log file exists, if not create it
                with open(self.log_file_path, 'a') as f:
                    f.write('')
            else:
                # Create fresh log file for new execution
                with open(self.log_file_path, 'w') as f:
                    f.write('')
        except Exception as e:
            print(f"[ERROR] Failed to initialize log file: {e}")

    def log_output(self, text: str):
        """Write to log file."""
        try:
            with open(self.log_file_path, 'a') as f:
                f.write(text + "\n")
        except Exception as e:
            print(f"[ERROR] Failed to write log: {e}")

    def update_terminal_output(self):
        """Update the terminal output after execution is complete."""
        try:
            with open(self.log_file_path, 'r') as f:
                terminal_output = f.read()
            body = {"project_job_id": self.project_job_id, "terminal_output": terminal_output}
            make_auth_request(endpoint="/agent-application/update-terminal-output", method="POST", data=body, error_message="Unable to update terminal output!")
            printer.print_message("[+] Terminal output updated successfully.", style="bold green")
        except Exception as e:
            print(f"[ERROR] Failed to update terminal output: {e}")

    def replace_variables(self, command: str) -> str:
        def replacer(match):
            key = match.group(1)
            value = self.environment_variables.get(key, match.group(0))
            if isinstance(value, list):
                # Convert list to safe, space-separated string
                return " ".join(shlex.quote(str(v)) for v in value)
            return shlex.quote(str(value)) if isinstance(value, str) else str(value)
        t = re.sub(r'\$\{(\w+)\}', replacer, command)
        return t

    def execute_command(self, command: str):
        """Run the command in the terminal, display output in real-time, and log the captured output."""
        import sys
        try:
            with tempfile.TemporaryFile() as tempf:
                proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                while True:
                    chunk = proc.stdout.read(1)
                    if not chunk:
                        break
                    sys.stdout.buffer.write(chunk)
                    sys.stdout.flush()
                    tempf.write(chunk)
                proc.stdout.close()
                proc.wait()

                tempf.seek(0)
                result = tempf.read().decode(errors="replace")
                self.log_output(result)  # Log the entire output

                if proc.returncode != 0:
                    self.log_output(f"[ERROR] Command failed with return code {proc.returncode}")
                    update_job_status(self.project_job_id, "failed")
                    update_stopped_at_node(self.project_id, self.project_job_id, self.current_node)
                    self.update_terminal_output()
                    raise SystemExit("[ERROR] Pipeline execution terminated due to failure.")

        except Exception as e:
            self.log_output(f"[ERROR] An unexpected error occurred: {e}")
            update_job_status(self.project_job_id, "failed")
            update_stopped_at_node(self.project_id, self.project_job_id, self.current_node)
            self.update_terminal_output()
            raise SystemExit("[ERROR] Pipeline execution terminated due to an unexpected error.")

    def monitor_background_job(self, futures, node_label, executor):
        """Monitor background job completion in a separate thread."""
        def monitor():
            all_successful = True
            for future in as_completed(futures):
                success = future.result()
                if not success:
                    all_successful = False
            
            if not all_successful:
                self.log_output(f"[ERROR] Background job {node_label} failed")
                printer.print_message(f"[BACKGROUND JOB] {node_label} Failed - some commands in background job failed", style="bold red")
            else:
                printer.print_message(f"[BACKGROUND JOB] {node_label} Execution completed in the background", style="bold green")
            
            # Clean up executor
            executor.shutdown(wait=False)
            if executor in self.background_executors:
                self.background_executors.remove(executor)
            
            # Update background job completion count
            with self.background_jobs_lock:
                self.background_jobs_completed += 1
        
        # Start monitoring thread
        monitor_thread = threading.Thread(target=monitor, daemon=True)
        monitor_thread.start()

    def wait_for_background_jobs(self):
        """Wait for all background jobs to complete."""
        import time
        if self.background_jobs_count > 0:
            printer.print_message(f"[INFO] Waiting for {self.background_jobs_count} background job(s) to complete...", style="bold yellow")
            
            while True:
                with self.background_jobs_lock:
                    if self.background_jobs_completed >= self.background_jobs_count:
                        break
                time.sleep(0.5)  # Check every 500ms
            
            printer.print_message("[INFO] All background jobs completed.", style="bold green")

    def dfs(self, node: str):
        """Perform Depth-First Search (DFS) for executing pipeline nodes."""
        if self.current_node == self.end_node:
            return

        self.current_node = node
        current_node = self.nodes_map[node]

        if current_node['type'] == "splitterParent":
            collector = None
            for child in self.adj_list[node]:
                if self.nodes_map[child]['data']['active']:
                    collector = self.dfs(child)
            if collector and self.adj_list[collector]:
                return self.dfs(self.adj_list[collector][0])
            return

        elif current_node['type'] == "splitter-child":
            if current_node['data']['active'] and self.adj_list[node]:
                return self.dfs(self.adj_list[node][0])
            return

        elif current_node['type'] == "terminal":
            # Update current node status
            update_current_node(self.project_id, self.project_job_id, node)
            
            commands = current_node['data']['commands']
            isGPUEnabled = current_node['data'].get('gpuEnabled', False)
            isBackgroundNode = current_node['data'].get('executeInBackground', False)
            node_label = current_node['data'].get('label', 'Unknown Node')
            
            if isBackgroundNode:
                # Background execution with multiprocessing
                numberOfThreads = current_node['data'].get('numberOfThreads', 1)
                printer.print_message(f"[BACKGROUND JOB] {node_label} Execution started in background", style="bold blue")
                
                # Prepare commands for parallel execution
                command_list = []
                for command in commands:
                    cmd = self.replace_variables(command.get('command', ''))
                    if cmd:
                        base_command = f"cd {self.base_dir}/{self.project_title}/{self.job_dir_name} && singularity exec "
                        container_path = f"{self.base_dir}/containers/{current_node['data']['software']}.sif"
                        gpu_flag = "--nv --nvccli" if isGPUEnabled else ""
                        full_command = f"{base_command} {gpu_flag} {container_path} {cmd}"
                        command_list.append(full_command)
                
                # Execute commands in background using ProcessPoolExecutor (non-blocking)
                if command_list:
                    # Increment background jobs counter
                    with self.background_jobs_lock:
                        self.background_jobs_count += 1
                    
                    executor = ProcessPoolExecutor(max_workers=numberOfThreads)
                    self.background_executors.append(executor)  # Keep reference to prevent garbage collection
                    futures = []
                    for cmd in command_list:
                        future = executor.submit(execute_background_command_standalone, cmd, self.log_file_path)
                        futures.append(future)
                    
                    # Start monitoring in a separate thread (non-blocking)
                    self.monitor_background_job(futures, node_label, executor)
                    
                    # Don't wait for completion, immediately continue to next node
                else:
                    printer.print_message(f"[BACKGROUND JOB] {node_label} No commands to execute", style="bold yellow")
            else:
                # Normal execution with real-time output
                for command in commands:
                    cmd = self.replace_variables(command.get('command', ''))
                    if cmd:
                        base_command = f"cd {self.base_dir}/{self.project_title}/{self.job_dir_name} && singularity exec "
                        container_path = f"{self.base_dir}/containers/{current_node['data']['software']}.sif"
                        gpu_flag = "--nv --nvccli" if isGPUEnabled else ""
                        full_command = f"{base_command} {gpu_flag} {container_path} {cmd}"
                        self.execute_command(full_command)

            if self.adj_list[node]:
                return self.dfs(self.adj_list[node][0])
            return

        elif current_node['type'] == "collector":
            return node if self.adj_list[node] else None

    def decode_and_execute_pipeline(self):
        """Start executing the pipeline."""
        # Use job status from configuration instead of API call
        current_status = self.job_status
        
        if current_status == "running":
            # Job is already running, resume from current node
            current_node_id = self.current_node_from_config
            if current_node_id and current_node_id in self.nodes_map:
                # Get the label from the current node
                current_node_label = self.nodes_map[current_node_id]['data'].get('label', current_node_id)
                printer.print_message(f"[INFO] Resuming execution from current node: {current_node_label}", style="bold blue")
                starting_node = current_node_id
            else:
                printer.print_message("[WARNING] Current node not found, starting from beginning", style="bold yellow")
                starting_node = self.start_node or next(iter(self.root_nodes), None)
        else:
            # Job is not running, start normally
            update_job_status(self.project_job_id, "running")
            starting_node = self.start_node or next(iter(self.root_nodes), None)

        if starting_node:
            self.dfs(starting_node)

        # Wait for all background jobs to complete before marking pipeline as completed
        self.wait_for_background_jobs()

        update_job_status(self.project_job_id, "completed")
        update_stopped_at_node(self.project_id, self.project_job_id, self.current_node)

        # Update terminal output at the end of execution
        self.update_terminal_output()

# External function to initiate the pipeline execution
def decode_and_execute_pipeline(base_dir: str, project_id: int, project_job_id: int, project_title: str, job_dir_name: str, nodes: List[Dict[str, Any]], edges: List[Dict[str, str]], environment_variables: Dict[str, str], start_node: str = None, end_node: str = None, job_status: str = None, current_node_from_config: str = None):
    """Initialize and execute the pipeline."""
    executor = PipelineExecutor(base_dir, project_id, project_job_id, project_title, job_dir_name, nodes, edges, environment_variables, start_node, end_node, job_status, current_node_from_config)
    executor.decode_and_execute_pipeline()