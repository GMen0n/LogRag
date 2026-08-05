import re
from typing import List, Dict

class OpenStackLogIngestor:
    """
    Ingests raw OpenStack logs, parses them via regex, and chunks them using a
    sliding window for RAG vector embedding.
    """
    def __init__(self, chunk_size: int = 300, overlap: int = 50):
        self.chunk_size = chunk_size
        self.overlap = overlap

        # Enhanced Regex Pattern to handle optional Loghub filename prefixes
        self.log_pattern = re.compile(
            r"^(?:(?!\d{4}-\d{2}-\d{2})\S+\s+)?"                # Optional prefix (e.g., nova-api.log.1.2017-...)
            r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3})\s+"  # Group 1: Timestamp
            r"(\d+)\s+"                                         # Group 2: PID
            r"(INFO|DEBUG|WARNING|WARN|ERROR|CRITICAL)\s+"      # Group 3: Level
            r"([a-zA-Z0-9\._\-]+)\s+"                           # Group 4: Service
            r"(?:\[.*?\]\s+)?"                                  # Request/Context ID (Ignored)
            r"(.*)"                                             # Group 5: Message
        )

    def parse_file(self, file_path: str) -> List[Dict]:
        """Reads the log file line by line and normalizes it into structured dictionaries."""
        parsed_logs = []
        current_log = None

        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                line_str = line.strip()
                if not line_str:
                    continue

                match = self.log_pattern.match(line_str)

                if match:
                    # Save the previous log entry if one was being processed
                    if current_log:
                        parsed_logs.append(current_log)

                    current_log = {
                        "timestamp": match.group(1),
                        "pid": match.group(2),
                        "level": match.group(3),
                        "service": match.group(4),
                        "message": match.group(5).strip()
                    }
                else:
                    # If regex doesn't match, this line is a multi-line stack trace/continuation
                    if current_log:
                        current_log["message"] += f"\n{line_str}"

            # Append the final log entry from the loop
            if current_log:
                parsed_logs.append(current_log)

        return self._chunk_text(parsed_logs)

    def parse_string(self, log_content: str) -> List[Dict]:
        """Utility method to parse log content directly from a string buffer."""
        parsed_logs = []
        current_log = None

        for line in log_content.strip().splitlines():
            line_str = line.strip()
            if not line_str:
                continue

            match = self.log_pattern.match(line_str)

            if match:
                if current_log:
                    parsed_logs.append(current_log)

                current_log = {
                    "timestamp": match.group(1),
                    "pid": match.group(2),
                    "level": match.group(3),
                    "service": match.group(4),
                    "message": match.group(5).strip()
                }
            else:
                if current_log:
                    current_log["message"] += f"\n{line_str}"

        if current_log:
            parsed_logs.append(current_log)

        return self._chunk_text(parsed_logs)

    def _chunk_text(self, parsed_logs: List[Dict]) -> List[Dict]:
        """Applies sliding window chunking over parsed log entries."""
        if not parsed_logs:
            return []

        # Reconstruct structured logs into unified context lines
        full_text_stream = [
            f"[{log['timestamp']}] [{log['level']}] [{log['service']}]: {log['message']}"
            for log in parsed_logs
        ]
        
        combined_text = " ".join(full_text_stream)
        words = combined_text.split()

        chunks = []
        step = max(1, self.chunk_size - self.overlap)

        for i in range(0, len(words), step):
            chunk_words = words[i:i + self.chunk_size]
            chunk_text = " ".join(chunk_words)  # Space preserved between words

            chunks.append({
                "chunk_id": f"chunk_{i // step}",
                "text": chunk_text,
                "metadata": {
                    "source": "openstack_cluster",
                    "word_count": len(chunk_words)
                }
            })

            if i + self.chunk_size >= len(words):
                break

        return chunks