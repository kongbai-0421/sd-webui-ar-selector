# Advanced Resolution Selector

English | [中文](README_zh.md)

Advanced Resolution Selector adds a compact preset-resolution and custom-bucket panel to Forge/WebUI. It places common 1024-base, 1280-base, and 1536-base aspect ratios near the generation controls and can save custom base and width/height presets.

## Features

- Preset resolution buttons for square, landscape, and portrait ratios.
- 1024-base presets for standard SDXL/Anima-style generation.
- 1280-base presets for quick HD bucket resolution setup.
- 1536-base presets for high-VRAM workflows.
- Enter any base resolution divisible by 64 to generate and save a matching bucket quick-preset bar.
- Custom base-resolution tabs include a delete `×` with a second confirmation prompt.
- Custom width/height input with automatic ratio calculation.
- Save, apply, and delete custom presets.
- Presets are stored in `custom_resolutions.json` inside the extension folder.
- Custom base resolutions are stored in `base_resolution_presets.json` inside the extension folder.
- Settings-page UI language switch: `zh` and `en`.

## Installation

1. Copy this folder to your WebUI/Forge `extensions` directory.
2. Restart WebUI, or use Reload UI.
3. Open txt2img or img2img. The panel appears near the width/height controls.

## Usage

- Click a preset button to set width and height immediately.
- In the custom tab, enter a base resolution divisible by 64 to calculate and add a new quick-preset bar.
- Click the `×` on a custom base-resolution tab and confirm twice to delete that quick-preset bar.
- Use the custom tab to enter any width/height pair.
- Save a custom pair with a name, or leave the name empty to generate one from the ratio and size.
- Select a saved custom preset to apply or delete it.

## Preset Groups

- **Square**: 1:1 sizes.
- **Landscape**: wide formats such as 4:3, 16:9, 21:9, and panorama.
- **Portrait**: vertical variants of the same common ratios.

## Language Setting

Use the **UI language** selector in the panel to switch between English and Chinese. The extension saves the option and refreshes the plugin panel without reloading the whole page.

## Notes

- The extension only writes to width/height controls; it does not change samplers, models, prompts, or generation logic.
- Large 1536-base presets may require more VRAM.
