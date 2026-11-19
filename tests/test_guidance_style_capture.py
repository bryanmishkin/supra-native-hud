import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from capture_guidance_styles import inventory, DIRECTORIES

class StyleCapturePaths(unittest.TestCase):
    def test_coherent_nested_paths(self):
        root = DIRECTORIES[0]
        paths = [root + '/data/part.0', root + '/index']
        self.assertEqual(inventory('\n'.join(paths), root), sorted(paths))

    def test_reject_escape_shell_duplicates_and_unbounded_inventory(self):
        root = DIRECTORIES[0]
        for text in [root+'/../secret',root+'/a;id',root+'/x\n'+root+'/x',
                     root+'2/index',root+'//index',root+'/./index',
                     '\n'.join(root+'/file'+str(i) for i in range(2049))]:
            with self.subTest(text=text[:80]), self.assertRaises(ValueError):
                inventory(text,root)

if __name__ == '__main__':
    unittest.main()
