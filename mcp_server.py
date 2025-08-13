import json
import os
import shutil
import sqlite3
import threading
from typing import List, Dict, Any
from pathlib import Path


class LocalMCPServer:
    def __init__(self, db_file="mcp_database.sqlite"):
        self.db_file = db_file
        self.desktop_path = self.get_desktop_path()
        self._lock = threading.Lock()  # Thread safety
        self.init_database()
    
    def get_desktop_path(self) -> str:
        """Get the user's desktop path"""
        return os.path.join(os.path.expanduser("~"), "Desktop")
    
    def is_safe_path(self, path: str) -> bool:
        """Check if the path is within the allowed Desktop directory"""
        try:
            abs_path = os.path.abspath(path)
            desktop_path = os.path.abspath(self.desktop_path)
            return abs_path.startswith(desktop_path)
        except:
            return False
    
    def init_database(self):
        """Initialize SQLite database and create tasks table if it doesn't exist"""
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS tasks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        description TEXT NOT NULL,
                        completed BOOLEAN DEFAULT 0
                    )
                ''')
                conn.commit()
        except Exception as e:
            print(f"Error initializing database: {str(e)}")
    
    def get_db_connection(self):
        """Get a thread-safe database connection"""
        conn = sqlite3.connect(self.db_file, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn
    
    # ===== HELPER: AUTO-TASK MANAGEMENT =====
    def auto_add_and_complete_task(self, task_description: str) -> Dict[str, Any]:
        """Add a task and immediately mark it as completed"""
        try:
            # Add the task
            add_result = self.add_task(task_description)
            if not add_result["success"]:
                return add_result
            
            # Complete the task immediately
            task_id = add_result["task_id"]
            complete_result = self.complete_task(task_id)
            
            return {
                "success": True,
                "message": f"Added and completed task: {task_description}",
                "task_id": task_id
            }
        except Exception as e:
            return {"success": False, "message": f"Error with auto task management: {str(e)}"}
    
    # ===== JSON FILE OPERATIONS =====
    def read_json_file(self, filename: str) -> Dict[str, Any]:
        """Read and display contents of a JSON file on Desktop"""
        try:
            file_path = os.path.join(self.desktop_path, filename)
            
            if not self.is_safe_path(file_path):
                return {"success": False, "message": "Access denied: File must be on Desktop"}
            
            if not os.path.exists(file_path):
                return {"success": False, "message": f"File not found: {filename}"}
            
            with open(file_path, 'r') as f:
                content = json.load(f)
            
            return {"success": True, "content": content, "filename": filename}
        
        except json.JSONDecodeError:
            return {"success": False, "message": f"Invalid JSON format in {filename}"}
        except Exception as e:
            return {"success": False, "message": f"Error reading file: {str(e)}"}
    
    def write_json_file(self, filename: str, content: dict) -> Dict[str, Any]:
        """Write content to a JSON file on Desktop"""
        try:
            file_path = os.path.join(self.desktop_path, filename)
            
            if not self.is_safe_path(file_path):
                return {"success": False, "message": "Access denied: File must be on Desktop"}
            
            with open(file_path, 'w') as f:
                json.dump(content, f, indent=2)
            
            return {"success": True, "message": f"Successfully wrote to {filename}"}
        
        except Exception as e:
            return {"success": False, "message": f"Error writing file: {str(e)}"}
    
    # ===== TO-DO LIST TOOLS (THREAD-SAFE) =====
    def add_task(self, task_description: str) -> Dict[str, Any]:
        """Add a new task to the database (thread-safe)"""
        try:
            with self._lock:  # Thread safety
                with self.get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO tasks (description, completed) VALUES (?, ?)",
                        (task_description, False)
                    )
                    task_id = cursor.lastrowid
                    conn.commit()
            
            return {
                "success": True, 
                "message": f"Added task: {task_description}", 
                "task_id": task_id
            }
        
        except Exception as e:
            return {"success": False, "message": f"Error adding task: {str(e)}"}
    
    def list_tasks(self) -> Dict[str, Any]:
        """Get all tasks from the database (thread-safe)"""
        try:
            with self._lock:  # Thread safety
                with self.get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT id, description, completed FROM tasks ORDER BY id")
                    rows = cursor.fetchall()
                    
                    tasks = []
                    for row in rows:
                        tasks.append({
                            "id": row["id"],
                            "description": row["description"],
                            "completed": bool(row["completed"])
                        })
            
            return {"success": True, "tasks": tasks}
        
        except Exception as e:
            return {"success": False, "message": f"Error reading tasks: {str(e)}"}
    
    def complete_task(self, task_id: int) -> Dict[str, Any]:
        """Mark a task as completed in the database (thread-safe)"""
        try:
            with self._lock:  # Thread safety
                with self.get_db_connection() as conn:
                    cursor = conn.cursor()
                    
                    # First check if task exists and get its current status
                    cursor.execute("SELECT description, completed FROM tasks WHERE id = ?", (task_id,))
                    result = cursor.fetchone()
                    
                    if not result:
                        return {"success": False, "message": f"Task with ID {task_id} not found"}
                    
                    task_desc, is_completed = result["description"], result["completed"]
                    if is_completed:
                        return {"success": False, "message": f"Task {task_id} is already completed"}
                    
                    # Update the task to completed
                    cursor.execute("UPDATE tasks SET completed = ? WHERE id = ?", (True, task_id))
                    conn.commit()
            
            return {"success": True, "message": f"Task '{task_desc}' marked as completed"}
        
        except Exception as e:
            return {"success": False, "message": f"Error completing task: {str(e)}"}
    
    def delete_task(self, task_id: int) -> Dict[str, Any]:
        """Delete a task from the database (thread-safe)"""
        try:
            with self._lock:  # Thread safety
                with self.get_db_connection() as conn:
                    cursor = conn.cursor()
                    
                    # First get the task description before deleting
                    cursor.execute("SELECT description FROM tasks WHERE id = ?", (task_id,))
                    result = cursor.fetchone()
                    
                    if not result:
                        return {"success": False, "message": f"Task with ID {task_id} not found"}
                    
                    task_desc = result["description"]
                    
                    # Delete the task
                    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
                    conn.commit()
            
            return {"success": True, "message": f"Deleted task: '{task_desc}'"}
        
        except Exception as e:
            return {"success": False, "message": f"Error deleting task: {str(e)}"}
    
    def clear_completed_tasks(self) -> Dict[str, Any]:
        """Remove all completed tasks from the database (thread-safe)"""
        try:
            with self._lock:  # Thread safety
                with self.get_db_connection() as conn:
                    cursor = conn.cursor()
                    
                    # Count completed tasks first
                    cursor.execute("SELECT COUNT(*) as count FROM tasks WHERE completed = ?", (True,))
                    completed_count = cursor.fetchone()["count"]
                    
                    if completed_count == 0:
                        return {"success": False, "message": "No completed tasks to clear"}
                    
                    # Delete all completed tasks
                    cursor.execute("DELETE FROM tasks WHERE completed = ?", (True,))
                    conn.commit()
            
            return {"success": True, "message": f"Cleared {completed_count} completed task(s)"}
        
        except Exception as e:
            return {"success": False, "message": f"Error clearing completed tasks: {str(e)}"}
    
    def get_task_stats(self) -> Dict[str, Any]:
        """Get statistics about tasks from the database (thread-safe)"""
        try:
            with self._lock:  # Thread safety
                with self.get_db_connection() as conn:
                    cursor = conn.cursor()
                    
                    # Get all stats in a single query for better performance
                    cursor.execute("""
                        SELECT 
                            COUNT(*) as total,
                            SUM(CASE WHEN completed = 1 THEN 1 ELSE 0 END) as completed,
                            SUM(CASE WHEN completed = 0 THEN 1 ELSE 0 END) as pending
                        FROM tasks
                    """)
                    result = cursor.fetchone()
            
            return {
                "success": True, 
                "stats": {
                    "total": result["total"],
                    "completed": result["completed"],
                    "pending": result["pending"]
                }
            }
        
        except Exception as e:
            return {"success": False, "message": f"Error getting task stats: {str(e)}"}
    
    # ===== FILE SYSTEM TOOLS (UNCHANGED) =====
    def create_folder(self, folder_name: str) -> Dict[str, Any]:
        """Create a new folder on Desktop and auto-add as completed task"""
        try:
            folder_path = os.path.join(self.desktop_path, folder_name)
            
            if not self.is_safe_path(folder_path):
                return {"success": False, "message": "Access denied: Can only create folders on Desktop"}
            
            if os.path.exists(folder_path):
                return {"success": False, "message": f"Folder already exists: {folder_name}"}
            
            # Create the folder
            os.makedirs(folder_path, exist_ok=True)
            
            # Auto-add as completed task
            task_result = self.auto_add_and_complete_task(f"Create folder '{folder_name}' on desktop")
            
            return {
                "success": True, 
                "message": f"Created folder: {folder_name} on Desktop",
                "task_added": task_result["success"],
                "task_id": task_result.get("task_id") if task_result["success"] else None
            }
        
        except Exception as e:
            return {"success": False, "message": f"Error creating folder: {str(e)}"}
    
    def delete_folder(self, folder_name: str) -> Dict[str, Any]:
        """Delete a folder from Desktop and auto-add as completed task"""
        try:
            folder_path = os.path.join(self.desktop_path, folder_name)
            
            if not self.is_safe_path(folder_path):
                return {"success": False, "message": "Access denied: Can only delete folders on Desktop"}
            
            if not os.path.exists(folder_path):
                return {"success": False, "message": f"Folder not found: {folder_name}"}
            
            if not os.path.isdir(folder_path):
                return {"success": False, "message": f"'{folder_name}' is not a folder"}
            
            # Check if folder is empty (for safety)
            if os.listdir(folder_path):
                return {"success": False, "message": f"Cannot delete '{folder_name}': Folder is not empty. Please empty it first for safety."}
            
            # Delete the folder
            os.rmdir(folder_path)
            
            # Auto-add as completed task
            task_result = self.auto_add_and_complete_task(f"Delete folder '{folder_name}' from desktop")
            
            return {
                "success": True, 
                "message": f"Deleted folder: {folder_name} from Desktop",
                "task_added": task_result["success"],
                "task_id": task_result.get("task_id") if task_result["success"] else None
            }
        
        except Exception as e:
            return {"success": False, "message": f"Error deleting folder: {str(e)}"}
    
    def rename_folder(self, old_name: str, new_name: str) -> Dict[str, Any]:
        """Rename a folder on Desktop and auto-add as completed task"""
        try:
            old_path = os.path.join(self.desktop_path, old_name)
            new_path = os.path.join(self.desktop_path, new_name)
            
            if not self.is_safe_path(old_path) or not self.is_safe_path(new_path):
                return {"success": False, "message": "Access denied: Can only rename folders on Desktop"}
            
            if not os.path.exists(old_path):
                return {"success": False, "message": f"Folder not found: {old_name}"}
            
            if not os.path.isdir(old_path):
                return {"success": False, "message": f"'{old_name}' is not a folder"}
            
            if os.path.exists(new_path):
                return {"success": False, "message": f"A folder named '{new_name}' already exists"}
            
            # Rename the folder
            os.rename(old_path, new_path)
            
            # Auto-add as completed task
            task_result = self.auto_add_and_complete_task(f"Rename folder '{old_name}' to '{new_name}'")
            
            return {
                "success": True, 
                "message": f"Renamed folder from '{old_name}' to '{new_name}'",
                "task_added": task_result["success"],
                "task_id": task_result.get("task_id") if task_result["success"] else None
            }
        
        except Exception as e:
            return {"success": False, "message": f"Error renaming folder: {str(e)}"}
    
    def list_files(self, subfolder: str = "", file_extension: str = None) -> Dict[str, Any]:
        """List files in Desktop or Desktop subfolder only"""
        try:
            if subfolder:
                folder_path = os.path.join(self.desktop_path, subfolder)
            else:
                folder_path = self.desktop_path
            
            if not self.is_safe_path(folder_path):
                return {"success": False, "message": "Access denied: Can only access Desktop and its subfolders"}
            
            if not os.path.exists(folder_path):
                return {"success": False, "message": f"Folder not found: {subfolder if subfolder else 'Desktop'}"}
            
            all_items = os.listdir(folder_path)
            files = []
            folders = []
            
            for item in all_items:
                item_path = os.path.join(folder_path, item)
                if os.path.isfile(item_path):
                    if file_extension:
                        if item.lower().endswith(file_extension.lower()):
                            files.append({
                                "name": item,
                                "full_path": item_path,
                                "size": os.path.getsize(item_path),
                                "type": "file"
                            })
                    else:
                        files.append({
                            "name": item,
                            "full_path": item_path,
                            "size": os.path.getsize(item_path),
                            "type": "file"
                        })
                elif os.path.isdir(item_path):
                    folders.append({
                        "name": item,
                        "full_path": item_path,
                        "type": "folder"
                    })
            
            return {
                "success": True, 
                "files": files,
                "folders": folders,
                "directory": folder_path,
                "file_count": len(files),
                "folder_count": len(folders)
            }
        
        except Exception as e:
            return {"success": False, "message": f"Error listing files: {str(e)}"}
    
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Return the list of available tools for the AI"""
        return [
            # Task Management Tools
            {
                "name": "add_task",
                "description": "Add a new task to the to-do list",
                "parameters": {
                    "task_description": "string - Description of the task to add"
                }
            },
            {
                "name": "list_tasks",
                "description": "Get all current tasks from the to-do list",
                "parameters": {}
            },
            {
                "name": "complete_task",
                "description": "Mark a task as completed",
                "parameters": {
                    "task_id": "integer - ID of the task to complete"
                }
            },
            {
                "name": "delete_task",
                "description": "Permanently delete a task from the to-do list",
                "parameters": {
                    "task_id": "integer - ID of the task to delete"
                }
            },
            {
                "name": "clear_completed_tasks",
                "description": "Remove all completed tasks from the list",
                "parameters": {}
            },
            {
                "name": "get_task_stats",
                "description": "Get statistics about total, completed, and pending tasks",
                "parameters": {}
            },
            # JSON File Operations (Desktop only)
            {
                "name": "read_json_file",
                "description": "Read and display contents of a JSON file on Desktop",
                "parameters": {
                    "filename": "string - Name of the JSON file to read (must be on Desktop)"
                }
            },
            {
                "name": "write_json_file",
                "description": "Write content to a JSON file on Desktop",
                "parameters": {
                    "filename": "string - Name of the JSON file to write",
                    "content": "dict - Content to write to the file"
                }
            },
            # Secure File System Tools (Desktop only)
            {
                "name": "create_folder",
                "description": "Create a new folder on Desktop and automatically add it as a completed task",
                "parameters": {
                    "folder_name": "string - Name of the folder to create on Desktop"
                }
            },
            {
                "name": "delete_folder",
                "description": "Delete an empty folder from Desktop and automatically add it as a completed task",
                "parameters": {
                    "folder_name": "string - Name of the folder to delete from Desktop"
                }
            },
            {
                "name": "rename_folder",
                "description": "Rename a folder on Desktop and automatically add it as a completed task",
                "parameters": {
                    "old_name": "string - Current name of the folder",
                    "new_name": "string - New name for the folder"
                }
            },
            {
                "name": "list_files",
                "description": "List files and folders on Desktop or in Desktop subfolders only",
                "parameters": {
                    "subfolder": "string (optional) - Subfolder name within Desktop",
                    "file_extension": "string (optional) - Filter by file extension"
                }
            }
        ]


# Test the server
if __name__ == "__main__":
    server = LocalMCPServer()
    
    print("=== Testing Thread-Safe Database Operations ===")
    
    # Test adding a task
    result = server.add_task("Test thread-safe task addition")
    print("Add task result:", result)
    
    # Test listing tasks
    result = server.list_tasks()
    print("List tasks result:", result)
