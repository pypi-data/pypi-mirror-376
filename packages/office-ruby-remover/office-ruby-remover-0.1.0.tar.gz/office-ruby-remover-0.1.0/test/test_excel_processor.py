import os
import sys
import unittest
from pathlib import Path
from openpyxl import Workbook, load_workbook

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from excel.remove_excel_ruby import remove_excel_ruby

class TestExcelRubyRemoval(unittest.TestCase):
    def setUp(self):
        """テスト実行前の準備"""
        # テストファイルのパスを設定
        self.test_dir = Path(__file__).parent / "test_files"
        self.test_dir.mkdir(exist_ok=True)
        
        self.input_file = self.test_dir / "A案件（名鉄）_IN_原紙補足資料.xlsx"
        self.output_file = self.test_dir / "test_output.xlsx"

    def test_remove_ruby_success(self):
        """ルビの削除が正常に行われることをテスト"""
        # ルビを削除
        result = remove_excel_ruby(str(self.input_file), str(self.output_file), overwrite=True)

        # 結果の検証
        self.assertEqual(result, 0)
        self.assertTrue(self.output_file.exists())

if __name__ == '__main__':
    unittest.main(exit=False)
