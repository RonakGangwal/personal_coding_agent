import os
from typing import Dict, Any


def write_file(file_path: str, content: str) -> str:
    """Write content to a file. Creates the file if it doesn't exist.
    
    Args:
        file_path: The path to the file to write
        content: The content to write to the file
        
    Returns:
        Success or error message
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True) if os.path.dirname(file_path) else None
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Successfully wrote to {file_path}"
    except Exception as e:
        return f"Error writing to {file_path}: {str(e)}"

