import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from extract_hvif_rdef import ExtractionError, extract_hvif, write_atomically


def resource(resource_id, chunks):
    body = "\n".join(f'  $"{chunk}"' for chunk in chunks)
    return f'resource({resource_id},"VECTOR:ICON") #\'VICN\' array {{\n{body}\n}};\n'


class ExtractHVIFRezTests(unittest.TestCase):
    def test_concatenates_chunks_in_source_byte_order(self):
        found_id, data = extract_hvif(resource(7, ["6e6369", "6600010203"]).encode())
        self.assertEqual(found_id, 7)
        self.assertEqual(data, b"ncif\x00\x01\x02\x03")

    def test_selects_id_when_multiple_icons_exist(self):
        text = (resource(7, ["6e63696601"]) + resource(8, ["6e63696602"])).encode()
        with self.assertRaisesRegex(ExtractionError, "multiple"):
            extract_hvif(text)
        self.assertEqual(extract_hvif(text, 8), (8, b"ncif\x02"))

    def test_rejects_missing_resource_bad_hex_odd_length_and_wrong_signature(self):
        cases = [
            (b"resource(1,\"ICON\") { $\"6e636966\" }", "no VECTOR:ICON"),
            (resource(1, ["6e63zz66"]), "malformed hexadecimal"),
            (resource(1, ["6e636966A"]), "odd number"),
            (resource(1, ["89504e470d0a"]), "does not begin"),
        ]
        for source, message in cases:
            with self.subTest(message=message), self.assertRaisesRegex(ExtractionError, message):
                extract_hvif(source.encode() if isinstance(source, str) else source)

    def test_rejects_unterminated_resource_and_non_ascii_source(self):
        with self.assertRaisesRegex(ExtractionError, "unterminated"):
            extract_hvif(b'resource(1,"VECTOR:ICON") { $"6e636966"')
        with self.assertRaisesRegex(ExtractionError, "not ASCII"):
            extract_hvif(b"\xff")

    def test_atomic_writer_preserves_exact_extracted_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "icon.hvif"
            write_atomically(target, b"ncif\x01")
            self.assertEqual(target.read_bytes(), b"ncif\x01")


if __name__ == "__main__":
    unittest.main()
