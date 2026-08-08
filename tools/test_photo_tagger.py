import importlib.util
import struct
import tempfile
import unittest
import zlib
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "photo_tagger", Path(__file__).parent / "photo-tagger.py"
)
photo_tagger = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(photo_tagger)


def make_png(path, width, height):
    """Собирает минимальный валидный PNG заданного размера."""
    sig = b"\x89PNG\r\n\x1a\n"
    ihdr_body = b"IHDR" + struct.pack(">II", width, height) + bytes([8, 2, 0, 0, 0])
    ihdr = struct.pack(">I", len(ihdr_body) - 4) + ihdr_body
    ihdr += struct.pack(">I", zlib.crc32(ihdr_body) & 0xFFFFFFFF)
    path.write_bytes(sig + ihdr)


def make_jpeg(path, width, height):
    """Собирает минимальный JPEG с SOF0-маркером заданного размера."""
    soi = b"\xff\xd8"
    sof_body = bytes([8]) + struct.pack(">HH", height, width) + bytes([3])
    sof = b"\xff\xc0" + struct.pack(">H", len(sof_body) + 2) + sof_body
    path.write_bytes(soi + sof + b"\xff\xd9")


class TestImageSize(unittest.TestCase):
    def test_png_size(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "a.png"
            make_png(p, 4032, 3024)
            self.assertEqual(photo_tagger.image_size(p), (4032, 3024))

    def test_jpeg_size(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "a.jpg"
            make_jpeg(p, 1920, 1080)
            self.assertEqual(photo_tagger.image_size(p), (1920, 1080))

    def test_unknown_format_returns_none(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "a.txt"
            p.write_bytes(b"not an image at all")
            self.assertIsNone(photo_tagger.image_size(p))

    def test_orientation(self):
        self.assertEqual(photo_tagger.orientation(4032, 3024), "landscape")
        self.assertEqual(photo_tagger.orientation(3024, 4032), "portrait")
        self.assertEqual(photo_tagger.orientation(1000, 1000), "square")


class TestTsvStorage(unittest.TestCase):
    def test_load_missing_file_returns_empty(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(photo_tagger.load_entries(Path(d) / "nope.tsv"), {})

    def test_save_then_load_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            tsv = Path(d) / "photos.tsv"
            rows = [
                ("IMG_001.jpg", "руки за кругом", "дети;керамика", 4032, 3024, "landscape"),
                ("IMG_002.jpg", "готовая ваза", "керамика", 3024, 4032, "portrait"),
            ]
            photo_tagger.save_rows(tsv, rows)
            loaded = photo_tagger.load_entries(tsv)
            self.assertEqual(loaded["IMG_001.jpg"]["description"], "руки за кругом")
            self.assertEqual(loaded["IMG_001.jpg"]["tags"], "дети;керамика")
            self.assertEqual(loaded["IMG_002.jpg"]["tags"], "керамика")

    def test_header_and_column_order(self):
        with tempfile.TemporaryDirectory() as d:
            tsv = Path(d) / "photos.tsv"
            photo_tagger.save_rows(tsv, [("a.jpg", "описание", "дети", 100, 200, "portrait")])
            lines = tsv.read_text(encoding="utf-8").splitlines()
            self.assertEqual(
                lines[0], "file\tdescription\ttags\twidth\theight\torientation"
            )
            self.assertEqual(lines[1], "a.jpg\tописание\tдети\t100\t200\tportrait")

    def test_sanitize_strips_tabs_and_newlines(self):
        self.assertEqual(photo_tagger.sanitize("две\tчасти"), "две части")
        self.assertEqual(photo_tagger.sanitize("строка\nвторая"), "строка вторая")
        self.assertEqual(photo_tagger.sanitize("  обрезка  "), "обрезка")

    def test_saved_description_with_tab_does_not_break_format(self):
        with tempfile.TemporaryDirectory() as d:
            tsv = Path(d) / "photos.tsv"
            photo_tagger.save_rows(
                tsv, [("a.jpg", photo_tagger.sanitize("а\tб"), "", 10, 10, "square")]
            )
            loaded = photo_tagger.load_entries(tsv)
            self.assertEqual(loaded["a.jpg"]["description"], "а б")

    def test_legacy_file_without_tags_column_still_loads(self):
        """Файл от ранней версии инструмента не должен ломать чтение."""
        with tempfile.TemporaryDirectory() as d:
            tsv = Path(d) / "photos.tsv"
            tsv.write_text(
                "file\tdescription\twidth\theight\torientation\n"
                "a.jpg\tстарое описание\t100\t200\tportrait\n",
                encoding="utf-8",
            )
            loaded = photo_tagger.load_entries(tsv)
            self.assertEqual(loaded["a.jpg"]["description"], "старое описание")
            self.assertEqual(loaded["a.jpg"]["tags"], "")

    def test_clean_tags_keeps_only_known_values(self):
        known = photo_tagger.clean_tags(["дети", "керамика", "выдуманный тег"])
        self.assertEqual(known, "дети;керамика")

    def test_clean_tags_empty(self):
        self.assertEqual(photo_tagger.clean_tags([]), "")

    def test_tag_groups_are_non_empty_and_unique(self):
        all_tags = [t for _, tags in photo_tagger.TAG_GROUPS for t in tags]
        self.assertTrue(all_tags)
        self.assertEqual(len(all_tags), len(set(all_tags)), "теги не должны повторяться")


if __name__ == "__main__":
    unittest.main()
