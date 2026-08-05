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

        # Compiling the regex pattern for performance 
        self.log_pattern = re.compile(
            r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3})\s+" # 1: Timestamp
            r"(\d+)\s+"                                        # 2: PID
            r"(INFO|DEBUG|WARNING|WARN|ERROR|CRITICAL)\s+"     # 3: Level
            r"([a-zA-Z0-9\._\-]+)\s+"                          # 4: Service
            r"(?:\[.*?\]\s+)?"                                 # Request ID (Ignored)
            r"(.*)"                                            # 5: Message
        )

    def parse_file(self, file_path: str) -> List[Dict]:
        """Reads the log file and normalizes it into structured dictionaries."""
        parsed_logs = []
        current_log = None

        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                match = self.log_pattern.match(line)

                if match:
                    # If there's an existing log being built, save it before starting new ones
                    if current_log:
                        parsed_logs.append(current_log)

                    current_log = {
                        "timestamp": match.group(1),
                        "level": match.group(3),
                        "service": match.group(4),
                        "message": match.group(5).strip()
                    }
                else:
                    # If no regex match, this line is part of a multi-line stack trace 
                    if current_log:
                        current_log["message"] += f"\n{line.strip()}"
                        
            # Append the very last log in the file
            if current_log:
                parsed_logs.append(current_log)
                
        return self._chunk_text(parsed_logs)

    def _chunk_text(self, parsed_logs: List[Dict]) -> List[Dict]:
        """Applies sliding window chunking over the parsed log strings."""
        # Convert structured logs into a single continuous string format for the LLM
        full_text_stream = [
            f"[{log['timestamp']}] {log['level']} {log['service']}: {log['message']}"
            for log in parsed_logs
        ]
        combined_text = " ".join(full_text_stream)
        words = combined_text.split()

        chunks = []
        # Sliding window logic using step size (chunk_size - overlap)
        step = self.chunk_size - self.overlap

        for i in range(0, len(words), step):
            chunk_words = words[i:i + self.chunk_size]
            chunk_text = " ".join(chunk_words)  # Added space here

            chunks.append({
                "chunk_id": f"chunk_{i // step}",
                "text": chunk_text,
                "metadata": {"source": "openstack_cluster"}
            })

            # Stop if we've reached the end of the words list
            if i + self.chunk_size >= len(words):
                break
                
        return chunks