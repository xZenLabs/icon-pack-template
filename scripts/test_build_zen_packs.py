"""Run with python3 -m unittest discover -s scripts -p 'test_*.py'."""

import importlib.util
from io import BytesIO, StringIO
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from PIL import Image, PngImagePlugin


spec = importlib.util.spec_from_file_location("builder", Path(__file__).with_name("build-zen-packs.py"))
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)
SVG = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"><path d="M0 0h48v48z"/></svg>'


class BuildPacksTest(unittest.TestCase):
    def test_repository_packs_build_installable_archives(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            packs = list(builder.pack_sources(builder.ROOT, output))
            if not packs:
                with patch("sys.argv", ["build-zen-packs.py", "--output", str(output)]), \
                        patch("sys.stderr", new=StringIO()) as errors:
                    with self.assertRaises(SystemExit) as error:
                        builder.main()
                self.assertEqual(error.exception.code, 1)
                self.assertIn("No icon packs found", errors.getvalue())
                self.assertFalse(list(output.iterdir()))
                return
            with patch("sys.argv", ["build-zen-packs.py", "--output", str(output)]):
                builder.main()
            self.assertEqual(len(list(output.glob("*.zip"))), len(packs))
            for pack, directories in packs:
                with self.subTest(pack=pack):
                    metadata = json.loads((pack / "pack.json").read_text())
                    prefix = metadata["id"] + "/"
                    destination = output / (metadata["id"] + ".zip")
                    with zipfile.ZipFile(destination) as archive:
                        self.assertIsNone(archive.testzip())
                        self.assertTrue(all(name.startswith(prefix) for name in archive.namelist()))
                        self.assertLessEqual(len(archive.namelist()), 512)
                        self.assertEqual(json.loads(archive.read(prefix + "pack.json")), metadata)
                        for directory in directories:
                            for path in directory.rglob("*.svg"):
                                self.assertEqual(archive.read(prefix + path.name), path.read_bytes())
                        for name in ("LICENSE", "LICENSE-ICONS.txt", "README.md"):
                            self.assertIn(prefix + name, archive.namelist())
                    with patch("sys.argv", ["build-zen-packs.py", str(pack),
                                            "--output", str(output), "--version", "2.3.4"]):
                        builder.main()
                    with zipfile.ZipFile(destination) as archive:
                        self.assertEqual(json.loads(archive.read(prefix + "pack.json")),
                                         dict(metadata, version="2.3.4"))

    def test_empty_scaffold_builds_after_artwork_is_added(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output = root / "dist"
            pack = root / "My Icons"
            metadata = {"schema_version": 1, "id": "zen-my-icons", "name": "My Icons for ZenOS",
                        "version": "1.0.0", "author": "Your name", "color": True}
            (root / "pack.json").write_text(json.dumps(metadata))
            for name in ("navbar", "controls", "launcher", "zenpm", "lookup",
                         "menus", "reader", "device", "koreader"):
                directory = pack / name
                directory.mkdir(parents=True)
                (directory / ".gitkeep").touch()
            (pack / "pack.json").write_text(json.dumps(metadata))
            self.assertFalse(list(builder.pack_sources(root, output)))
            (pack / "navbar/library.svg").write_bytes(SVG)
            self.assertEqual(len(list(builder.pack_sources(root, output))), 1)
            with patch("sys.argv", ["build-zen-packs.py", str(root), "--output", str(output)]):
                builder.main()
            with zipfile.ZipFile(output / "zen-my-icons.zip") as archive:
                self.assertEqual(archive.read("zen-my-icons/library.svg"), SVG)
                self.assertEqual(json.loads(archive.read("zen-my-icons/pack.json")), metadata)
                self.assertFalse(any(name.endswith(".gitkeep") for name in archive.namelist()))

    def test_grouped_pack_builds_directly_and_keeps_explicit_alias_artwork(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            pack, output = root / "Grouped", root / "output"
            files = {
                "navbar/tab_books.svg": SVG,
                "controls/quick_search.svg": SVG,
                "koreader/appbar.search.svg": SVG.replace(b"48", b"24"),
                "koreader/book_open.svg": SVG,
                "koreader/appbar.textsize.svg": SVG,
                "navbar/tab_left.svg": SVG,
                "navbar/tab_right.svg": SVG,
                "zenpm/packages.svg": SVG,
            }
            for name, data in files.items():
                path = pack / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
            (pack / "pack.json").write_text(json.dumps({
                "schema_version": 1, "id": "zen-grouped", "name": "Grouped for ZenOS",
            }))
            for source in (root, pack):
                with self.subTest(source=source):
                    self.assertEqual(list(builder.pack_sources(source, output)), [(pack, [pack])])
                    with patch("sys.argv", ["build-zen-packs.py", str(source),
                                            "--output", str(output)]):
                        builder.main()
                    with zipfile.ZipFile(output / "zen-grouped.zip") as archive:
                        self.assertTrue(all(len(Path(name).parts) == 2
                                            for name in archive.namelist()))
                        for name, data in files.items():
                            self.assertEqual(archive.read("zen-grouped/" + Path(name).name), data)

    def test_color_metadata_survives_repository_and_direct_builds(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output = root / "output"
            manifest = {"version": "2.3.4", "author": "Repository artist", "color": True}
            (root / "pack.json").write_text(json.dumps(manifest))
            for name, color in (("Color", True), ("Mono", False)):
                pack = root / name
                icons = pack / "Pack Icons"
                icons.mkdir(parents=True)
                (icons / "home.svg").write_bytes(SVG)
                (pack / "pack.json").write_text(json.dumps(dict(manifest, color=color)))
            for source in (root, root / "Color", root / "Mono"):
                with self.subTest(source=source), patch("sys.argv", [
                        "build-zen-packs.py", str(source), "--output", str(output),
                        "--version", "3.4.5"]):
                    builder.main()
                    for pack, _ in builder.pack_sources(source, output):
                        pack_id = builder.zen_id(pack.name)
                        with zipfile.ZipFile(output / (pack_id + ".zip")) as archive:
                            metadata = json.loads(archive.read(pack_id + "/pack.json"))
                            self.assertIs(metadata["color"], pack.name == "Color")
                            self.assertEqual(metadata["version"], "3.4.5")
                            self.assertEqual(metadata["author"], "Repository artist")
            for manifest_path in (root / "pack.json", root / "Mono" / "pack.json"):
                for invalid in (None, "false", 0, 1, [], {}):
                    with self.subTest(manifest=manifest_path, color=invalid):
                        manifest_path.write_text(json.dumps(dict(manifest, color=invalid)))
                        with patch("sys.argv", ["build-zen-packs.py", str(root),
                                                "--output", str(output)]):
                            with patch("sys.stderr", new=StringIO()) as errors:
                                with self.assertRaises(SystemExit):
                                    builder.main()
                            self.assertIn("color must be a boolean", errors.getvalue())
                manifest_path.write_text(json.dumps(manifest))

    def test_repository_pack_json_metadata_and_cli_override(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            pack, output = root / "Pack", root / "output"
            pack.mkdir()
            (pack / "sui_menu.svg").write_bytes(SVG)
            (pack / "pack.lua").write_text(
                'return { name = "Pack", version = "1.0.0", author = "Old artist", }')
            manifest = {"schema_version": 1, "id": "zen-example", "name": "Example for ZenOS",
                        "version": "2.3.4", "author": "Repository artist"}
            (root / "pack.json").write_text(json.dumps(manifest))
            for options, expected in (([], "2.3.4"), (["--version", "3.0.0"], "3.0.0")):
                with self.subTest(options=options), patch("sys.argv", [
                        "build-zen-packs.py", str(root), "--output", str(output), *options]):
                    builder.main()
                    with zipfile.ZipFile(output / "zen-pack.zip") as archive:
                        metadata = json.loads(archive.read("zen-pack/pack.json"))
                        self.assertEqual(metadata, dict(manifest, id="zen-pack",
                                                        name="Pack for ZenOS", version=expected))
            (pack / "pack.json").write_text(json.dumps(manifest))
            with patch("sys.argv", ["build-zen-packs.py", str(pack), "--output", str(output)]):
                builder.main()
            with zipfile.ZipFile(output / "zen-example.zip") as archive:
                self.assertEqual(json.loads(archive.read("zen-example/pack.json")), manifest)
            (pack / "pack.json").write_text(json.dumps(dict(manifest, id="../unsafe")))
            with patch("sys.argv", ["build-zen-packs.py", str(pack), "--output", str(output)]):
                with self.assertRaises(SystemExit), patch("sys.stderr"):
                    builder.main()

    def test_custom_png_map_strips_metadata_and_appended_zip_preserving_pixels(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            pack, output = root / "input", root / "output"
            pack.mkdir()
            output.mkdir()
            marker = root / "must-not-exist"
            (pack / "pack.lua").write_text(
                f'os.execute("touch {marker}")\n'
                'return { name = "Night Owl", author = "Test artist", version = "2.3.4",\n'
                'map = { ["sui_action_homescreen"] = "house image.png", sui_search = "lens.svg", }, }\n')
            (pack / "lens.svg").write_bytes(SVG)
            pixels = Image.new("RGBA", (2, 2), (12, 34, 56, 128))
            pixels.putpixel((1, 1), (200, 150, 100, 0))
            metadata = PngImagePlugin.PngInfo()
            metadata.add_text("payload", "metadata must be discarded")
            metadata.add(b"ruSt", b"hidden private chunk")
            original = BytesIO()
            pixels.save(original, format="PNG", pnginfo=metadata, icc_profile=b"fake ICC payload")
            appended = BytesIO()
            with zipfile.ZipFile(appended, "w") as archive:
                archive.writestr("hidden.lua", "untrusted appended file")
            source = original.getvalue() + appended.getvalue()
            (pack / "house image.png").write_bytes(source)

            destination = builder.build_pack(pack, [pack], pack, output, None)

            self.assertFalse(marker.exists())
            self.assertEqual((pack / "house image.png").read_bytes(), source)
            with zipfile.ZipFile(destination) as archive:
                prefix = "zen-night-owl/"
                manifest = json.loads(archive.read(prefix + "pack.json"))
                self.assertEqual(manifest["id"], "zen-night-owl")
                self.assertEqual(manifest["version"], "2.3.4")
                self.assertEqual(manifest["author"], "Test artist")
                self.assertEqual(archive.read(prefix + "appbar.search.svg"), SVG)
                clean = archive.read(prefix + "home.png")
                self.assertEqual(clean, archive.read(prefix + "house-image.png"))
                self.assertNotIn(prefix + "pack.lua", archive.namelist())
            with Image.open(BytesIO(clean)) as image:
                self.assertEqual(image.info, {})
                self.assertEqual(image.convert("RGBA").tobytes(), pixels.tobytes())
            offset, chunks = 8, []
            while offset < len(clean):
                size = struct.unpack_from(">I", clean, offset)[0]
                chunks.append(clean[offset + 4:offset + 8])
                offset += size + 12
            self.assertEqual(offset, len(clean))
            self.assertEqual(chunks, [b"IHDR", b"IDAT", b"IEND"])

    def test_flat_pack_without_manifest_uses_svg_and_png_slot_names(self):
        with tempfile.TemporaryDirectory() as temporary:
            pack = Path(temporary) / "Minimal"
            output = Path(temporary) / "output"
            pack.mkdir()
            output.mkdir()
            (pack / "sui_menu.svg").write_bytes(SVG)
            Image.new("P", (1, 1)).save(pack / "sui_action_wifi_toggle.png")
            Image.new("RGBA", (1, 1)).save(pack / "HOME.PNG")
            self.assertEqual(list(builder.pack_sources(pack, output)), [(pack, [pack])])
            destination = builder.build_pack(pack, [pack], pack, output, "9.0")
            with zipfile.ZipFile(destination) as archive:
                self.assertIn("zen-minimal/appbar.menu.svg", archive.namelist())
                self.assertIn("zen-minimal/quick_wifi.png", archive.namelist())
                self.assertIn("zen-minimal/home.png", archive.namelist())
                self.assertNotIn("zen-minimal/HOME.png", archive.namelist())
                self.assertEqual(json.loads(archive.read("zen-minimal/pack.json"))["version"], "9.0")

    def test_bad_pngs_are_rejected_without_replacing_a_zip(self):
        with tempfile.TemporaryDirectory() as temporary:
            pack = Path(temporary) / "Broken"
            output = Path(temporary) / "output"
            pack.mkdir()
            output.mkdir()
            destination = output / "zen-broken.zip"
            destination.write_bytes(b"previous release")
            valid = BytesIO()
            Image.new("RGBA", (2, 2)).save(valid, format="PNG")
            animated = BytesIO()
            Image.new("RGBA", (2, 2), "red").save(
                animated, format="PNG", save_all=True,
                append_images=[Image.new("RGBA", (2, 2), "blue")])
            for name, data in {"empty": b"", "renamed SVG": SVG,
                               "truncated": valid.getvalue()[:24], "animated": animated.getvalue()}.items():
                with self.subTest(name=name):
                    (pack / "icon.png").write_bytes(data)
                    with self.assertRaises((ValueError, OSError, SyntaxError)):
                        builder.build_pack(pack, [pack], pack, output, None)
                    self.assertEqual(destination.read_bytes(), b"previous release")
            (pack / "icon.png").write_bytes(valid.getvalue())
            with patch.object(Image, "MAX_IMAGE_PIXELS", 3):
                with self.assertRaises(Image.DecompressionBombWarning):
                    builder.clean_icon(pack / "icon.png")

    def test_duplicates_missing_maps_and_symlinks_fail(self):
        with tempfile.TemporaryDirectory() as temporary:
            pack = Path(temporary) / "Bad"
            output = Path(temporary) / "output"
            pack.mkdir()
            output.mkdir()
            (pack / "home.svg").write_bytes(SVG)
            second = pack / "second"
            second.mkdir()
            (second / "HOME.svg").write_bytes(SVG)
            with self.assertRaisesRegex(ValueError, "Duplicate"):
                builder.build_pack(pack, [pack], pack, output, None)
            (second / "HOME.svg").unlink()
            (pack / "pack.lua").write_text('return { map = { sui_menu = "missing.svg", }, }')
            with self.assertRaisesRegex(ValueError, "missing mapped icon"):
                builder.build_pack(pack, [pack], pack, output, None)
            (pack / "pack.lua").unlink()
            (pack / "linked.svg").symlink_to(pack / "home.svg")
            with self.assertRaisesRegex(ValueError, "Unsafe"):
                builder.build_pack(pack, [pack], pack, output, None)

    def test_discovers_mixed_variants_and_ignores_generated_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            named, plain, output = root / "Named", root / "Plain", root / "output"
            for directory in (named, plain, output):
                directory.mkdir()
                (directory / "sui_menu.svg").write_bytes(SVG)
            (named / "pack.lua").write_text('return { name = "Named", }')
            (output / "pack.lua").write_text('return { name = "Generated", }')
            self.assertEqual(list(builder.pack_sources(root, output)),
                             [(named, [named]), (plain, [plain])])
            (named / "pack.lua").write_text('return { name = computed_name(), }')
            with self.assertRaisesRegex(ValueError, "literal quoted string"):
                builder.lua_strings(named / "pack.lua")
            self.assertEqual(builder.zen_id("Lumière"), "zen-lumiere")
            self.assertRegex(builder.zen_id("夜猫"), r"^zen-[a-f0-9]{12}$")


if __name__ == "__main__":
    unittest.main()
