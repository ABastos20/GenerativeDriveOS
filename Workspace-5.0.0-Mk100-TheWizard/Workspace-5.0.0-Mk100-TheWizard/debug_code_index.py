import os
import tempfile
from jarvis.indices.code_index import CodeIndex

def debug_index():
    with tempfile.TemporaryDirectory() as tmp:
        print(f"DEBUG: Created temp dir {tmp}")
        
        # Create a sample structure
        main_py = os.path.join(tmp, "main.py")
        with open(main_py, "w") as f:
            f.write('"""Main module."""\n\ndef main():\n    """Run the app."""\n    pass\n')
        
        subdir = os.path.join(tmp, "subdir")
        os.makedirs(subdir, exist_ok=True)
        utils_py = os.path.join(subdir, "utils.py")
        with open(utils_py, "w") as f:
            f.write('class Helper:\n    """A helper class."""\n    def do_help(self): pass\n')
            
        print("DEBUG: Files created.")
        
        index = CodeIndex(root=tmp)
        index.build_index()
        
        items = index.snapshot()
        print(f"DEBUG: Items found: {len(items)}")
        for item in items:
            print(f"  - {item.name} ({item.kind}) in {item.path}")
            
        filenames = [os.path.basename(i.path) for i in items]
        print(f"DEBUG: Filenames: {filenames}")
        
        # Search test
        results = index.search("Helper")
        print(f"DEBUG: Search 'Helper' found: {len(results)}")
        if results:
            print(f"  - Top result: {results[0].name}")

if __name__ == "__main__":
    debug_index()
