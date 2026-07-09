import pytest
import os
import tempfile
from jarvis.indices.code_index import CodeIndex, CodeItem

class TestCodeIndex:
    
    @pytest.fixture
    def temp_workspace(self):
        with tempfile.TemporaryDirectory() as tmp:
            # Create a sample structure
            # main.py
            with open(os.path.join(tmp, "main.py"), "w") as f:
                f.write('"""Main module."""\n\ndef main():\n    """Run the app."""\n    pass\n')
            
            # subdir/utils.py
            os.makedirs(os.path.join(tmp, "subdir"), exist_ok=True)
            with open(os.path.join(tmp, "subdir", "utils.py"), "w") as f:
                f.write('class Helper:\n    """A helper class."""\n    def do_help(self): pass\n')
                
            yield tmp

    def test_indexing_files(self, temp_workspace):
        index = CodeIndex(root=temp_workspace)
        index.build_index() # Replaced index_files() with build_index() based on read file
        
        # Internal implementation detail: self._index is dict, self.items was in my head but not in file?
        # File has snapshot() method.
        items = index.snapshot()
        assert len(items) > 0
        filenames = [os.path.basename(i.file_path) for i in items]
        assert "main.py" in filenames
        assert "utils.py" in filenames
        # Check class
        assert "Helper" in filenames
        # Check method
        assert "Helper.do_help" in filenames

    def test_search(self, temp_workspace):
        index = CodeIndex(root=temp_workspace)
        index.build_index()
        
        results = index.search("Helper")
        assert len(results) >= 1
        assert results[0].name == "Helper"
        
        results = index.search("Run the app") # Search docstring
        assert len(results) >= 1
        # The file item has name="main.py"
        assert results[0].name == "main.py"
        
