# Icon Pack Template for ZenOS

An empty GitHub template for [ZenOS](https://github.com/xZenLabs/zen-os), KOReader,
and ZenPM icon packs. Add your own artwork; the builder, validation tests, and
automatic release workflow are already set up.

The packaging infrastructure comes from
[xZenLabs/solariconpack-zen](https://github.com/xZenLabs/solariconpack-zen).
This template contains no icon artwork or previews.

## Create a pack

1. Click **Use this template → Create a new repository**, or run:

   ```sh
   gh repo create OWNER/my-icon-pack --public --template xZenLabs/icon-pack-template --clone
   ```

2. Add your SVG or PNG files to the empty folders:

   ```text
   My Icons/
     pack.json
     Pack Icons/
     KOReader Icons/
     Supplementary Icons/
   ```

   Use filenames from [ICON-LIST.md](ICON-LIST.md) to replace application icons.
   Include only the designs you want to replace; missing icons use the bundled
   artwork. Keep filenames unique across the three folders.
3. Rename `My Icons` and update root `pack.json` and the style's `pack.json`.
   Set `id`, `name`, `version`, `author`, and `color`. Set `color` to `true` for
   color artwork or `false` for monochrome.
   A style folder named `My Icons` builds as `zen-my-icons` with the display name
   `My Icons for ZenOS`; use those same values in the style manifest so direct
   and repository builds agree. Root metadata supplies the shared version and
   author; each style supplies its own color setting.
4. Replace `LICENSE-ICONS.txt` with your icon credits and required license terms,
   then update this README with your pack's name and installation links.
5. Run the checks below and push to `main`. GitHub Actions publishes an installable
   ZIP containing one folder whose name matches the pack ID.

IDs may contain letters, numbers, dots, dashes, and underscores, starting with a
letter or number. A flat style folder also works. To include multiple styles,
add another style folder with its own manifest and artwork.

No Lua plugin is needed. The builder preserves source SVGs, cleans PNG metadata,
flattens the icon folders, and generates the existing ZenOS/KOReader/ZenPM aliases.
It validates manifests, SVG documents, and archive limits. SVGs are validated but
are not sanitized.

## Build and check

Requires Python 3 and the pinned Pillow dependency:

```sh
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r scripts/requirements.txt
python3 -m unittest discover -s scripts -p 'test_*.py'
python3 scripts/build-zen-packs.py
```

After adding artwork, the default output is `dist/zen-my-icons.zip`.
To build a style directly or override the packaged version:

```sh
python3 scripts/build-zen-packs.py "My Icons" --output dist --version 1.0.0
```

Tests pass on the empty scaffold. A manual build reports that no icon packs were
found until artwork is added; it never creates an empty installable ZIP.

## Releases

**Actions → Release Zen icon packs** runs on pushes to `main` and manually.
It installs dependencies and runs the tests. While the scaffold is empty, it
skips version selection, packaging, and publishing. Once you add artwork, the
same workflow builds and validates the packs and publishes their ZIPs.

A pushed increase in root `pack.json` releases that exact version. Otherwise,
including an initial release or manual run, the workflow increments the patch
number above the higher of the manifest version and existing release tags.
Runs are serialized.

## Installing your finished pack

Copy the release ZIP into `koreader/icons/zen/`. Under **Zen Settings → Interface**,
enable **Custom icons**, select the pack under **Custom icons → Custom icon pack**,
and restart KOReader. ZenOS validates and extracts the ZIP automatically.
See the [ZenOS icon-pack guide](https://github.com/xZenLabs/zen-os/blob/main/docs/icon-packs.md).

## License

Repository code is **AGPL-3.0**; see [LICENSE](LICENSE). Your icon artwork may use
a separate license; record it in `LICENSE-ICONS.txt`, which is included in release ZIPs.

Support ZenLabs projects on [Ko-fi](https://ko-fi.com/xzenlabs).
