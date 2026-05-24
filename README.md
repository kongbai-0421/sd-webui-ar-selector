# Advanced Resolution Selector

English | [中文](README_zh.md)

Advanced Resolution Selector adds a compact preset-resolution and custom-bucket panel to Forge/WebUI. It places common 1024-base and 1536-base aspect ratios near the generation controls and can save custom width/height presets.

## Features

- Preset resolution buttons for square, landscape, and portrait ratios.
- 1024-base presets for standard SDXL/Anima-style generation.
- 1536-base presets for high-VRAM workflows.
- Custom width/height input with automatic ratio calculation.
- Save, apply, and delete custom presets.
- Presets are stored in `custom_resolutions.json` inside the extension folder.
- Settings-page UI language switch: `zh` and `en`.

## Installation

1. Copy this folder to your WebUI/Forge `extensions` directory.
2. Restart WebUI, or use Reload UI.
3. Open txt2img or img2img. The panel appears near the width/height controls.

## Usage

- Click a preset button to set width and height immediately.
- Use the custom tab to enter any width/height pair.
- Save a custom pair with a name, or leave the name empty to generate one from the ratio and size.
- Select a saved custom preset to apply or delete it.

## Preset Groups

- **Square**: 1:1 sizes.
- **Landscape**: wide formats such as 4:3, 16:9, 21:9, and panorama.
- **Portrait**: vertical variants of the same common ratios.

## Language Setting

Open **Settings**, find **Advanced Resolution Selector**, and choose `zh` or `en`. Reload UI after changing the option.

## Notes

- The extension only writes to width/height controls; it does not change samplers, models, prompts, or generation logic.
- Large 1536-base presets may require more VRAM.
