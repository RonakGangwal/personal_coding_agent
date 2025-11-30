import os
from typing import Dict, Any


def edit_file(file_path: str, old_content: str, new_content: str) -> str:
    """Edit a file by replacing old content with new content.
    
    Args:
        file_path: The path to the file to edit
        old_content: The content to be replaced
        new_content: The new content to insert
        
    Returns:
        Success or error message
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            current_content = f.read()
        
        if old_content not in current_content:
            return f"Error: Could not find the specified content in {file_path}"
        
        updated_content = current_content.replace(old_content, new_content)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        return f"Successfully edited {file_path}"
    except FileNotFoundError:
        return f"Error: File not found: {file_path}"
    except Exception as e:
        return f"Error editing {file_path}: {str(e)}"


