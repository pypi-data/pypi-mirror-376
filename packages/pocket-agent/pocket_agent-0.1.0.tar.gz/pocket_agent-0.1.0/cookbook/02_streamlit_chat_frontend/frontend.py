import streamlit as st
import asyncio
import json
import os
from pathlib import Path
from litellm import Router
import litellm
from agent import WeatherAgent
from pocket_agent import AgentConfig, AgentEvent, AgentHooks
import threading
import time

# Get current directory where this frontend.py file is located
current_dir = os.path.dirname(os.path.abspath(__file__))

# Load router configuration
router_config_path = os.path.join(current_dir, "..", "sample_router.json")
with open(router_config_path, 'r') as f:
    router_config = json.load(f)

# Create litellm router
litellm_router = Router(model_list=router_config["models"])

class StreamlitAgentHooks(AgentHooks):
    """Custom hooks for Streamlit real-time updates"""
    
    def __init__(self, real_time_placeholder):
        super().__init__()
        self.real_time_placeholder = real_time_placeholder
    
    def on_event(self, event: AgentEvent) -> None:
        """Handle agent events for real-time UI updates"""
        if event.event_type == "new_message":
            # Initialize agent_messages if not exists
            if "agent_messages" not in st.session_state:
                st.session_state.agent_messages = []
            
            message = event.data
            role = message.get("role", "unknown")
            
            # Format the message for display
            if role == "assistant":
                content = message.get("content", "")
                tool_calls = message.get("tool_calls", [])
                
                if tool_calls:
                    # Show tool calls being made
                    tool_names = [tc.get('function', {}).get('name', 'unknown') for tc in tool_calls]
                    st.session_state.agent_messages.append({
                        "role": "assistant", 
                        "content": f"🔧 Using tools: {', '.join(tool_names)}",
                        "type": "tool_call"
                    })
                    # Update UI immediately
                    self.update_real_time_display()
                
                if content:
                    # Don't add assistant text message here - we'll handle it at the end
                    pass
            
            elif role == "tool":
                # Show tool results
                tool_name = message.get("name", "unknown")
                content = message.get("content", [])
                
                # Extract text content from tool result
                text_content = ""
                if isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict) and item.get("type") == "text":
                            text_content += item.get("text", "")
                elif isinstance(content, str):
                    text_content = content
                
                # Truncate long tool results for display
                display_content = text_content[:150] + "..." if len(text_content) > 150 else text_content
                
                st.session_state.agent_messages.append({
                    "role": "tool",
                    "content": f"📊 **{tool_name}**: {display_content}",
                    "type": "tool_result"
                })
                # Update UI immediately
                self.update_real_time_display()
    
    def update_real_time_display(self):
        """Update the real-time display placeholder"""
        if "agent_messages" in st.session_state and st.session_state.agent_messages:
            with self.real_time_placeholder.container():
                st.markdown("#### 🔍 Real-time Agent Activity")
                for msg in st.session_state.agent_messages:
                    if msg["type"] == "tool_call":
                        st.info(msg["content"])
                    elif msg["type"] == "tool_result":
                        st.success(msg["content"])

def initialize_agent(real_time_placeholder):
    """Initialize the weather agent with proper configuration"""
    try:

        
        # MCP server configuration - simple and clean
        mcp_config = {
            "mcpServers": {
                "weather": {
                    "transport": "stdio",
                    "command": "python",
                    "args": ["server.py"],
                    "cwd": os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "servers", "simple_weather")
                }
            }
        }
        
        # Get existing agent messages from session state
        existing_messages = st.session_state.get("agent_conversation_history", [])
        
        # Agent configuration with existing messages
        config = AgentConfig(
            llm_model="gpt-5-nano",
            system_prompt="You are a helpful weather assistant. Use the available weather tools to provide accurate weather information. Be friendly and conversational.",
            messages=existing_messages  # Pass existing conversation history
        )
        
        # Create custom hooks for Streamlit
        hooks = StreamlitAgentHooks(real_time_placeholder)
        
        # Create agent with the custom hooks
        agent = WeatherAgent(
            agent_config=config,
            mcp_config=mcp_config,
            router=litellm_router,
            hooks=hooks
        )
        
        return agent
    except Exception as e:
        st.error(f"Failed to initialize agent: {str(e)}")
        return None

def run_async_agent_response(agent, user_input):
    """Run the agent response in a proper async context"""
    try:
        # Clear previous agent messages for new request
        st.session_state.agent_messages = []
        
        # Use asyncio.run() which properly handles event loop lifecycle
        response = asyncio.run(agent.run(user_input))
        
        # Save agent's conversation history to session state after each run
        st.session_state.agent_conversation_history = agent.messages.copy()
        
        return response
    except Exception as e:
        st.error(f"Error getting agent response: {str(e)}")
        return {"message": "Sorry, I encountered an error processing your request."}

def main():
    st.set_page_config(
        page_title="Weather Chat Assistant",
        page_icon="🌤️",
        layout="wide"
    )
    
    st.title("🌤️ Weather Chat Assistant")
    st.markdown("Ask me about the weather in any city! Watch as I think and use tools in real-time.")
    
    # Initialize agent conversation history if not exists
    if "agent_conversation_history" not in st.session_state:
        st.session_state.agent_conversation_history = []
    
    # Sidebar with real-time activity and information
    with st.sidebar:
        
        # Create a placeholder for real-time updates in the sidebar
        real_time_placeholder = st.empty()
        
        st.markdown("---")  # Separator line
        
        st.markdown("### Available Weather Tools")
        st.markdown("""
        - **Current Weather**: Ask about current weather in any city
        - **Weather Forecast**: Get multi-day forecasts
        - **Weather Comparison**: Compare weather between two cities
        
        ### Example Queries
        - "What's the weather like in London?"
        - "Give me a 5-day forecast for Tokyo"
        - "Compare the weather in New York and Paris"
        """)
        
        if st.button("Clear Conversation"):
            st.session_state.messages = []
            st.session_state.agent_messages = []
            real_time_placeholder.empty()
            st.session_state.messages.append({
                "role": "assistant", 
                "content": "Hello! I'm your weather assistant. Ask me about the weather in any city, get forecasts, or compare weather between cities!"
            })
            st.rerun()
    
    # Initialize agent with the placeholder - agent will now get existing messages
    agent = initialize_agent(real_time_placeholder)
    if agent is None:
        st.error("Failed to initialize the weather agent. Please check the configuration.")
        st.stop()
    
    # Initialize session state for conversation history
    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.messages.append({
            "role": "assistant", 
            "content": "Hello! I'm your weather assistant. Ask me about the weather in any city, get forecasts, or compare weather between cities!"
        })
    
    # Initialize agent messages for real-time display
    if "agent_messages" not in st.session_state:
        st.session_state.agent_messages = []
    
    # Display conversation history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask about the weather..."):
        # Add user message to conversation
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get agent response with real-time updates
        with st.chat_message("assistant"):
            with st.spinner("Getting weather information..."):
                try:
                    # The event handler will update the real_time_placeholder during execution
                    response = run_async_agent_response(agent, prompt)
                    
                    # Extract the message content from the response
                    if isinstance(response, dict):
                        if "message" in response:
                            content = response["message"]
                        elif "message_content" in response:
                            content = response["message_content"]
                        else:
                            content = str(response)
                    else:
                        content = str(response)
                    
                    # Add assistant response to conversation
                    st.session_state.messages.append({"role": "assistant", "content": content})
                    
                    # Clear the real-time display
                    real_time_placeholder.empty()
                    
                    # Show final response
                    st.rerun()
                    
                except Exception as e:
                    error_msg = f"Sorry, I encountered an error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
                    # Clear real-time display on error
                    real_time_placeholder.empty()

if __name__ == "__main__":
    main()
