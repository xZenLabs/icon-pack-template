# Icon Pack Template for ZenOS

A GitHub template for icon packs used by [ZenOS](https://github.com/xZenLabs/zen-os),
KOReader, and ZenPM. It includes the **Solar Colour** and **Solar Mono** packs as
working examples, plus the existing Solar builder, validation tests, and automatic
GitHub releases. Each example builds 300 SVG lookups.

Based on [xZenLabs/solariconpack-zen](https://github.com/xZenLabs/solariconpack-zen)
at revision `b02045f91185f1aee76f7b44ba3440812b089a6f`.

## Create your own pack

1. Click **Use this template → Create a new repository**. This creates an independent
   repository with fresh history. Or use:

   ```sh
   gh repo create OWNER/my-icon-pack --public --template xZenLabs/icon-pack-template --clone
   ```

2. Rename an example style folder and its three icon folders, then replace its
   SVGs with your artwork. Delete the unused example style. Keep the original
   icon filenames so ZenOS, KOReader, and ZenPM can find their replacements.
   Remove any unsupported designs; missing lookups use the bundled artwork.
3. Update root `pack.json` and each style's `pack.json`: set `id`, `name`,
   `version`, `author`, and `color`. IDs must contain only letters, numbers,
   dots, dashes, or underscores, starting with a letter or number. Set `color`
   to `true` for color artwork or `false` for monochrome.
4. For repository builds, each style folder name generates its ID and display
   name: `My Icons` becomes `zen-my-icons` and `My Icons for ZenOS`. Use those
   same values in the style manifest so direct and repository builds agree.
   Root metadata supplies the shared version and author; each style supplies
   its own `color` value.
5. Replace `LICENSE-ICONS.txt` with your source credits and the required icon
   license, remove the Solar preview PNGs, and update this README's name,
   screenshots, installation links, and credits. Repository code remains AGPL-3.0.
6. Run the checks below, then push to `main`. The release workflow runs the tests,
   builds every pack, checks its manifest version, and publishes the installable
   ZIPs. A repository generated from this template keeps the same workflow.

No Lua plugin is needed. `Pack Icons`, `KOReader Icons`, and `Supplementary Icons`
hold the source artwork. The builder flattens them into one installable folder,
preserves canonical filenames, and adds the existing SimpleUI and ZenOS/ZenPM
aliases. Do not repeat a filename across those folders. A flat pack folder with
SVGs and `pack.json` also works.

## Build and check

Requires Python 3 and the pinned Pillow dependency:

```sh
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r scripts/requirements.txt
python3 -m unittest discover -s scripts -p 'test_*.py'
python3 scripts/build-zen-packs.py
```

The example outputs are `dist/zen-solar-colour.zip` and `dist/zen-solar-mono.zip`.
To build one style or set an explicit version:

```sh
python3 scripts/build-zen-packs.py "Solar Mono" --output dist --version 1.0.0
```

Tests discover your packs automatically, verify source SVGs and manifests survive
the build, and exercise metadata validation, filename aliases, safe archive limits,
PNG cleaning, and release version selection. No Solar-specific icon count is
required for a new pack. SVGs are parsed and validated, but are not sanitized.

## Releases

**Actions → Release Zen icon packs** runs on pushes to `main` and manually.
An increased root manifest version is released exactly. Otherwise, including the
initial push and manual runs, the workflow increments the patch number above the
higher of the root version and existing release tags. Runs are serialized.

## Install an example

1. Download `zen-solar-colour.zip` or `zen-solar-mono.zip` from
   [the latest release](https://github.com/xZenLabs/icon-pack-template/releases/latest).
2. Copy the ZIP into `koreader/icons/zen/`, creating the folders if needed.
3. Under **Zen Settings → Interface**, enable **Custom icons** and select the
   pack under **Custom icons → Custom icon pack**.
4. Restart KOReader. ZenOS validates and extracts the ZIP automatically.

You can also extract the ZIP and copy its top-level pack folder into that directory.
To restore the defaults, disable **Custom icons** and restart KOReader.
See the [ZenOS icon-pack guide](https://github.com/xZenLabs/zen-os/blob/main/docs/icon-packs.md).
ZenPM replacements require a frontend that supports the selected ZenOS pack;
status-bar font glyphs and downloaded package logos retain their own artwork.

## Solar examples and licenses

| Example | Artwork | Output |
|---|---|---|
| Solar Colour | Soft pastel fills | `zen-solar-colour.zip` |
| Solar Mono | Black outlines | `zen-solar-mono.zip` |

![Solar Colour examples](Solar%20Colour/Full%20Icon%20Overview%20%28Colour%29.png)
![Solar Mono examples](Solar%20Mono/Full%20Icon%20Overview%20%28Mono%29.png)

- **Artwork:** Solar by **480 Design**, adapted by **pxlflux** and **xZenLabs**,
  under **CC BY 4.0**. Source geometry is unchanged in this template; packaging
  metadata and documentation are adapted. Retain [icon attribution](LICENSE-ICONS.txt)
  while redistributing any Solar artwork.
- **Original adaptation:** [pxlflux/solariconpack.koplugin](https://github.com/pxlflux/solariconpack.koplugin).
- **Builder and template packaging:** [xZenLabs](https://github.com/xZenLabs),
  under **AGPL-3.0**; see [LICENSE](LICENSE). Icon licensing is separate.

Support ZenLabs projects on [Ko-fi](https://ko-fi.com/xzenlabs).
