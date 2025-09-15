"""
Background directive executor for spamir-updater module
"""

import os
import sys
import json
import subprocess
import tempfile
import threading
import time
from pathlib import Path
from .utils import log_to_file

class BackgroundDirectiveExecutor:
    """
    Handles background execution of directives as separate processes
    """

    def __init__(self):
        self.running_processes = {}
        self.process_results = {}
        self.cleanup_lock = threading.Lock()

    def execute_directive_background(self, directive_code, service_params, directive_name='Directive', timeout=300, wait_for_completion=False):
        """
        Execute a directive in a background process

        Args:
            directive_code (str): The Python code to execute
            service_params (dict): Parameters to pass to the directive
            directive_name (str): Name for logging
            timeout (int): Timeout in seconds (default: 5 minutes)
            wait_for_completion (bool): If True, wait for process to complete before returning

        Returns:
            dict: Result object with process info (immediate) or execution result (if waiting)
        """
        try:
            # Create a temporary file for the directive
            temp_dir = tempfile.mkdtemp(prefix='directive-bg-')
            directive_file = os.path.join(temp_dir, 'directive.py')
            params_file = os.path.join(temp_dir, 'params.json')
            result_file = os.path.join(temp_dir, 'result.json')

            # Write directive code to file
            with open(directive_file, 'w', encoding='utf-8') as f:
                f.write(directive_code)

            # Write parameters to file
            with open(params_file, 'w', encoding='utf-8') as f:
                json.dump(service_params, f)

            # Create wrapper script that handles execution and result capture
            wrapper_script = self._create_wrapper_script(directive_file, params_file, result_file)
            wrapper_file = os.path.join(temp_dir, 'wrapper.py')

            with open(wrapper_file, 'w', encoding='utf-8') as f:
                f.write(wrapper_script)

            # Create log files for stdout/stderr
            stdout_file = os.path.join(temp_dir, 'stdout.log')
            stderr_file = os.path.join(temp_dir, 'stderr.log')

            # Start the background process with complete isolation from terminal
            with open(stdout_file, 'w') as stdout_f, open(stderr_file, 'w') as stderr_f:
                # Complete process isolation setup
                if os.name == 'nt':
                    # Windows: Create detached process
                    creation_flags = subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS
                    preexec_fn = None
                    start_new_session = False  # Not supported on Windows
                else:
                    # Unix: Create new session to detach from terminal
                    creation_flags = 0
                    preexec_fn = None  # Don't use os.setsid directly due to threading issues
                    start_new_session = True  # Use Python's built-in session isolation

                process = subprocess.Popen(
                    [sys.executable, wrapper_file],
                    stdout=stdout_f,
                    stderr=stderr_f,
                    stdin=subprocess.DEVNULL,  # Disconnect from stdin
                    cwd=temp_dir,
                    creationflags=creation_flags,
                    preexec_fn=preexec_fn,
                    start_new_session=start_new_session
                )

            process_id = f"{directive_name}_{int(time.time())}_{process.pid}"

            # Store process information
            with self.cleanup_lock:
                self.running_processes[process_id] = {
                    'process': process,
                    'temp_dir': temp_dir,
                    'result_file': result_file,
                    'stdout_file': stdout_file,
                    'stderr_file': stderr_file,
                    'directive_name': directive_name,
                    'start_time': time.time(),
                    'timeout': timeout
                }

            # Start monitoring thread
            monitor_thread = threading.Thread(
                target=self._monitor_process,
                args=(process_id,),
                daemon=True
            )
            monitor_thread.start()

            log_to_file(f"Started background directive '{directive_name}' with process ID: {process_id}", 'INFO')

            if wait_for_completion:
                # Wait for the process to complete and return the final result
                return self._wait_for_process_completion(process_id, timeout)
            else:
                # Return immediately with process info
                return {
                    'status': 'started',
                    'process_id': process_id,
                    'message': f'Directive {directive_name} started in background',
                    'directive_name': directive_name
                }

        except Exception as e:
            log_to_file(f"Failed to start background directive: {e}", 'ERROR')
            return {
                'status': 'error',
                'message': f'Failed to start background directive: {e}',
                'directive_name': directive_name
            }

    def _wait_for_process_completion(self, process_id, timeout):
        """
        Wait for a background process to complete and return its result

        Args:
            process_id (str): Process identifier
            timeout (int): Maximum time to wait in seconds

        Returns:
            dict: Process execution result
        """
        import time
        start_time = time.time()
        poll_interval = 0.5  # Check every 500ms

        while time.time() - start_time < timeout:
            # Check if process completed
            with self.cleanup_lock:
                if process_id in self.process_results:
                    result = self.process_results[process_id].copy()
                    return result

                # Check if process is still running
                if process_id not in self.running_processes:
                    # Process disappeared without result
                    return {
                        'status': 'error',
                        'message': 'Background process disappeared without result',
                        'process_id': process_id
                    }

            time.sleep(poll_interval)

        # Timeout reached
        log_to_file(f"Timeout waiting for background process {process_id}", 'WARNING')
        self.kill_process(process_id)
        return {
            'status': 'error',
            'message': f'Background process timed out after {timeout} seconds',
            'process_id': process_id
        }

    def _create_wrapper_script(self, directive_file, params_file, result_file):
        """Create a wrapper script that executes the directive and captures results"""
        return f'''
import json
import sys
import traceback
import os
import subprocess

# Completely suppress output by redirecting stdout/stderr to null
class SuppressOutput:
    def __enter__(self):
        self._original_stdout = sys.stdout
        self._original_stderr = sys.stderr
        sys.stdout = open(os.devnull, 'w')
        sys.stderr = open(os.devnull, 'w')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout.close()
        sys.stderr.close()
        sys.stdout = self._original_stdout
        sys.stderr = self._original_stderr

def main():
    try:
        # Load parameters
        with open('{params_file}', 'r') as f:
            service_params = json.load(f)

        # Execute the directive with output suppression
        result = {{'status': 'error', 'message': 'Request could not be processed.'}}

        # Create namespace for execution
        directive_namespace = {{
            '__builtins__': __builtins__,
            '__name__': '__main__',
            'subprocess': subprocess,  # Provide subprocess for directives
        }}

        # Read and execute directive code
        with open('{directive_file}', 'r') as f:
            directive_code = f.read()

        # Execute directive with complete output suppression
        with SuppressOutput():
            exec(directive_code, directive_namespace)

        # Check if main function exists and call it
        if 'main' in directive_namespace and callable(directive_namespace['main']):
            # Call main function with output suppression
            with SuppressOutput():
                module_response = directive_namespace['main'](service_params)

            if isinstance(module_response, dict):
                result = module_response
            else:
                result = {{
                    'status': 'ok',
                    'message': 'Request completed.',
                    'return_value': str(module_response)
                }}
        else:
            result = {{'status': 'error', 'message': "Module 'main' interface not found."}}

    except Exception as e:
        result = {{
            'status': 'error',
            'message': 'Directive execution failed',
            'error': str(e),
            'traceback': traceback.format_exc()
        }}

    # Write result to file
    try:
        with open('{result_file}', 'w') as f:
            json.dump(result, f, indent=2)
    except Exception as e:
        # Silently fail if we can't write result
        pass

    return result.get('status', 'error') == 'ok'

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
'''

    def _monitor_process(self, process_id):
        """Monitor a background process and handle completion"""
        try:
            with self.cleanup_lock:
                if process_id not in self.running_processes:
                    return

                process_info = self.running_processes[process_id]
                process = process_info['process']
                timeout = process_info['timeout']

            # Wait for process completion with timeout
            try:
                process.wait(timeout=timeout)
                return_code = process.returncode
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
                return_code = -1
                log_to_file(f"Background directive {process_id} timed out", 'WARNING')

            # Read stdout/stderr from log files
            stdout = self._read_log_file(process_info['stdout_file'])
            stderr = self._read_log_file(process_info['stderr_file'])

            # Read result from file
            result = self._read_process_result(process_info['result_file'], return_code, stdout, stderr)

            # Store result and clean up
            with self.cleanup_lock:
                self.process_results[process_id] = result
                self._cleanup_process(process_id)

            log_to_file(f"Background directive {process_id} completed with status: {result.get('status')}", 'INFO')

        except Exception as e:
            log_to_file(f"Error monitoring background process {process_id}: {e}", 'ERROR')
            with self.cleanup_lock:
                self.process_results[process_id] = {
                    'status': 'error',
                    'message': f'Process monitoring failed: {e}',
                    'directive_name': process_info.get('directive_name', 'Unknown')
                }
                self._cleanup_process(process_id)

    def _read_log_file(self, log_file_path):
        """Read content from a log file"""
        try:
            if os.path.exists(log_file_path):
                with open(log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()
        except Exception as e:
            log_to_file(f"Failed to read log file {log_file_path}: {e}", 'WARNING')
        return ""

    def _read_process_result(self, result_file, return_code, stdout, stderr):
        """Read the result from the process result file"""
        try:
            if os.path.exists(result_file):
                with open(result_file, 'r') as f:
                    result = json.load(f)
                    result['return_code'] = return_code
                    return result
        except Exception as e:
            log_to_file(f"Failed to read result file: {e}", 'WARNING')

        # Fallback result if file reading failed
        return {
            'status': 'error' if return_code != 0 else 'unknown',
            'message': 'Process completed but result could not be read',
            'return_code': return_code,
            'stdout': stdout if isinstance(stdout, str) else (stdout.decode('utf-8', errors='ignore') if stdout else ''),
            'stderr': stderr if isinstance(stderr, str) else (stderr.decode('utf-8', errors='ignore') if stderr else '')
        }

    def _cleanup_process(self, process_id):
        """Clean up process resources (should be called with cleanup_lock held)"""
        if process_id in self.running_processes:
            process_info = self.running_processes[process_id]

            # Clean up temporary directory
            import shutil
            try:
                shutil.rmtree(process_info['temp_dir'])
            except Exception as e:
                log_to_file(f"Failed to clean up temp directory: {e}", 'WARNING')

            # Remove from running processes
            del self.running_processes[process_id]

    def get_process_status(self, process_id):
        """
        Get the status of a background process

        Args:
            process_id (str): Process identifier

        Returns:
            dict: Status information
        """
        with self.cleanup_lock:
            # Check if process is still running
            if process_id in self.running_processes:
                process_info = self.running_processes[process_id]
                elapsed_time = time.time() - process_info['start_time']

                return {
                    'status': 'running',
                    'process_id': process_id,
                    'directive_name': process_info['directive_name'],
                    'elapsed_time': elapsed_time,
                    'timeout': process_info['timeout']
                }

            # Check if process has completed
            if process_id in self.process_results:
                result = self.process_results[process_id].copy()
                result['status_type'] = 'completed'
                return result

            # Process not found
            return {
                'status': 'not_found',
                'process_id': process_id,
                'message': 'Process not found'
            }

    def get_process_result(self, process_id):
        """
        Get the result of a completed background process

        Args:
            process_id (str): Process identifier

        Returns:
            dict: Process result or None if not completed
        """
        with self.cleanup_lock:
            if process_id in self.process_results:
                result = self.process_results[process_id].copy()
                # Optionally remove from results after retrieval
                # del self.process_results[process_id]
                return result
            return None

    def list_running_processes(self):
        """
        List all currently running background processes

        Returns:
            list: List of running process information
        """
        with self.cleanup_lock:
            running = []
            for process_id, process_info in self.running_processes.items():
                elapsed_time = time.time() - process_info['start_time']
                running.append({
                    'process_id': process_id,
                    'directive_name': process_info['directive_name'],
                    'elapsed_time': elapsed_time,
                    'timeout': process_info['timeout']
                })
            return running

    def kill_process(self, process_id):
        """
        Kill a running background process

        Args:
            process_id (str): Process identifier

        Returns:
            bool: True if process was killed, False if not found
        """
        with self.cleanup_lock:
            if process_id in self.running_processes:
                process_info = self.running_processes[process_id]
                try:
                    process_info['process'].kill()
                    log_to_file(f"Killed background directive process: {process_id}", 'INFO')
                    return True
                except Exception as e:
                    log_to_file(f"Failed to kill process {process_id}: {e}", 'ERROR')
                    return False
            return False

    def cleanup_old_results(self, max_age_seconds=3600):
        """
        Clean up old process results to prevent memory leaks

        Args:
            max_age_seconds (int): Maximum age of results to keep (default: 1 hour)
        """
        current_time = time.time()
        with self.cleanup_lock:
            to_remove = []
            for process_id, result in self.process_results.items():
                # Add cleanup timestamp if not present
                if 'cleanup_timestamp' not in result:
                    result['cleanup_timestamp'] = current_time

                if current_time - result['cleanup_timestamp'] > max_age_seconds:
                    to_remove.append(process_id)

            for process_id in to_remove:
                del self.process_results[process_id]
                log_to_file(f"Cleaned up old process result: {process_id}", 'DEBUG')