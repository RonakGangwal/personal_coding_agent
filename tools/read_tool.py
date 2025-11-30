import os
from typing import Dict, Any


def read_file(file_path: str) -> str:
    """Read the contents of a file.
    
    Args:
        file_path: The path to the file to read
        
    Returns:
        The contents of the file as a string
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return f"Successfully read {file_path}:\n\n{content}"
    except FileNotFoundError:
        return f"Error: File not found: {file_path}"
    except Exception as e:
        return f"Error reading {file_path}: {str(e)}"

