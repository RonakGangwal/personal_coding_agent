from anthropic import Anthropic
import os
import time
from typing import Dict, List, Any, Iterator, Optional
from tools.tools import TOOLS, TOOL_FUNCTIONS
from prompt_store.system_prompt import system_prompt
from config.API_KEY import API_KEY

# Streaming speed control (delay in seconds between chunks)
STREAMING_DELAY = 0.5  # 20ms delay = ~50 chunks per second


def run_agent_anthropic_stream(user_input, history, logger):
    """
    Run the Anthropic agent with streaming support.
    
    Args:
        user_input: User's message
        history: Conversation history
        logger: Logger instance
    
    Yields:
        Tuples of (event_type, data) where event_type can be:
        - 'text': text chunk (str)
        - 'tool_start': tool execution started (dict with 'name', 'args')
        - 'tool_result': tool execution completed (dict with 'name', 'result')
        - 'token_usage': token usage info (dict with 'input', 'output', 'iteration')
        - 'done': final result (dict with 'responses', 'tool_usage', 'token_usage')
    """
    logger.debug("Initializing Anthropic client")
    client = Anthropic(api_key=API_KEY)
    
    messages = [*history, {"role": "user", "content": user_input}]
    
    all_responses = []
    all_tool_usage = []
    token_usage_per_iteration = []

    iteration = 0
    while True:
        iteration += 1
        logger.info(f"\n--- Iteration {iteration} ---")
        logger.debug(f"Sending streaming request to Anthropic API (model: claude-3-5-haiku-latest)")
        
        with client.messages.stream(
            model="claude-3-5-haiku-latest",
            max_tokens=4000,
            temperature=0.5,
            system=system_prompt,
            messages=messages,
            tools=TOOLS,
        ) as stream:
            current_text = ""
            
            for event in stream:
                # Handle text delta events - stream text as it arrives
                if event.type == "content_block_delta":
                    if hasattr(event, 'delta') and hasattr(event.delta, 'text'):
                        text_delta = event.delta.text
                        current_text += text_delta
                        # Add small delay to slow down streaming for better visibility
                        time.sleep(STREAMING_DELAY)
                        yield ('text', text_delta)
            
            # Get the final message to extract complete content and usage
            final_message = stream.get_final_message()
            
            # Extract token usage from final message
            if hasattr(final_message, 'usage') and final_message.usage:
                input_tokens = final_message.usage.input_tokens
                output_tokens = final_message.usage.output_tokens
                token_usage_per_iteration.append({
                    "iteration": iteration,
                    "input": input_tokens,
                    "output": output_tokens
                })
                token_info = f"📊 Tokens: {input_tokens} in / {output_tokens} out"
                logger.info(token_info)
                yield ('token_usage', {
                    "input": input_tokens,
                    "output": output_tokens,
                    "iteration": iteration
                })
            
            # Collect tool uses and text responses from final message
            tool_uses = []
            text_responses = []
            
            for content_block in final_message.content:
                if content_block.type == "tool_use":
                    tool_uses.append(content_block)
                    logger.debug(f"Tool use detected: {content_block.name}")
                elif content_block.type == "text":
                    text_responses.append(content_block.text)
                    logger.debug(f"Text response received ({len(content_block.text)} chars)")
            
            # Store complete text response
            if text_responses:
                combined_text = "\n".join(text_responses)
                all_responses.append(combined_text)
                logger.info("Agent response (no tool calls)")
            
            # If there are tool uses, execute them
            if tool_uses:
                logger.info(f" Agent requested {len(tool_uses)} tool call(s)")
                
                # Prepare assistant message with all tool uses
                assistant_content = [{"type": "tool_use", "id": tu.id, "name": tu.name, "input": tu.input} for tu in tool_uses]
                messages.append({
                    "role": "assistant",
                    "content": assistant_content,
                })
                logger.debug("Added assistant tool use message to conversation")
                
                # Execute all tools and collect results
                tool_results = []
                iteration_tool_usage = []
                
                for tool_use in tool_uses:
                    tool_name = tool_use.name
                    args = tool_use.input
                    tool_use_id = tool_use.id
                    
                    logger.info(f" Executing tool: {tool_name}")
                    logger.debug(f"Tool arguments: {args}")
                    yield ('tool_start', {"name": tool_name, "args": args, "tool_use_id": tool_use_id})

                    # Run the tool and send result back
                    if tool_name not in TOOL_FUNCTIONS:
                        tool_result = f"Unknown tool: {tool_name}"
                        logger.error(f"Unknown tool requested: {tool_name}")
                    else:
                        try:
                            tool_result = TOOL_FUNCTIONS[tool_name](args)
                        except Exception as e:
                            tool_result = f"Error: Tool execution failed: {e}"
                            logger.error(f" Tool {tool_name} failed: {str(e)}", exc_info=True)

                    yield ('tool_result', {"name": tool_name, "result": str(tool_result), "tool_use_id": tool_use_id})

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_use.id,
                        "content": str(tool_result),
                    })
                    
                    iteration_tool_usage.append({
                        "name": tool_name,
                        "args": args,
                        "result": str(tool_result)
                    })
                
                all_tool_usage.extend(iteration_tool_usage)
                
                # Append tool results as user message
                messages.append({
                    "role": "user",
                    "content": tool_results,
                })
                logger.debug("Added tool results to conversation, continuing loop...")
                
                continue
            else:
                # No tool uses, we're done
                logger.info("Agent completed (no more tool calls)")
                break
    
    # Calculate total tokens
    total_input = sum(t["input"] for t in token_usage_per_iteration)
    total_output = sum(t["output"] for t in token_usage_per_iteration)
    
    yield ('done', {
        "responses": all_responses,
        "tool_usage": all_tool_usage,
        "token_usage": {
            "per_iteration": token_usage_per_iteration,
            "total": {"input": total_input, "output": total_output}
        }
    })


def run_agent_anthropic(user_input, history, logger):
    """Non-streaming version for backward compatibility."""
    logger.debug("Initializing Anthropic client")
    client = Anthropic(api_key=API_KEY)
    
    messages = [*history, {"role": "user", "content": user_input}]
    
    all_responses = []
    all_tool_usage = []
    token_usage_per_iteration = []

    iteration = 0
    while True:
        iteration += 1
        logger.info(f"\n--- Iteration {iteration} ---")
        logger.debug(f"Sending request to Anthropic API (model: claude-3-5-haiku-latest)")
        
        response = client.messages.create(
            model="claude-3-5-haiku-latest",
            max_tokens=4000,
            temperature=0.5,
            system=system_prompt,
            messages=messages,
            tools=TOOLS,
        )
        
        # Extract token usage
        input_tokens = 0
        output_tokens = 0
        if hasattr(response, 'usage') and response.usage:
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            token_usage_per_iteration.append({
                "iteration": iteration,
                "input": input_tokens,
                "output": output_tokens
            })
            token_info = f"📊 Tokens: {input_tokens} in / {output_tokens} out"
            logger.info(token_info)
            print(f"\n{token_info}")
        
        logger.debug(f"Received response from API (response ID: {response.id})")
        
        # Collect all tool uses and text responses
        tool_uses = []
        text_responses = []
        
        for content_block in response.content:
            if content_block.type == "tool_use":
                tool_uses.append(content_block)
                logger.debug(f"Tool use detected: {content_block.name}")
            elif content_block.type == "text":
                text_responses.append(content_block.text)
                logger.debug(f"Text response received ({len(content_block.text)} chars)")
        
        # If there are text responses, print them
        if text_responses:
            combined_text = "\n".join(text_responses)
            all_responses.append(combined_text)
            logger.info("Agent response (no tool calls)")
            print("\nClaude:")
            print(combined_text)
        
        # If there are tool uses, execute them
        if tool_uses:
            logger.info(f" Agent requested {len(tool_uses)} tool call(s)")
            
            # Prepare assistant message with all tool uses
            assistant_content = [{"type": "tool_use", "id": tu.id, "name": tu.name, "input": tu.input} for tu in tool_uses]
            messages.append({
                "role": "assistant",
                "content": assistant_content,
            })
            logger.debug("Added assistant tool use message to conversation")
            
            # Execute all tools and collect results
            tool_results = []
            iteration_tool_usage = []
            
            for tool_use in tool_uses:
                tool_name = tool_use.name
                args = tool_use.input
                tool_use_id = tool_use.id
                
                logger.info(f" Executing tool: {tool_name}")
                logger.debug(f"Tool arguments: {args}")
                print(f"\n🔧 Executing: {tool_name}({args})")

                # Run the tool and send result back
                if tool_name not in TOOL_FUNCTIONS:
                    tool_result = f"Unknown tool: {tool_name}"
                    logger.error(f"Unknown tool requested: {tool_name}")
                else:
                    try:
                        tool_result = TOOL_FUNCTIONS[tool_name](args)
                        print(f"✅ Result: {tool_result}")
                    except Exception as e:
                        tool_result = f"Error: Tool execution failed: {e}"
                        logger.error(f" Tool {tool_name} failed: {str(e)}", exc_info=True)
                        print(f"❌ {tool_result}")

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_use.id,
                    "content": str(tool_result),
                })
                
                iteration_tool_usage.append({
                    "name": tool_name,
                    "args": args,
                    "result": str(tool_result)
                })
            
            all_tool_usage.extend(iteration_tool_usage)
            
            # Append tool results as user message
            messages.append({
                "role": "user",
                "content": tool_results,
            })
            logger.debug("Added tool results to conversation, continuing loop...")
            
            continue
        else:
            # No tool uses, we're done
            logger.info("Agent completed (no more tool calls)")
            break
    
    # Calculate total tokens
    total_input = sum(t["input"] for t in token_usage_per_iteration)
    total_output = sum(t["output"] for t in token_usage_per_iteration)
    
    return {
        "responses": all_responses,
        "tool_usage": all_tool_usage,
        "token_usage": {
            "per_iteration": token_usage_per_iteration,
            "total": {"input": total_input, "output": total_output}
        }
    }
