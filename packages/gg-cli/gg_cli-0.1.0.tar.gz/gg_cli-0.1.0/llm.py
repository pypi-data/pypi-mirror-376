import json
import os
import sys
import subprocess
import platform
import time
import traceback
from typing import List, Dict, Any, Tuple
from warnings import warn
import locale
import threading
import queue

from openai import OpenAI

class LLM:
    def __init__(self, client:OpenAI, model:str, temperature:float, sys_prompt:str):
        self.cli=client
        self.mod=model
        self.tem=temperature
        self.reset_context(sys_prompt)
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": f'terminal',
                    "description": f'Execute terminal commands in the persistent shell',
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {
                                "type": "string",
                                "description": "the command string to execute", 
                            },
                            "timeout": {
                                "type": "float",
                                "description": "set a proper timeout so that the command finishes within it.", 
                            }
                        },
                        "required": ["command"],
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": f'reset',
                    "description": f'Reset/restart the shell process',
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": [],
                    }
                }
            }
        ]
        self.marker = "___COMMAND_COMPLETED_MARKER___"

        # Platform detection and shell setup
        self.platform = platform.system().lower()
        self.shell_process = None
        
        # Thread-safe queues for stdout and stderr
        self.stdout_queue = queue.Queue()
        self.stderr_queue = queue.Queue()
        
        # Thread management
        self.stdout_thread = None
        self.stderr_thread = None
        self.stop_threads = threading.Event()
        
        # Setup shell based on platform
        if self.platform == "windows":
            self.shell_cmd = ["powershell", "-NoProfile", "-NoExit"]
            self.shell_name = "PowerShell"
        elif self.platform == "linux":
            self.shell_cmd = ["bash", "-i"]
            self.shell_name = "Bash"
        elif self.platform == "darwin":
            self.shell_cmd = ["zsh", "-i"]
            self.shell_name = "Zsh"
        else:
            self.shell_cmd = ["bash", "-i"]
            self.shell_name = "Bash"

        print(f'{self.shell_cmd = }')
        
        self.reset_shell()

    def reset_context(self, sys_prompt:str):
        self.spp=sys_prompt if sys_prompt.strip() else f"""\
You are a helpful assistant to the user.

The os is: {platform.system()}
The architecture of chip is: {platform.machine()}
The conversation starts at: {time.strftime('%Y-%m-%d %H:%M:%S')}

1. Try not to execute commands that run forever or to enter new shell environment such as wsl, bash, or powershell. If the user asks you to do so, remind the user before executing.
2. Do not use markdown. Use plain text as your output instead. 
"""
        self.msg=[
            {'role':'system','content':self.spp}
        ]
    
    def _read_stdout(self):
        """Background thread to continuously read stdout"""
        while not self.stop_threads.is_set() and self.shell_process:
            try:
                if self.shell_process and self.shell_process.stdout:
                    line = self.shell_process.stdout.readline()
                    if line:
                        self.stdout_queue.put(line.strip())
                    else:
                        # Process ended
                        break
                else:
                    break
            except Exception as e:
                print(f"Error reading stdout: {e}")
                break
            time.sleep(0.01)  # Small delay to prevent busy waiting
    
    def _read_stderr(self):
        """Background thread to continuously read stderr"""
        while not self.stop_threads.is_set() and self.shell_process:
            try:
                if self.shell_process and self.shell_process.stderr:
                    line = self.shell_process.stderr.readline()
                    # Print stderr output in red color using ANSI escape codes
                    # \033[91m = red foreground color, \033[0m = reset to default color
                    print(f"\033[91mstderr: \033[0m{line}")
                    if line:
                        self.stderr_queue.put(line.strip())
                    else:
                        # Process ended
                        break
                else:
                    break
            except Exception as e:
                print(f"Error reading stderr: {e}")
                break
            time.sleep(0.01)  # Small delay to prevent busy waiting
        
        

    def reset_shell(self) -> Dict[str, Any]:
        """Reset/restart the shell process"""
        print("Resetting shell process...")
        
        # Stop existing threads
        self.stop_threads.set()
        # Terminate existing process
        if self.shell_process:
            self.shell_process.terminate()
            self.shell_process.wait(1.0)
            try:
                self.shell_process.kill()
            except:
                pass
        
        # Clear queues
        while not self.stdout_queue.empty():
            try:
                self.stdout_queue.get_nowait()
            except queue.Empty:
                break
        while not self.stderr_queue.empty():
            try:
                self.stderr_queue.get_nowait()
            except queue.Empty:
                break
        
        # Reset stop event
        self.stop_threads.clear()
        
        # Start new process
        try:
            self.shell_process = subprocess.Popen(
                self.shell_cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                encoding=locale.getpreferredencoding(),
            )
            print(f"Started {self.shell_name} shell process (PID: {self.shell_process.pid})")
            
            # Start background threads for reading stdout and stderr
            self.stdout_thread = threading.Thread(target=self._read_stdout, daemon=True)
            self.stderr_thread = threading.Thread(target=self._read_stderr, daemon=True)
            self.stdout_thread.start()
            self.stderr_thread.start()
            
        except Exception as e:
            print(f"Failed to start shell: {e}")
            self.shell_process = None
        
        return {
            "action": "reset",
            "success": self.shell_process is not None,
            "shell_name": self.shell_name,
            "message": f"Shell process {'restarted successfully' if self.shell_process else 'failed to restart'}"
        }

    def run_command(self, command: str, timeout:float=5.0) -> Dict[str, Any]:
        print(f"Approve running command with {timeout = }s: \n{command}")
        while True:
            approval = input("[y], n: ")
            approval = approval.lower().strip()

            if approval == "y" or approval == "":
                if not self.shell_process:
                    print("No shell process available, starting new one...")
                    self.reset_shell()
                    if not self.shell_process:
                        return {
                            "command": command,
                            "approved": True,
                            "stdout": "",
                            "stderr": "Failed to start shell process",
                            "returncode": -1,
                        }

                try:
                    self.shell_process.stdin.write(f"\n{command};echo {self.marker};\n")
                    self.shell_process.stdin.flush()
                    
                    # Read output from queues until we find the marker
                    stdout_lines = []
                    stderr_lines = []
                    
                    start_time = time.time()
                    last_time = time.time()
                    brk = 0
                    
                    while time.time() - start_time <= timeout and time.time() - last_time <= 2.0:
                        try:
                            stdout_line = self.stdout_queue.get(timeout=0.1).replace(f';echo {self.marker};','')
                            if stdout_line == self.marker:
                                brk=1
                                break
                            print(stdout_line)
                            last_time = time.time()
                            stdout_lines.append(stdout_line)
                        except queue.Empty:
                            pass

                        try:
                            stderr_line = self.stderr_queue.get(timeout=0.01)
                            stderr_lines.append(stderr_line)
                        except queue.Empty:
                            pass

                    
                    if brk:
                        result = {
                            "command": command,
                            "approved": True,
                            "stdout": '\n'.join(stdout_lines).strip(),
                            "stderr": '\n'.join(stderr_lines).strip(),
                            "returncode": 0,
                            'msg':'successful',
                        }
                    else:
                        result = {
                            "command": command,
                            "approved": True,
                            "stdout": '\n'.join(stdout_lines).strip().replace(f'echo {self.marker};',''),
                            "stderr": '\n'.join(stderr_lines).strip(),
                            "returncode": 0,
                            'msg':'Command timed out. The shell may stuck. Remind the user the shell may have stuck. Therefore, you following commands may not execute at all. ',
                        }
                    return result
                    
                except Exception as e:
                    result = {
                        "command": command,
                        "approved": True,
                        "stdout": "",
                        "stderr": "",
                        "returncode": -1,
                        'msg':f'Error executing command: {traceback.format_exc()}',
                    }
                    return result

            if approval == "n":
                result = {
                    "command": command,
                    "approved": False,
                    "stdout": "",
                    "stderr": "",
                    "returncode": None,
                    'msg':'The user rejects your command',
                }
                return result

            print(f"Please type in y or n")

        raise

    def chat(self, prompt:str):
        if prompt:
            self.msg.append({
                'role':'user',
                'content':prompt,
            })

        while self.msg[-1]['role'] !='assistant':
            self.chat_one_round()
            if self.msg and self.msg[-1]['role']=='tool':
                inj = input('(inject instruction, skip by pressing enter)\ni>>')
                if inj.strip():
                    self.msg.append({
                        'role':'user','content':inj
                    })

    def chat_one_round(self):
        stream = self.cli.chat.completions.create(
            model=self.mod,
            messages=self.msg,
            temperature=self.tem,
            stream=True,
            tools=self.tools,
        )
        r,c=[],[]
        tool_calls = {}
        for chunk in stream:  # type: ignore
            delta = chunk.choices[0].delta
            if delta.tool_calls:
                for dtc in delta.tool_calls:
                    if dtc.index not in tool_calls:
                        tool_calls[dtc.index]=dtc
                    elif hasattr(dtc.function,'arguments') and dtc.function.arguments:
                        tool_calls[dtc.index].function.arguments+=dtc.function.arguments

            if not hasattr(chunk,'choices') or not chunk.choices or not hasattr(chunk.choices[0],'delta'):
                continue

            # Print reasoning content in yellow
            if hasattr(delta,'reasoning_content') and delta.reasoning_content:
                print(f"\033[33m{delta.reasoning_content}\033[0m",end='')
                r.append(delta.reasoning_content)
            # Print regular content in green
            if hasattr(delta,'content') and delta.content:
                print(f"\033[32m{delta.content}\033[0m", end="")
                c.append(delta.content)

        print()
        rep={
            "role":"assistant",
            "content":"".join(c),
        }
        if len(tool_calls)>0:
            rep['tool_calls']=list(tool_calls.values())
        self.msg.append(rep)

        for index,tc in tool_calls.items():
            f = tc.function
            args=json.loads(f.arguments)
            name=f.name
            if name=='terminal':
                result = self.run_command(**args)
                # if result['approved']:
                #     print('stdout:',result['stdout'])
                #     print('stderr:',result['stderr'])

                self.msg.append({
                    "role":"tool",
                    "content":json.dumps(result,indent=0),
                    "tool_call_id":tc.id,
                })

            elif name=='reset':
                result = self.reset_shell()
                print(f"Reset result: {result['message']}")
                
                self.msg.append({
                    "role":"tool",
                    "content":json.dumps(result,indent=0),
                    "tool_call_id":tc.id,
                })

            else:
                warn(f"The LLM outputs an unknown tool name: {name}")

    def __del__(self):
        """Cleanup method to properly close the shell process and threads"""
        # Stop threads
        if hasattr(self, 'stop_threads'):
            self.stop_threads.set()
        
        # Terminate shell process
        if hasattr(self, 'shell_process') and self.shell_process:
            try:
                self.shell_process.terminate()
            except:
                try:
                    self.shell_process.kill()
                except:
                    pass

