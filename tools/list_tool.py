import os
from typing import Dict, Any, List


def list_files(directory: str = ".") -> str:
    """List all files and directories in a given directory.
    
    Args:
        directory: The path to the directory to list (default: current directory)
        
    Returns:
        A formatted string listing all files and directories
    """
    try:
        items = []
        for item in os.listdir(directory):
            item_path = os.path.join(directory, item)
            is_dir = os.path.isdir(item_path)
            items.append({
                "name": item,
                "type": "directory" if is_dir else "file",
                "path": item_path
            })
        
        # Format output
        output = f"Contents of {directory}:\n\n"
        dirs = [item for item in items if item["type"] == "directory"]
        files = [item for item in items if item["type"] == "file"]
        
        if dirs:
            output += "Directories:\n"
            for item in dirs:
                output += f"  📁 {item['name']}\n"
        
        if files:
            output += "\nFiles:\n"
            for item in files:
                output += f"  📄 {item['name']}\n"
        
        output += f"\nTotal: {len(dirs)} directories, {len(files)} files"
        return output
    except Exception as e:
        return f"Error listing {directory}: {str(e)}"

