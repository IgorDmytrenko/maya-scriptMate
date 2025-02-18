import socket
from datetime import datetime
import getpass
import textwrap
from crudo_sm.utils import file_utils


class ScriptManagerLogger:
    _instance = None

    @staticmethod
    def get_instance(config=None):
        if ScriptManagerLogger._instance is None:
            if config is None:
                raise ValueError(
                    "Logger instance is not initialized and no config provided."
                )
            ScriptManagerLogger._instance = ScriptManagerLogger(config)
        return ScriptManagerLogger._instance

    def __init__(self, config):
        if ScriptManagerLogger._instance is not None:
            raise RuntimeError("Use `get_instance` to access the ScriptManagerLogger.")

        self.config = config
        self.enable_logging = self.config.get_core_param("log", "state")
        self.log_file_path = self.config.get_core_param("log", "path")
        self.logs = []
        self.error_buffer = []  # For error printing into maya console
        self.finalized = False  # Ensure logs are written only once

        if self.enable_logging:
            self.username = getpass.getuser()
            self.hostname = socket.gethostname()
            self.local_ip = self.get_local_ip()
            self.start_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def log_module(self, source, module_name, has_unsafe_imports, reason, error):
        """
        Add a module entry to the logs.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = (source, module_name, has_unsafe_imports, reason, error, timestamp)

        if self.enable_logging:
            self.logs.append(entry)  # For file logging

        if error != "-":  # If there's an error
            self.error_buffer.append(entry)  # For immediate display
            # self.print_error_buffer()  # Print immediately
            # self.error_buffer.clear()  # Clear only the error buffer

    def get_local_ip(self):
        try:
            # Use a fake connection to identify the real network interface
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                # Connect to a non-routable address (doesn't send data)
                s.connect(("192.168.1.1", 80))
                return s.getsockname()[0]
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    def clear_logs(self):
        """Clear log from memory after debugging."""
        self.error_buffer.clear()
        self.logs.clear()

    def print_error_buffer(self):
        """Print current error buffer to Maya console with appropriate formatting."""
        if self.error_buffer:
            # Format specifically for console output
            formatted_log = self.format_logs(self.error_buffer, for_console=True) + "\n"
            print(f"\nScriptMate: RUNTIME ERROR>\n\t{formatted_log}\n")
        self.error_buffer.clear()

    def write_logs(self):
        # print(f"write_logs called, enable_logging: {self.enable_logging}, logs: {self.logs}")  # Debug
        if self.enable_logging and not self.finalized and self.logs:
            try:
                log_file_path = file_utils.path_existance(self.log_file_path)
                with open(log_file_path, "a") as log_file:
                    log_file.write(f"Logging started: {self.start_timestamp}\n")
                    log_file.write(f"Username: {self.username}\n")
                    log_file.write(f"Hostname: {self.hostname}\n")
                    log_file.write(f"Local IP: {self.local_ip}\n\n")

                    # Format and write the logs
                    log_file.write(self.format_logs(self.logs) + "\n")
                    log_file.write(
                        f"Logging ended: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                    )

                self.finalized = True
            except Exception as e:
                print(f"Error writing logs: {e}")  # Debug

    def format_logs(self, log_entries, for_console=False):
        """
        Format logs with consistent column widths and wrapping for both console and file output.
        Maintains proper formatting for multi-line content and error messages.
        """
        if not log_entries:
            return ""

        # Define our columns and their ideal widths
        column_config = [
            ("Source", max(8, 8)),
            ("Module", max(40, 10)),
            ("Has Unsafe Imports", max(45, 15)),
            ("Reason", max(35, 10)),
            ("Errors", max(60, 15)),
            ("Timestamp", max(20, 19))
        ]

        headers = [col[0] for col in column_config]
        widths = [col[1] for col in column_config]

        def wrap_text(text, width, column_type='text'):
            """
            Intelligently wrap text based on content type.
            For imports: Split on semicolons and maintain structure
            For errors: Preserve indentation and formatting
            For regular text: Word wrap at spaces
            """
            if not text or text == '-':
                return [text]

            if column_type == 'imports':
                # Handle import statements with careful semicolon splitting
                # print("text check: ", text)
                parts = text.split('; ')
                # print("CHECK: ", parts)
                lines = []
                current_line = []
                current_length = 0

                for part in parts:
                    subparts = part.split(', ')
                    for subpart in subparts:
                        if '.py:' in subpart and current_line:
                            lines.append(' '.join(current_line))
                            current_line = [subpart]
                            current_length = len(subpart)
                        elif current_length + len(subpart) + 2 <= width:
                            current_line.append(subpart)
                            current_length += len(subpart) + 2
                        else:
                            if current_line:
                                lines.append(', '.join(current_line))
                            current_line = [subpart]
                            current_length = len(subpart)

                if current_line:
                    lines.append(' '.join(current_line))
                return lines or ['-']

            elif column_type == 'error':
                # Preserve error message formatting
                lines = text.split('\n')
                wrapped_lines = []
                for line in lines:
                    # Preserve indentation
                    indent = len(line) - len(line.lstrip())
                    indent_str = ' ' * min(indent, width - 1)
                    available_width = max(1, width - len(indent_str))
                    content = line.lstrip()

                    # Wrap content if too long
                    if len(line) > width:
                        # Split content to fit width while accounting for indentation
                        available_width = width - indent
                        wrapped = textwrap.wrap(content, available_width) if available_width > 0 else [content]
                        # wrapped = content
                        wrapped_lines.extend(indent_str + line for line in wrapped)
                    else:
                        wrapped_lines.append(line)
                return wrapped_lines or ['-']

            else:  # Regular text wrapping
                if len(text) <= width:
                    return [text]

                words = text.split()
                lines = []
                current_line = []
                current_length = 0

                for word in words:
                    if current_length + len(word) + 1 <= width:
                        current_line.append(word)
                        current_length += len(word) + 1
                    else:
                        if current_line:
                            lines.append(' '.join(current_line))
                        current_line = [word]
                        current_length = len(word)

                if current_line:
                    lines.append(' '.join(current_line))
                return lines or ['-']

        # Process each row to handle multi-line content
        formatted_rows = []

        for entry in log_entries:
            # Process each column in the row
            row_parts = {}
            for i, content in enumerate(entry):
                content_str = str(content)
                if i == 2:  # Has Unsafe Imports
                    row_parts[i] = wrap_text(content_str, widths[i], 'imports')
                elif i == 4:  # Errors
                    row_parts[i] = wrap_text(content_str, widths[i], 'error')
                else:
                    row_parts[i] = wrap_text(content_str, widths[i], 'text')

            # Find how many lines we need for this row
            max_lines = max(len(lines) for lines in row_parts.values())

            # Build each line of the row
            for line_num in range(max_lines):
                row = []
                for col in range(len(headers)):
                    lines = row_parts[col]
                    if line_num < len(lines):
                        content = lines[line_num]
                        row.append(f"{content:<{widths[col]}}")
                    else:
                        row.append(" " * widths[col])

                if line_num == 0:
                    formatted_rows.append(" | ".join(row))
                else:
                    # For continuation lines, clear first two columns
                    row[0] = " " * widths[0]  # Clear Source
                    row[1] = " " * widths[1]  # Clear Module
                    formatted_rows.append(" | ".join(row))

        # Create header and separator
        header = " | ".join(f"{h:<{w}}" for h, w in zip(headers, widths))
        separator = "-+-".join("-" * w for w in widths)

        return f"{header}\n{separator}\n" + "\n".join(formatted_rows)

    def debug_state(self, runtime_err=True, clear_after=True, finalize_log=False):
        """
        Print the current state of the logger instance for debugging.
        """
        if not runtime_err:
            print("=== Logger Debug State ===")
            print(f"Enable Logging: {self.enable_logging}")
            print(f"Log File Path: {self.log_file_path}")
            print(f"Finalized: {self.finalized}")
            print(f"Start Timestamp: {self.start_timestamp}")
            print(f"Username: {self.username}")
            print(f"Hostname: {self.hostname}")
            print(f"Local IP: {self.local_ip}")
            print(f"Logs Stored in Memory: {self.logs}")
            print("==========================")
        else:
            print(f"\nScriptMate: RUNTIME ERROR>\n\t{self.format_logs(self.logs)}\n")

        if clear_after and finalize_log:
            self.clear_logs()
