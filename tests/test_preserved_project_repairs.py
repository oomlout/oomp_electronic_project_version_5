import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

class PreservedProjectRepairs(unittest.TestCase):
    def test_non_applicable_jumper_features_have_no_reconstructed_folders(self):
        root = ROOT / "parts/oomp_project_github_sparkfun_spark_fun_qwiic_directional_pad_qwiic_directional_pad_current/data/generated_data/components"
        for reference in ("JP1", "JP2", "JP3"):
            self.assertFalse((root / reference).exists())

    def test_buspirate_j302_canonical_rotation_is_corrected(self):
        pcb = ROOT / "parts/oomp_project_github_dangerousprototypes_buspirate5_hardware_5_rev10a/data/kicad_file.kicad_pcb"
        original = ROOT / "parts/oomp_project_github_dangerousprototypes_buspirate5_hardware_5_rev10a/data/original/kicad_file.kicad_pcb"
        self.assertIn('(at 129.9 116.82 180)', pcb.read_text(encoding="utf-8"))
        self.assertIn('(at 129.9 116.82)', original.read_text(encoding="utf-8"))
