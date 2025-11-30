from tools.write_tool import write_file
from tools.list_tool import list_files
from tools.read_tool import read_file
from tools.edit_tool import edit_file

# Tool definitions for the API
TOOLS = [
    {
        "name": "create_tool",
        "description": "Create a file with content",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "content": {"type": "string"}
            },
            "required": ["path"]
        }
    },
    {
        "name": "list_tool",
        "description": "List files in a directory",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"}
            }
        }
    },
    {
        "name": "read_tool",
        "description": "Read content of a file",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"}
            },
            "required": ["path"]
        }
    },
    {
        "name": "edit_tool",
        "description": "Find and replace text in a file",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "old_str": {"type": "string"},
                "new_str": {"type": "string"}
            },
            "required": ["path", "old_str", "new_str"]
        }
    }
]

# Mapping from tool names to their actual function implementations
TOOL_FUNCTIONS = {
    "create_tool": lambda args: write_file(args.get("path", ""), args.get("content", "")),
    "list_tool": lambda args: list_files(args.get("path", ".")),
    "read_tool": lambda args: read_file(args.get("path", "")),
    "edit_tool": lambda args: edit_file(args.get("path", ""), args.get("old_str", ""), args.get("new_str", ""))  # Note: edit_file uses old_content/new_content but API uses old_str/new_str
}