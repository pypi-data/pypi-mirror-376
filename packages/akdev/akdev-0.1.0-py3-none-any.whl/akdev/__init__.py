"""AKDev - Development tools by Aarush Kukreja"""
__version__ = "0.1.0"

def debug_info(obj):
    """Get debug information about an object"""
    return {
        "type": type(obj).__name__,
        "value": str(obj),
        "size": len(str(obj)),
        "repr": repr(obj)
    }

def format_code(code):
    """Basic code formatting"""
    return f"# AKDev formatted code\n{code.strip()}\n# End of formatted code"

class DevLogger:
    def __init__(self, name="AKDev"):
        self.name = name
        self.logs = []
    
    def log(self, message):
        entry = f"[{self.name}] {message}"
        self.logs.append(entry)
        print(entry)
        return entry
    
    def get_logs(self):
        return self.logs.copy()
