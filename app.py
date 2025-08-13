import streamlit as st
import google.generativeai as genai
import json
import re
import time
import atexit
import base64
import requests
from mcp_server import LocalMCPServer

# Performance monitoring
load_start = time.time()

# Configure the page
st.set_page_config(
    page_title="My AI Personal Assistant",
    page_icon="🤖",
    layout="wide"
)

# Function to load animated GIF
@st.cache_data
def get_gif_bytes():
    """Load GIF as bytes for animated display"""
    try:
        # Try local file first
        with open('robot.gif', 'rb') as f:
            return f.read()
    except Exception:
        # Fallback to online GIF
        try:
            gif_url = "https://media.giphy.com/media/3oEjI6SIIHBdRxXI40/giphy.gif"
            response = requests.get(gif_url)
            if response.status_code == 200:
                return response.content
        except:
            pass
    return None

# Cache expensive resources
@st.cache_resource
def init_mcp_server():
    """Initialize thread-safe MCP server once and cache it"""
    return LocalMCPServer()

@st.cache_resource  
def init_ai_model(api_key):
    """Initialize AI model once and cache it"""
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-2.5-pro')

# Configure AI
API_KEY = "AIzaSyAG3OHH59pGnFpcnTHy-zPNeCOjOsl9NUo"

# Initialize session state with performance optimization
if "messages" not in st.session_state:
    st.session_state.messages = []

if "mcp_server" not in st.session_state:
    with st.spinner("🔄 Initializing MCP server..."):
        st.session_state.mcp_server = init_mcp_server()
    
    # Register cleanup function
    def cleanup_database():
        if hasattr(st.session_state, 'mcp_server') and st.session_state.mcp_server:
            st.session_state.mcp_server.close_database()
    
    atexit.register(cleanup_database)

if "model" not in st.session_state:
    with st.spinner("🤖 Loading AI model..."):
        st.session_state.model = init_ai_model(API_KEY)

# Use cached model
model = st.session_state.model

# Cache desktop files for 30 seconds to avoid repeated file system calls
@st.cache_data(ttl=30)
def get_cached_desktop_files():
    """Get desktop files with caching to improve performance"""
    return st.session_state.mcp_server.list_files()

# Cache task stats for 10 seconds
@st.cache_data(ttl=10)
def get_cached_task_stats():
    """Get task statistics with caching"""
    return st.session_state.mcp_server.get_task_stats()

# Cache task list for 5 seconds
@st.cache_data(ttl=5)
def get_cached_tasks():
    """Get task list with caching"""
    return st.session_state.mcp_server.list_tasks()

# BEAUTIFUL UI CSS
st.markdown("""
<style>
/* Animated gradient title */
.gradient-title {
    font-size: 3.2rem;
    font-weight: 700;
    background: linear-gradient(90deg, #ff6b6b, #feca57, #48dbfb, #ff9ff3);
    background-size: 300% 100%;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    animation: gradient-shift 3s ease infinite;
    text-align: center;
    margin-bottom: 1rem;
    padding: 10px 0;
}

@keyframes gradient-shift {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

/* Clean example sections */
.example-section {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 20px;
    border-radius: 15px;
    margin: 15px 5px;
    color: white;
    box-shadow: 0 8px 25px rgba(0,0,0,0.1);
}

.example-category {
    font-size: 1.2rem;
    font-weight: 600;
    margin-bottom: 12px;
    color: #fff;
    display: flex;
    align-items: center;
    gap: 8px;
}

.example-list {
    list-style: none;
    padding-left: 0;
    margin: 0;
}

.example-list li {
    background: rgba(255,255,255,0.15);
    margin: 6px 0;
    padding: 10px 15px;
    border-radius: 10px;
    font-size: 0.95rem;
    border-left: 4px solid #feca57;
    transition: all 0.3s ease;
}

.example-list li:hover {
    background: rgba(255,255,255,0.25);
    transform: translateX(5px);
}

/* Sidebar styling */
.sidebar-content {
    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    padding: 18px;
    border-radius: 15px;
    margin: 15px 0;
    color: white;
    box-shadow: 0 6px 20px rgba(0,0,0,0.15);
}

.sidebar-title {
    font-size: 1.2rem;
    font-weight: 600;
    margin-bottom: 12px;
    color: #fff;
    display: flex;
    align-items: center;
    gap: 8px;
}

.sidebar-text {
    font-size: 0.95rem;
    line-height: 1.5;
    margin: 8px 0;
    opacity: 0.95;
}

/* GIF container */
.gif-container {
    text-align: center;
    margin-bottom: 25px;
    padding: 10px;
}

.robot-gif {
    width: 130%;
    max-width: 180px;
    border-radius: 15px;
    box-shadow: 0 8px 25px rgba(0,0,0,0.2);
    transition: transform 0.1s ease;
}

.robot-gif:hover {
    transform: scale(1.05);
}

/* Chat message styling */
.chat-message {
    margin: 15px 0;
    padding: 15px 20px;
    border-radius: 18px;
    max-width: 85%;
    word-wrap: break-word;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    animation: slideIn 0.3s ease;
}

@keyframes slideIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

/* Button styling */
.stButton > button {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white !important;
    border: none !important;
    padding: 12px 20px;
    font-weight: 600;
    font-size: 1rem;
    width: 100%;
    border-radius: 25px;
    transition: all 0.3s ease;
    margin: 8px 0;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
}

.stButton > button:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 25px rgba(0,0,0,0.2);
    background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
}

.stButton > button:active {
    transform: translateY(-1px);
}

/* Chat input styling */
.stChatInput > div > div > input {
    border-radius: 25px;
    border: 2px solid #e0e0e0;
    padding: 12px 20px;
    font-size: 1rem;
    transition: all 0.3s ease;
}

.stChatInput > div > div > input:focus {
    border-color: #667eea;
    box-shadow: 0 0 15px rgba(102, 126, 234, 0.3);
}

/* Performance indicator */
.perf-indicator {
    background: linear-gradient(135deg, #00b894 0%, #55a3ff 100%);
    color: white;
    padding: 10px 20px;
    border-radius: 25px;
    text-align: center;
    font-weight: 600;
    margin: 10px 0;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
}

/* Tool execution indicator */
.tool-execution {
    background: linear-gradient(135deg, #ff7675 0%, #fd79a8 100%);
    color: white;
    padding: 12px 18px;
    border-radius: 10px;
    margin: 10px 0;
    font-weight: 500;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

/* Success message */
.success-message {
    background: linear-gradient(135deg, #00b894 0%, #00cec9 100%);
    color: white;
    padding: 10px 15px;
    border-radius: 8px;
    margin: 8px 0;
    font-weight: 500;
}

/* Error message */
.error-message {
    background: linear-gradient(135deg, #ff7675 0%, #fd79a8 100%);
    color: white;
    padding: 10px 15px;
    border-radius: 8px;
    margin: 8px 0;
    font-weight: 500;
}

/* Task list styling */
.task-item {
    background: rgba(255,255,255,0.1);
    padding: 8px 12px;
    margin: 5px 0;
    border-radius: 8px;
    font-size: 0.9rem;
}

/* Hide Streamlit footer and header */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

def parse_ai_response_for_tool_call(response_text, available_tools):
    """ENHANCED: Parser with delete folder support and better task detection"""
    response_lower = response_text.lower()
    
    # Look for explicit tool usage patterns first
    tool_match = re.search(r'using?\s+(\w+)', response_lower)
    if tool_match:
        tool_name = tool_match.group(1)
        
        # Extract parameters based on tool type
        if tool_name == "add_task":
            task_match = re.search(r'"([^"]+)"', response_text)
            if task_match:
                return {"tool": "add_task", "params": {"task_description": task_match.group(1)}}
        
        elif tool_name == "create_folder":
            folder_match = re.search(r'"([^"]+)"', response_text)
            if folder_match:
                return {"tool": "create_folder", "params": {"folder_name": folder_match.group(1)}}
        
        elif tool_name == "delete_folder":
            folder_match = re.search(r'"([^"]+)"', response_text)
            if folder_match:
                return {"tool": "delete_folder", "params": {"folder_name": folder_match.group(1)}}
        
        elif tool_name == "rename_folder":
            quotes = re.findall(r'"([^"]+)"', response_text)
            if len(quotes) >= 2:
                return {"tool": "rename_folder", "params": {"old_name": quotes[0], "new_name": quotes[1]}}
        
        elif tool_name in ["list_tasks", "list_files"]:
            return {"tool": tool_name, "params": {}}
        
        elif tool_name == "complete_task" or tool_name == "delete_task":
            id_match = re.search(r'\b(\d+)\b', response_text)
            if id_match:
                return {"tool": tool_name, "params": {"task_id": int(id_match.group(1))}}
    
    # Fallback: Look for specific action keywords
    if "add" in response_lower and "task" in response_lower:
        task_match = re.search(r'"([^"]+)"', response_text)
        if task_match:
            return {"tool": "add_task", "params": {"task_description": task_match.group(1)}}
    
    if "create" in response_lower and "folder" in response_lower:
        folder_match = re.search(r'"([^"]+)"', response_text)
        if folder_match:
            return {"tool": "create_folder", "params": {"folder_name": folder_match.group(1)}}
    
    if ("delete" in response_lower or "remove" in response_lower) and "folder" in response_lower:
        folder_match = re.search(r'"([^"]+)"', response_text)
        if folder_match:
            return {"tool": "delete_folder", "params": {"folder_name": folder_match.group(1)}}
    
    if ("rename" in response_lower or "change name" in response_lower) and "folder" in response_lower:
        quotes = re.findall(r'"([^"]+)"', response_text)
        if len(quotes) >= 2:
            return {"tool": "rename_folder", "params": {"old_name": quotes[0], "new_name": quotes[1]}}
    
    if ("list" in response_lower or "show" in response_lower) and "task" in response_lower:
        return {"tool": "list_tasks", "params": {}}
    
    if ("list" in response_lower or "show" in response_lower) and "file" in response_lower:
        return {"tool": "list_files", "params": {}}
    
    return None

def extract_potential_tasks_from_input(user_input):
    """Extract potential tasks from user input that should be added to task list"""
    task_patterns = [
        r"(?:i need to|i have to|i want to|i should|remind me to|add task|todo)\s+(.+)",
        r"(?:task:|todo:|reminder:)\s*(.+)",
        r"(?:remember to|don't forget to)\s+(.+)"
    ]
    
    user_lower = user_input.lower()
    for pattern in task_patterns:
        match = re.search(pattern, user_lower)
        if match:
            task_description = match.group(1).strip()
            task_description = re.sub(r'\s+', ' ', task_description)
            if task_description:
                return task_description
    
    return None

def execute_tool_call(tool_call):
    """Execute a tool call on the MCP server with performance monitoring"""
    server = st.session_state.mcp_server
    tool_name = tool_call["tool"]
    params = tool_call["params"]
    
    # Clear relevant caches when data is modified
    if tool_name in ["add_task", "complete_task", "delete_task", "clear_completed_tasks"]:
        get_cached_tasks.clear()
        get_cached_task_stats.clear()
    
    if tool_name == "add_task":
        return server.add_task(params["task_description"])
    elif tool_name == "list_tasks":
        return server.list_tasks()
    elif tool_name == "complete_task":
        return server.complete_task(params["task_id"])
    elif tool_name == "delete_task":
        return server.delete_task(params["task_id"])
    elif tool_name == "create_folder":
        result = server.create_folder(params["folder_name"])
        get_cached_desktop_files.clear()
        return result
    elif tool_name == "delete_folder":
        result = server.delete_folder(params["folder_name"])
        get_cached_desktop_files.clear()
        return result
    elif tool_name == "rename_folder":
        result = server.rename_folder(params["old_name"], params["new_name"])
        get_cached_desktop_files.clear()
        return result
    elif tool_name == "list_files":
        subfolder = params.get("subfolder", "")
        file_extension = params.get("file_extension")
        return server.list_files(subfolder, file_extension)
    elif tool_name == "read_json_file":
        return server.read_json_file(params["filename"])
    elif tool_name == "write_json_file":
        return server.write_json_file(params["filename"], params["content"])
    else:
        return {"success": False, "message": f"Unknown tool: {tool_name}"}

@st.cache_data(ttl=60)
def get_system_prompt(tools_json, potential_task=None):
    """Generate system prompt with caching"""
    base_prompt = f"""You are a helpful AI assistant with access to these tools:

{tools_json}

IMPORTANT: When you decide to use a tool, you MUST respond in this exact format:
"I'll [action description] using [tool_name] with [parameters]"

Examples:
- User: "add buy milk to my tasks" → You: "I'll add that task using add_task with "buy milk""
- User: "create folder MyProject" → You: "I'll create that folder using create_folder with "MyProject""
- User: "delete folder TestFolder" → You: "I'll delete that folder using delete_folder with "TestFolder""
- User: "rename folder aditya to NewName" → You: "I'll rename that folder using rename_folder with "aditya" and "NewName""

TASK DETECTION: If the user mentions something they need to do, want to do, or should remember, automatically add it as a task.
Examples:
- "I need to call the dentist" → You: "I'll add that task using add_task with "call the dentist""
- "Remind me to buy groceries" → You: "I'll add that reminder using add_task with "buy groceries""
- "I have to finish the report" → You: "I'll add that task using add_task with "finish the report""

SPECIAL FEATURES:
- File operations (create/delete/rename folders) are automatically tracked as completed tasks
- Any task mentioned by the user should be added to their task list

SECURITY: You can only access Desktop folder and its subfolders."""

    if potential_task:
        base_prompt += f'\n\nDETECTED TASK: The user mentioned "{potential_task}" - you should add this as a task.'
    
    return base_prompt

def get_ai_response(user_input):
    """Get response from AI with enhanced task detection and caching"""
    tools_info = st.session_state.mcp_server.get_available_tools()
    potential_task = extract_potential_tasks_from_input(user_input)
    
    system_prompt = get_system_prompt(json.dumps(tools_info, indent=2), potential_task)
    full_prompt = f"{system_prompt}\n\nUser request: {user_input}"

    response = model.generate_content(full_prompt)
    return response.text

def manage_message_history():
    """Keep only the last 50 messages to prevent performance degradation"""
    if len(st.session_state.messages) > 50:
        st.session_state.messages = st.session_state.messages[-50:]

# MAIN APP WITH BEAUTIFUL UI
st.markdown('<h1 class="gradient-title">🤖 My Personal Assistant</h1>', unsafe_allow_html=True)

# Performance indicator
init_time = time.time() - load_start
if init_time > 2:
    st.markdown(f'<div class="perf-indicator">⚡ App loaded in {init_time:.2f}s</div>', unsafe_allow_html=True)

# Beautiful example sections
col1, col2 = st.columns(2)
with col1:
    st.markdown("""
    <div class="example-section">
        <div class="example-category">📋 Task Management</div>
        <ul class="example-list">
            <li>Add "buy groceries"</li>
            <li>I need to call the dentist</li>
            <li>Complete task 2</li>
            <li>Show my current tasks</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="example-section">
        <div class="example-category">📁 Desktop Operations</div>
        <ul class="example-list">
            <li>Create folder "ProjectX"</li>
            <li>Rename folder to "ProjectY"</li>
            <li>Delete empty folder</li>
            <li>Show files on desktop</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

# REMOVED: Auto-tracking banner completely removed from here

# SIDEBAR WITH ANIMATED GIF
with st.sidebar:
    # Animated GIF at top
    gif_bytes = get_gif_bytes()
    if gif_bytes:
        gif_b64 = base64.b64encode(gif_bytes).decode()
        st.markdown(f"""
        <div class="gif-container">
            <img src="data:image/gif;base64,{gif_b64}" class="robot-gif" alt="AI Assistant Robot">
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown('<div class="gif-container"><p>🤖 Loading animation...</p></div>', unsafe_allow_html=True)

    # Task Dashboard
    st.markdown("""
    <div class="sidebar-content">
        <div class="sidebar-title">📋 Task Dashboard</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Use cached task data
    tasks_result = get_cached_tasks()
    if tasks_result["success"] and tasks_result["tasks"]:
        completed_tasks = [t for t in tasks_result["tasks"] if t["completed"]]
        pending_tasks = [t for t in tasks_result["tasks"] if not t["completed"]]
        
        if pending_tasks:
            st.write("**⏳ Pending Tasks:**")
            for task in pending_tasks:
                st.markdown(f'<div class="task-item">⏳ **{task["id"]}.** {task["description"]}</div>', unsafe_allow_html=True)
        
        if completed_tasks:
            st.write("**✅ Recently Completed:**")
            for task in completed_tasks[-3:]:  # Show last 3
                st.markdown(f'<div class="task-item">✅ **{task["id"]}.** {task["description"]}</div>', unsafe_allow_html=True)
    else:
        st.write("No tasks yet!")
    
    # Desktop Access info
    st.markdown("""
    <div class="sidebar-content">
        <div class="sidebar-title">🔒 Desktop Access</div>
        <div class="sidebar-text">• Secure desktop-only operations</div>
    </div>
    """, unsafe_allow_html=True)

    # REMOVED: Auto-tracking section completely removed from sidebar

    # Action buttons
    if st.button("🔄 Refresh"):
        get_cached_tasks.clear()
        get_cached_task_stats.clear()
        get_cached_desktop_files.clear()
        get_system_prompt.clear()
        st.rerun()

    if st.button("🧹 Clear Chat History"):
        st.session_state.messages = []
        st.rerun()

# CHAT INTERFACE
manage_message_history()
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("💬 What would you like me to do?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.write(prompt)
    
    with st.chat_message("assistant"):
        with st.spinner("🤔 Thinking..."):
            response_start = time.time()
            ai_response = get_ai_response(prompt)
            response_time = time.time() - response_start
            
            st.markdown(ai_response)
            
            if response_time > 3:
                st.caption(f"⏱️ AI response took {response_time:.2f}s")
            
            tool_call = parse_ai_response_for_tool_call(ai_response, st.session_state.mcp_server.get_available_tools())
            
            if tool_call:
                st.markdown(f'<div class="tool-execution">🛠️ <strong>Executing:</strong> {tool_call["tool"]} with {tool_call["params"]}</div>', unsafe_allow_html=True)
                
                with st.spinner("⚙️ Executing..."):
                    exec_start = time.time()
                    result = execute_tool_call(tool_call)
                    exec_time = time.time() - exec_start
                
                if result["success"]:
                    if tool_call["tool"] in ["create_folder", "delete_folder", "rename_folder"]:
                        st.markdown(f'<div class="success-message">✅ {result["message"]}</div>', unsafe_allow_html=True)
                        # REMOVED: Auto-added task message completely removed
                    
                    elif tool_call["tool"] == "add_task":
                        st.markdown(f'<div class="success-message">✅ {result["message"]}</div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="success-message">📋 Task added with ID: {result.get("task_id")}</div>', unsafe_allow_html=True)
                    
                    elif tool_call["tool"] == "list_tasks":
                        if result["tasks"]:
                            st.write("📋 **Your current tasks:**")
                            for task in result["tasks"]:
                                status = "✅" if task["completed"] else "⏳"
                                st.write(f"{status} **{task['id']}.** {task['description']}")
                        else:
                            st.write("📋 Your to-do list is empty!")
                    
                    elif tool_call["tool"] == "list_files":
                        if result["files"] or result["folders"]:
                            st.write(f"📁 **Contents of {result['directory']}:**")
                            
                            if result["folders"]:
                                st.write("**📁 Folders:**")
                                for folder in result["folders"]:
                                    st.write(f"📂 **{folder['name']}/**")
                            
                            if result["files"]:
                                st.write("**📄 Files:**")
                                for file_info in result["files"]:
                                    size_kb = round(file_info["size"] / 1024, 2)
                                    st.write(f"📄 **{file_info['name']}** ({size_kb} KB)")
                        else:
                            st.write(f"📁 No files or folders found in {result['directory']}")
                    
                    else:
                        st.markdown(f'<div class="success-message">✅ {result["message"]}</div>', unsafe_allow_html=True)
                    
                    if exec_time > 1:
                        st.caption(f"⏱️ Execution took {exec_time:.2f}s")
                else:
                    st.markdown(f'<div class="error-message">❌ Error: {result["message"]}</div>', unsafe_allow_html=True)
            else:
                st.write("ℹ️ *No tool execution detected. Try being more specific about what you want me to do.*")
    
    st.session_state.messages.append({"role": "assistant", "content": ai_response})
