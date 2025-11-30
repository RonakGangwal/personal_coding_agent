# AI Coding Assistant

A modern, interactive AI coding assistant built with Streamlit and Anthropic's Claude API. This assistant can help you with coding tasks by reading, writing, editing, and managing files in your project.

## Features

- 🤖 **Interactive Chat Interface**: Natural conversation with Claude AI models
- 📁 **File Operations**: Read, write, edit, and list files directly through the chat
- 🎨 **Modern UI**: Clean, responsive interface with code syntax highlighting
- ⚙️ **Configurable Settings**: Adjust model, temperature, and system prompts
- 📊 **Tool Usage Tracking**: See what tools the assistant uses during conversations
- 🔍 **File Browser**: Browse your project files in the sidebar

## Installation

1. **Clone or navigate to this repository**

2. **Create a virtual environment (recommended)**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up your API key**
   
   You can either:
   - Set it in the UI sidebar (stored in session)
   - Set it as an environment variable:
     ```bash
     export ANTHROPIC_API_KEY="your-api-key-here"
     ```
   - Or create a `.env` file:
     ```
     ANTHROPIC_API_KEY=your-api-key-here
     ```

## Usage

1. **Start the application**
   ```bash
   streamlit run main.py
   ```

2. **Open your browser**
   - The app will automatically open at `http://localhost:8501`
   - If not, navigate to the URL shown in the terminal

3. **Configure settings (optional)**
   - Enter your Anthropic API key in the sidebar
   - Select your preferred Claude model
   - Adjust temperature for creativity vs. focus
   - Customize the system prompt

4. **Start chatting!**
   - Ask questions about coding
   - Request file operations (read, write, edit, list)
   - Get help with your projects

## Example Queries

- "List all Python files in the current directory"
- "Read the contents of main.py"
- "Create a new file called test.py with a hello world function"
- "Edit main.py to add error handling"
- "What does this code do?" (after sharing code)

## Available Tools

The assistant has access to these tools:

1. **read_file**: Read the contents of any file
2. **write_file**: Write content to a file (creates if doesn't exist)
3. **edit_file**: Edit files by replacing old content with new content
4. **list_files**: List all files and directories in a directory

## Models Supported

- Claude 3.5 Sonnet (recommended)
- Claude 3.5 Haiku
- Claude 3 Opus
- Claude 3 Sonnet
- Claude 3 Haiku

## Project Structure

```
personal_coding_agent/
├── main.py              # Main Streamlit application
├── run.py               # (Optional) CLI runner
├── requirements.txt     # Python dependencies
├── config/             # Configuration files
├── prompt_store/       # System prompts
└── tools/              # Tool implementations
```

## Troubleshooting

**Issue**: "Anthropic SDK not installed"
- **Solution**: Run `pip install anthropic`

**Issue**: "API key not set"
- **Solution**: Add your API key in the sidebar or set `ANTHROPIC_API_KEY` environment variable

**Issue**: Port already in use
- **Solution**: Use `streamlit run main.py --server.port 8502` to use a different port

## License

This project is open source and available for personal and commercial use.

## Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.

