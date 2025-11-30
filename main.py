import os
import json
import logging
import sys
import hashlib
from io import StringIO
from typing import List, Dict, Any
from datetime import datetime
import uuid
import streamlit as st

from run import run_agent_anthropic, run_agent_anthropic_stream

# Configure logger to capture output
class StreamlitLogger:
    def __init__(self, log_placeholder=None):
        self.logs = []
        self.log_placeholder = log_placeholder
    
    def debug(self, msg):
        self.logs.append(("DEBUG", msg))
    
    def info(self, msg):
        self.logs.append(("INFO", msg))
        if self.log_placeholder:
            # Display all INFO logs in the log area
            info_logs = [msg for level, msg in self.logs if level == "INFO"]
            if info_logs:
                log_text = "\n".join(info_logs)
                self.log_placeholder.text(log_text)
        else:
            st.info(msg)
    
    def error(self, msg, exc_info=False):
        self.logs.append(("ERROR", msg))
        if self.log_placeholder:
            all_logs = [msg for level, msg in self.logs if level in ["INFO", "ERROR"]]
            if all_logs:
                log_text = "\n".join(all_logs)
                self.log_placeholder.text(log_text)
        else:
            st.error(msg)
    
    def warning(self, msg):
        self.logs.append(("WARNING", msg))
        if self.log_placeholder:
            all_logs = [msg for level, msg in self.logs if level in ["INFO", "WARNING"]]
            if all_logs:
                log_text = "\n".join(all_logs)
                self.log_placeholder.text(log_text)
        else:
            st.warning(msg)


def _ensure_session_state() -> None:
    """Initialize Streamlit session state for the chat UI."""
    if "chats" not in st.session_state:
        st.session_state.chats: Dict[str, Dict[str, Any]] = {}
    
    if "current_chat_id" not in st.session_state:
        # Create first chat if none exists
        if not st.session_state.chats:
            chat_id = str(uuid.uuid4())
            st.session_state.chats[chat_id] = {
                "messages": [],
                "title": "New Chat",
                "created_at": datetime.now().isoformat()
            }
            st.session_state.current_chat_id = chat_id
        else:
            # Use the first chat
            st.session_state.current_chat_id = list(st.session_state.chats.keys())[0]


def get_current_messages() -> List[Dict[str, Any]]:
    """Get messages for the current chat."""
    if st.session_state.current_chat_id in st.session_state.chats:
        return st.session_state.chats[st.session_state.current_chat_id]["messages"]
    return []


def set_current_messages(messages: List[Dict[str, Any]]) -> None:
    """Set messages for the current chat."""
    if st.session_state.current_chat_id in st.session_state.chats:
        st.session_state.chats[st.session_state.current_chat_id]["messages"] = messages


def create_new_chat() -> str:
    """Create a new chat and return its ID."""
    chat_id = str(uuid.uuid4())
    st.session_state.chats[chat_id] = {
        "messages": [],
        "title": "New Chat",
        "created_at": datetime.now().isoformat()
    }
    st.session_state.current_chat_id = chat_id
    return chat_id


def update_chat_title(chat_id: str, title: str) -> None:
    """Update the title of a chat."""
    if chat_id in st.session_state.chats:
        st.session_state.chats[chat_id]["title"] = title


def get_chat_title(chat_id: str) -> str:
    """Get the title of a chat, or generate one from first message."""
    if chat_id not in st.session_state.chats:
        return "Unknown Chat"
    
    chat = st.session_state.chats[chat_id]
    title = chat.get("title", "New Chat")
    
    # If title is still "New Chat" and there are messages, generate title from first user message
    if title == "New Chat" and chat.get("messages"):
        for msg in chat["messages"]:
            if msg.get("role") == "user":
                content = msg.get("content", "")
                if isinstance(content, str) and content:
                    # Use first 50 chars as title
                    title = content[:50] + ("..." if len(content) > 50 else "")
                    update_chat_title(chat_id, title)
                break
    
    return title


def format_tool_usage(tool_name: str, args: Dict[str, Any]) -> str:
    """Format tool usage for display."""
    args_str = ", ".join([f"{k}={v}" for k, v in args.items()])
    return f"🔧 {tool_name}({args_str})"


def main() -> None:
    _ensure_session_state()

    st.set_page_config(
        page_title="Ronak's AI Coding Assistant",
        page_icon="💻",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    
    # ChatGPT-like clean styling
    st.markdown("""
    <style>
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        max-width: 900px;
    }
    
    /* Hide Streamlit branding but keep sidebar toggle */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    /* Don't hide header completely - sidebar toggle needs it */
    header button[data-testid="baseButton-header"] {
        visibility: visible !important;
    }
    
    /* Chat message styling - clean and minimal */
    .stChatMessage {
        padding: 1.25rem 0;
    }
    
    /* Code block styling */
    .stCodeBlock {
        border-radius: 4px;
        margin: 0.5rem 0;
    }
    
    /* Clean input area */
    .stChatInput {
        position: sticky;
        bottom: 0;
        padding: 1rem 0;
    }
    
    /* Sidebar styling - ensure it's visible and properly styled */
    section[data-testid="stSidebar"],
    [data-testid="stSidebar"] {
        display: block !important;
        visibility: visible !important;
        background-color: #171717 !important;
    }
    
    [data-testid="stSidebar"] > div {
        visibility: visible !important;
        display: block !important;
    }
    
    /* Ensure sidebar content is visible */
    [data-testid="stSidebar"] .element-container {
        visibility: visible !important;
    }
    
    /* Button styling - remove red colors */
    .stButton > button {
        background-color: transparent;
        color: #ffffff;
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 6px;
        padding: 0.5rem 1rem;
        transition: background-color 0.2s;
    }
    
    .stButton > button:hover {
        background-color: rgba(255, 255, 255, 0.1);
    }
    
    
    /* Primary button - no red */
    .stButton > button[kind="primary"] {
        background-color: rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    .stButton > button[kind="primary"]:hover {
        background-color: rgba(255, 255, 255, 0.15);
    }
    
    /* Remove any red error colors */
    .stAlert {
        background-color: rgba(255, 255, 255, 0.05);
        border-left: 3px solid #4a9eff;
    }
    
    /* Clean title */
    h1, h2, h3 {
        font-weight: 500;
        letter-spacing: -0.01em;
    }
    </style>
    """, unsafe_allow_html=True)

    # Sidebar with chat history - ensure it's always rendered
    with st.sidebar:
        # Simple "New chat" option
        if st.button("New chat", key="new_chat", use_container_width=True):
            create_new_chat()
            st.rerun()
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Chat History section
        st.markdown("**Chat History**")
        
        # Display chat list
        if st.session_state.chats:
            # Sort chats by creation time (newest first)
            sorted_chats = sorted(
                st.session_state.chats.items(),
                key=lambda x: x[1].get("created_at", ""),
                reverse=True
            )
            
            for chat_id, chat_data in sorted_chats:
                title = get_chat_title(chat_id)
                is_active = chat_id == st.session_state.current_chat_id
                
                # Use button to switch chats
                if st.button(
                    title,
                    key=f"chat_{chat_id}",
                    use_container_width=True,
                    type="primary" if is_active else "secondary"
                ):
                    if chat_id != st.session_state.current_chat_id:
                        st.session_state.current_chat_id = chat_id
                        st.rerun()
        else:
            st.caption("No chats yet")

    # Get current chat messages
    current_messages = get_current_messages()

    # Main chat interface - ChatGPT-like minimal
    if not current_messages:
        st.markdown("""
        <div style='text-align: center; padding: 4rem 0 2rem 0;'>
            <h1 style='font-size: 2rem; font-weight: 500; margin-bottom: 0.5rem; color: #ffffff;'>Ronak's AI Coding Assistant</h1>
            <p style='color: #888; font-size: 0.95rem; margin-top: 0.5rem;'>What are you working on?</p>
        </div>
        """, unsafe_allow_html=True)

    # Display chat messages
    for message in current_messages:
        role = message.get("role", "user")
        content = message.get("content", "")
        tool_usage = message.get("tool_usage", [])
        token_usage = message.get("token_usage", {})
        
        with st.chat_message(role):
            # Display message content
            if isinstance(content, list):
                # Handle content blocks
                for block in content:
                    if isinstance(block, dict):
                        if block.get("type") == "text":
                            st.markdown(block.get("text", ""))
                        elif block.get("type") == "tool_use":
                            st.markdown(f"Using tool: `{block.get('name', 'unknown')}`")
                    else:
                        st.markdown(str(block))
            else:
                st.markdown(content)
            
            # Show tool usage if any (collapsed)
            if tool_usage:
                with st.expander(f"Tools Used ({len(tool_usage)})", expanded=False):
                    for tool in tool_usage:
                        tool_name = tool.get("name", "unknown")
                        tool_args = tool.get("args", {})
                        args_str = ", ".join([f"`{k}`=`{v}`" for k, v in tool_args.items()])
                        st.markdown(f"**{tool_name}**({args_str})")
            
            # Show token usage for assistant messages (collapsed)
            if role == "assistant" and token_usage:
                per_iteration = token_usage.get("per_iteration", [])
                total = token_usage.get("total", {})
                
                if per_iteration:
                    with st.expander("Token Usage", expanded=False):
                        for iter_info in per_iteration:
                            st.text(f"Iteration {iter_info['iteration']}: {iter_info['input']} in / {iter_info['output']} out")
                        if len(per_iteration) > 1:
                            st.markdown("---")
                            st.text(f"**Total**: {total.get('input', 0)} in / {total.get('output', 0)} out")
                elif total:
                    with st.expander("Token Usage", expanded=False):
                        st.text(f"Total: {total.get('input', 0)} in / {total.get('output', 0)} out")

    # Chat input
    user_input = st.chat_input("Message...")

    if user_input:
        # Update chat title if this is the first message
        if not current_messages:
            # Generate title from first message
            title = user_input[:50] + ("..." if len(user_input) > 50 else "")
            update_chat_title(st.session_state.current_chat_id, title)
        
        # Add user message
        current_messages.append({
            "role": "user",
            "content": user_input
        })
        set_current_messages(current_messages)
        
        # Display user message immediately
        with st.chat_message("user"):
            st.markdown(user_input)

        # Get assistant response
        with st.chat_message("assistant"):
            # Show thinking indicator
            thinking_placeholder = st.empty()
            thinking_placeholder.info("Thinking...")
            
            try:
                # Prepare history for the agent - reconstruct full conversation including tool usage
                history = []
                for msg in current_messages[:-1]:  # Exclude the just-added user message
                    role = msg.get("role")
                    if role not in ["user", "assistant"]:
                        continue
                    
                    # Check if this is an assistant message with tool usage
                    tool_usage = msg.get("tool_usage", [])
                    content = msg.get("content", "")
                    
                    if role == "assistant" and tool_usage:
                        # Reconstruct assistant message with tool_use blocks
                        # We need to create tool_use blocks from the stored tool_usage
                        content_blocks = []
                        
                        # Add text content if present
                        if content and content.strip():
                            content_blocks.append({
                                "type": "text",
                                "text": content
                            })
                        
                        # Add tool_use blocks
                        for tool in tool_usage:
                            tool_name = tool.get("name")
                            tool_args = tool.get("args", {})
                            tool_use_id = tool.get("tool_use_id")
                            
                            # If we don't have a stored tool_use_id, generate one
                            # (this shouldn't happen for new messages, but handles legacy data)
                            if not tool_use_id:
                                tool_use_id = f"toolu_{hashlib.md5(f'{tool_name}{str(tool_args)}'.encode()).hexdigest()[:16]}"
                            
                            content_blocks.append({
                                "type": "tool_use",
                                "id": tool_use_id,
                                "name": tool_name,
                                "input": tool_args
                            })
                        
                        history.append({
                            "role": "assistant",
                            "content": content_blocks if content_blocks else content
                        })
                        
                        # Add tool results as a user message (following Anthropic's format)
                        tool_results = []
                        for tool in tool_usage:
                            tool_name = tool.get("name")
                            tool_args = tool.get("args", {})
                            tool_result = tool.get("result", "")
                            tool_use_id = tool.get("tool_use_id")
                            
                            # If we don't have a stored tool_use_id, generate one
                            if not tool_use_id:
                                tool_use_id = f"toolu_{hashlib.md5(f'{tool_name}{str(tool_args)}'.encode()).hexdigest()[:16]}"
                            
                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": tool_use_id,
                                "content": str(tool_result)
                            })
                        
                        if tool_results:
                            history.append({
                                "role": "user",
                                "content": tool_results
                            })
                    else:
                        # Regular user or assistant message without tools
                        history.append({
                            "role": role,
                            "content": content
                        })
                
                # Capture stdout to get printed responses
                old_stdout = sys.stdout
                sys.stdout = captured_output = StringIO()
                
                # Clear thinking indicator
                thinking_placeholder.empty()
                
                # Use streaming version
                # Create placeholders - logger messages appear first, then response
                log_placeholder = st.empty()  # For logger output
                tool_usage_placeholder = st.empty()
                token_usage_placeholder = st.empty()
                response_placeholder = st.empty()  # For streaming response
                
                # Create logger with placeholder for real-time log display
                ui_logger = StreamlitLogger(log_placeholder=log_placeholder)
                
                # Collect streaming data
                full_response_text = ""
                tool_usage = []
                token_usage_per_iteration = []
                current_tool_info = None
                text_chunks_buffer = []  # Buffer text chunks until we know if tools come first
                tools_executed = False
                tool_use_id_map = {}  # Map tool names+args to tool_use_ids
                
                # Process events and handle display order
                for event_type, data in run_agent_anthropic_stream(user_input, history, ui_logger):
                    if event_type == 'tool_start':
                        # Tools are being executed - show this immediately
                        if not tools_executed:
                            # First tool execution - clear any previous text and start fresh
                            # This ensures tool messages appear before the response text
                            full_response_text = ""  # Reset for response after tools
                            response_placeholder.empty()  # Clear the response area
                        
                        tools_executed = True
                        current_tool_info = data
                        tool_name = data.get("name", "unknown")
                        tool_args = data.get("args", {})
                        tool_use_id = data.get("tool_use_id")
                        args_str = ", ".join([f"`{k}`=`{v}`" for k, v in tool_args.items()])
                        tool_usage_placeholder.info(f"Executing: **{tool_name}**({args_str})")
                        
                        # Store tool_use_id for later use
                        if tool_use_id:
                            tool_key = f"{tool_name}:{str(tool_args)}"
                            tool_use_id_map[tool_key] = tool_use_id
                        
                        # Clear any buffered text - we'll show response text after tools
                        text_chunks_buffer = []
                    
                    elif event_type == 'tool_result':
                        # Store tool result with tool_use_id
                        tool_name = data.get("name")
                        tool_result = data.get("result")
                        tool_use_id = data.get("tool_use_id")
                        tool_args = current_tool_info.get("args", {}) if current_tool_info else {}
                        
                        # If tool_use_id not in data, try to get it from map
                        if not tool_use_id:
                            tool_key = f"{tool_name}:{str(tool_args)}"
                            tool_use_id = tool_use_id_map.get(tool_key)
                        
                        tool_usage.append({
                            "name": tool_name,
                            "args": tool_args,
                            "result": tool_result,
                            "tool_use_id": tool_use_id
                        })
                        current_tool_info = None
                    
                    elif event_type == 'token_usage':
                        # Show token usage (minimal, can be hidden)
                        token_usage_per_iteration.append(data)
                        # Don't show token usage during streaming for cleaner UI
                    
                    elif event_type == 'text':
                        # Always accumulate text
                        full_response_text += data
                        
                        # If tools have been executed, show text immediately
                        # Otherwise, buffer it in case tools come (but show a bit to indicate streaming)
                        if tools_executed:
                            # Tools already executed, stream text immediately
                            response_placeholder.markdown(full_response_text)
                        else:
                            # Buffer text but show it anyway (tools might not come)
                            text_chunks_buffer.append(data)
                            # Show buffered text so user sees streaming, but we'll reorder if tools come
                            response_placeholder.markdown(full_response_text)
                    
                    elif event_type == 'done':
                        # Flush any remaining buffered text
                        if text_chunks_buffer:
                            buffered_text = "".join(text_chunks_buffer)
                            full_response_text += buffered_text
                            response_placeholder.markdown(full_response_text)
                            text_chunks_buffer = []
                        
                        # Finalize display
                        final_result = data
                        final_tool_usage = final_result.get("tool_usage", [])
                        final_token_usage = final_result.get("token_usage", {})
                        
                        # Show final tool usage summary (collapsed)
                        if final_tool_usage:
                            with tool_usage_placeholder.expander(f"Tools Used ({len(final_tool_usage)})", expanded=False):
                                for tool in final_tool_usage:
                                    tool_name = tool.get("name", "unknown")
                                    tool_args = tool.get("args", {})
                                    args_str = ", ".join([f"`{k}`=`{v}`" for k, v in tool_args.items()])
                                    st.markdown(f"**{tool_name}**({args_str})")
                        
                        # Show final token usage (collapsed)
                        per_iteration = final_token_usage.get("per_iteration", [])
                        total = final_token_usage.get("total", {})
                        if per_iteration:
                            with token_usage_placeholder.expander("Token Usage", expanded=False):
                                for iter_info in per_iteration:
                                    st.text(f"Iteration {iter_info['iteration']}: {iter_info['input']} in / {iter_info['output']} out")
                                if len(per_iteration) > 1:
                                    st.markdown("---")
                                    st.text(f"**Total**: {total.get('input', 0)} in / {total.get('output', 0)} out")
                        elif total:
                            with token_usage_placeholder.expander("Token Usage", expanded=False):
                                st.text(f"Total: {total.get('input', 0)} in / {total.get('output', 0)} out")
                        
                        # Store assistant message
                        content_to_store = full_response_text if full_response_text else ("Request processed successfully." if final_tool_usage else "Request processed successfully.")
                        current_messages = get_current_messages()
                        current_messages.append({
                            "role": "assistant",
                            "content": content_to_store,
                            "tool_usage": final_tool_usage,
                            "token_usage": final_token_usage
                        })
                        set_current_messages(current_messages)
                        break
                    
                # Restore stdout
                sys.stdout = old_stdout
                    
            except Exception as e:
                thinking_placeholder.empty()
                # Use info instead of error to avoid red colors
                st.info(f"Error: {str(e)}")
                current_messages = get_current_messages()
                current_messages.append({
                    "role": "assistant",
                    "content": f"Error: {str(e)}"
                })
                set_current_messages(current_messages)


if __name__ == "__main__":
    main()
