import modules.scripts as scripts
import gradio as gr
import platform
import ctypes
import os
import json
import logging
import math
from pathlib import Path

from fastapi import Request
from modules import script_callbacks, shared

logger = logging.getLogger("adv_ar_selector")
LANGUAGE_OPTION = "adv_ar_selector_language"
LANGUAGE_CHOICES = ("zh", "en")
EXTENSION_DIR = Path(__file__).resolve().parents[1]
LANG = {
    "zh": {
        "intro_language": "界面语言",
        "language_saved": "界面语言已保存，正在刷新以应用全部控件文字。",
        "language_save_failed": "界面语言保存失败，请检查控制台日志。",
        "title": "高级分辨率与自定义桶",
        "accordion": "预设分辨率与自定义比例",
        "tab_1024": "1024 基准 (标准)",
        "tab_1280": "1280 基准 (高清)",
        "tab_1536": "1536 基准 (超高分)",
        "tab_base_custom": "基准",
        "tab_custom": "自定义 & 保存",
        "square": "方形 (Square)",
        "landscape": "横向 (Landscape)",
        "portrait": "竖向 (Portrait)",
        "note_widescreen": "宽银幕",
        "note_cinematic": "电影",
        "note_ultrawide": "超宽",
        "note_panorama": "全景",
        "note_vertical_widescreen": "竖银幕",
        "note_vertical": "竖向",
        "note_narrow": "极窄",
        "note_strip": "竖条",
        "base_quick_title": "基础分辨率快速设置",
        "base_quick_hint": "输入 64 的倍数，自动计算桶分辨率并添加到快速设置栏。",
        "base_quick_placeholder": "例如: 1600",
        "base_quick_add": "添加到快速设置栏",
        "base_quick_invalid": "请输入一个大于 0 且为 64 倍数的整数。",
        "base_quick_added": "已添加 {base} 基准快速设置，正在刷新界面。",
        "base_quick_exists": "{base} 基准快速设置已存在。",
        "base_quick_failed": "保存基础分辨率失败，请检查控制台日志。",
        "base_quick_delete_confirm": "删除 {base} 基准快速设置？",
        "base_quick_delete_confirm_final": "再次确认删除 {base} 基准预设？此操作会刷新界面。",
        "base_quick_deleted": "已删除 {base} 基准快速设置。",
        "base_quick_delete_failed": "删除基础分辨率失败，请检查控制台日志。",
        "custom_width": "自定义宽度",
        "custom_height": "自定义高度",
        "auto_ratio": "自动计算比例",
        "preset_name": "预设名称 (留空则自动生成)",
        "preset_name_placeholder": "例如: 宽屏电影 16:9",
        "save_preset": "计算并保存为预设",
        "saved_presets": "已保存的自定义预设",
        "apply_preset": "应用选中预设",
        "delete_preset": "删除选中预设",
    },
    "en": {
        "intro_language": "UI language",
        "language_saved": "UI language saved. Reloading to apply all control labels.",
        "language_save_failed": "Failed to save UI language. Check the console log.",
        "title": "Advanced Resolution and Custom Buckets",
        "accordion": "Preset Resolutions and Custom Ratios",
        "tab_1024": "1024 Base (Standard)",
        "tab_1280": "1280 Base (HD)",
        "tab_1536": "1536 Base (Ultra High)",
        "tab_base_custom": "Base",
        "tab_custom": "Custom & Save",
        "square": "Square",
        "landscape": "Landscape",
        "portrait": "Portrait",
        "note_widescreen": "Widescreen",
        "note_cinematic": "Cinema",
        "note_ultrawide": "Ultrawide",
        "note_panorama": "Panorama",
        "note_vertical_widescreen": "Vertical widescreen",
        "note_vertical": "Vertical",
        "note_narrow": "Narrow",
        "note_strip": "Strip",
        "base_quick_title": "Base resolution quick preset",
        "base_quick_hint": "Enter a multiple of 64 to calculate bucket resolutions and add them to the quick preset bar.",
        "base_quick_placeholder": "Example: 1600",
        "base_quick_add": "Add to quick presets",
        "base_quick_invalid": "Enter a positive integer that is divisible by 64.",
        "base_quick_added": "Added the {base} base quick preset. Reloading the UI.",
        "base_quick_exists": "The {base} base quick preset already exists.",
        "base_quick_failed": "Failed to save the base resolution. Check the console log.",
        "base_quick_delete_confirm": "Delete the {base} base quick preset?",
        "base_quick_delete_confirm_final": "Confirm deletion of the {base} base preset? The UI will reload.",
        "base_quick_deleted": "Deleted the {base} base quick preset.",
        "base_quick_delete_failed": "Failed to delete the base resolution. Check the console log.",
        "custom_width": "Custom width",
        "custom_height": "Custom height",
        "auto_ratio": "Calculated ratio",
        "preset_name": "Preset name (auto-generated when empty)",
        "preset_name_placeholder": "Example: Cinematic 16:9",
        "save_preset": "Calculate and save preset",
        "saved_presets": "Saved custom presets",
        "apply_preset": "Apply selected preset",
        "delete_preset": "Delete selected preset",
    },
}
INTRO_EN = "Quickly set common 1024/1280/1536-base resolutions, calculate custom buckets and aspect ratios, and save reusable presets."
INTRO_ZH = "快速设置常用 1024/1280/1536 基准分辨率，计算自定义桶与比例，并保存可复用预设。"


def _language():
    value = getattr(shared.opts, LANGUAGE_OPTION, "zh")
    return value if value in LANGUAGE_CHOICES else "zh"


def _t(key):
    return LANG.get(_language(), LANG["zh"]).get(key, key)


def _html_attr(value):
    return str(value).replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;")


def _status_html(message, reload_ui=False):
    reload_attr = ' data-adv-ar-language-reload="1"' if reload_ui else ""
    return f'<span{reload_attr}>{_html_attr(message)}</span>'


def _choice_to_language(language):
    if language in LANGUAGE_CHOICES:
        return language
    return "zh" if language == "中文" else "en"


def _language_choice(language=None):
    return "中文" if _choice_to_language(language or _language()) == "zh" else "English"


def _intro_text(language=None):
    return INTRO_ZH if _choice_to_language(language or _language()) == "zh" else INTRO_EN


def _intro_default(language=None):
    return _intro_text(language or _language())


def _save_ui_language(language):
    language_code = _choice_to_language(language)
    try:
        if LANGUAGE_OPTION in shared.opts.data_labels:
            shared.opts.set(LANGUAGE_OPTION, language_code, run_callbacks=False)
        else:
            shared.opts.data[LANGUAGE_OPTION] = language_code
        shared.opts.save(shared.config_filename)
        return _intro_text(language_code), _status_html(LANG[language_code]["language_saved"], reload_ui=True)
    except Exception:
        logger.exception("Failed to save Advanced Resolution Selector UI language")
        return _intro_text(language_code), _status_html(LANG[language_code]["language_save_failed"])


def _intro_block():
    with gr.Row():
        intro_language = gr.Radio(
            choices=["English", "中文"],
            value=_language_choice(),
            label=_t("intro_language"),
        )
    intro = gr.Markdown(value=_intro_default())
    intro_status = gr.HTML(value="", elem_classes="adv-ar-language-status")
    intro_language.change(fn=_save_ui_language, inputs=[intro_language], outputs=[intro, intro_status], queue=False, show_progress=False)


def _setting_language():
    if LANGUAGE_OPTION in shared.opts.data_labels:
        return
    shared.opts.add_option(
        LANGUAGE_OPTION,
        shared.OptionInfo(
            "zh",
            "Advanced Resolution Selector language / 高级分辨率选择器语言",
            gr.Radio,
            {"choices": LANGUAGE_CHOICES},
            section=("advanced-resolution-selector", "Advanced Resolution Selector"),
            category_id="system",
        ).needs_reload_ui(),
    )


script_callbacks.on_ui_settings(_setting_language)

# 调用 Windows 系统 API，为后端进程声明高 DPI 感知 (适配 RTX 3090 4K 屏幕)
if platform.system() == "Windows":
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        pass

# 将自定义预设保存在插件目录下的 JSON 文件中
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PRESETS_FILE = os.path.join(BASE_DIR, "custom_resolutions.json")
BASE_PRESETS_FILE = os.path.join(BASE_DIR, "base_resolution_presets.json")
BUCKET_STEP = 64
BUILTIN_BASE_PRESETS = (1024, 1280, 1536)

CANONICAL_1024_BUCKETS = {
    "square": [("1:1", "", (1024, 1024))],
    "landscape": [
        ("5:4", "", (1152, 896)),
        ("4:3", "", (1152, 832)),
        ("3:2", "", (1216, 832)),
        ("16:9", "", (1344, 768)),
        ("1.85:1", "note_widescreen", (1408, 768)),
        ("2:1", "note_cinematic", (1472, 704)),
        ("21:9", "note_ultrawide", (1536, 640)),
        ("3:1", "note_panorama", (1728, 576)),
    ],
    "portrait": [
        ("4:5", "", (896, 1152)),
        ("3:4", "", (832, 1152)),
        ("2:3", "", (832, 1216)),
        ("9:16", "", (768, 1344)),
        ("1:1.85", "note_vertical_widescreen", (768, 1408)),
        ("1:2", "note_vertical", (704, 1472)),
        ("9:21", "note_narrow", (640, 1536)),
        ("1:3", "note_strip", (576, 1728)),
    ],
}

STATIC_RESOLUTION_SIZES = {
    1024: {
        "square": [(1024, 1024)],
        "landscape": [(1152, 896), (1152, 832), (1216, 832), (1344, 768), (1408, 768), (1472, 704), (1536, 640), (1728, 576)],
        "portrait": [(896, 1152), (832, 1152), (832, 1216), (768, 1344), (768, 1408), (704, 1472), (640, 1536), (576, 1728)],
    },
    1536: {
        "square": [(1536, 1536)],
        "landscape": [(1728, 1344), (1728, 1280), (1856, 1216), (2048, 1152), (2112, 1152), (2240, 1088), (2304, 960), (2560, 832)],
        "portrait": [(1344, 1728), (1280, 1728), (1216, 1856), (1152, 2048), (1152, 2112), (1088, 2240), (960, 2304), (832, 2560)],
    },
}


def _json_response(ok, message, **extra):
    payload = {"ok": ok, "message": message}
    payload.update(extra)
    return payload


def _round_to_bucket(value):
    return max(BUCKET_STEP, int(math.floor((float(value) / BUCKET_STEP) + 0.5)) * BUCKET_STEP)


def _valid_base_resolution(value):
    try:
        base = int(value)
    except (TypeError, ValueError):
        return None
    if base <= 0 or base % BUCKET_STEP != 0:
        return None
    return base


def _format_bucket_label(ratio, note_key, w, h):
    note_part = f" {_t(note_key)}" if note_key else ""
    return f"{ratio}{note_part} ({w}x{h})"


def _bucket_entries_for_base(base):
    if base in STATIC_RESOLUTION_SIZES:
        entries = {}
        for category, canonical_entries in CANONICAL_1024_BUCKETS.items():
            entries[category] = []
            sizes = STATIC_RESOLUTION_SIZES[base][category]
            for (ratio, note_key, _canonical_size), size in zip(canonical_entries, sizes):
                entries[category].append((ratio, note_key, size))
        return entries

    scale = base / 1024
    entries = {}
    for category, canonical_entries in CANONICAL_1024_BUCKETS.items():
        entries[category] = []
        for ratio, note_key, (canonical_w, canonical_h) in canonical_entries:
            if category == "square":
                size = (base, base)
            else:
                size = (_round_to_bucket(canonical_w * scale), _round_to_bucket(canonical_h * scale))
            entries[category].append((ratio, note_key, size))
    return entries


def build_resolution_set(base):
    base = _valid_base_resolution(base)
    if base is None:
        return {}

    result = {}
    for category, entries in _bucket_entries_for_base(base).items():
        result[category] = {}
        for ratio, note_key, (w, h) in entries:
            result[category][_format_bucket_label(ratio, note_key, w, h)] = (w, h)
    return result


def load_custom_base_presets():
    if not os.path.exists(BASE_PRESETS_FILE):
        return []
    try:
        with open(BASE_PRESETS_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)
        values = raw.get("bases", []) if isinstance(raw, dict) else raw
        presets = []
        for value in values:
            base = _valid_base_resolution(value)
            if base and base not in BUILTIN_BASE_PRESETS and base not in presets:
                presets.append(base)
        return presets
    except Exception:
        logger.exception("Failed to load Advanced Resolution Selector base presets")
        return []


def save_custom_base_presets(presets):
    values = []
    for value in presets:
        base = _valid_base_resolution(value)
        if base and base not in BUILTIN_BASE_PRESETS and base not in values:
            values.append(base)
    with open(BASE_PRESETS_FILE, "w", encoding="utf-8") as f:
        json.dump({"bases": values}, f, indent=4)


def all_base_presets():
    return list(BUILTIN_BASE_PRESETS) + load_custom_base_presets()


def add_custom_base_preset(base):
    base = _valid_base_resolution(base)
    if base is None:
        return _json_response(False, _t("base_quick_invalid"), bases=all_base_presets())
    if base in all_base_presets():
        return _json_response(False, _t("base_quick_exists").format(base=base), bases=all_base_presets())
    presets = load_custom_base_presets()
    presets.append(base)
    try:
        save_custom_base_presets(presets)
        return _json_response(True, _t("base_quick_added").format(base=base), bases=all_base_presets())
    except Exception:
        logger.exception("Failed to save Advanced Resolution Selector base preset")
        return _json_response(False, _t("base_quick_failed"), bases=all_base_presets())


def delete_custom_base_preset(base):
    base = _valid_base_resolution(base)
    if base is None or base in BUILTIN_BASE_PRESETS:
        return _json_response(False, _t("base_quick_delete_failed"), bases=all_base_presets())
    presets = [value for value in load_custom_base_presets() if value != base]
    try:
        save_custom_base_presets(presets)
        return _json_response(True, _t("base_quick_deleted").format(base=base), bases=all_base_presets())
    except Exception:
        logger.exception("Failed to delete Advanced Resolution Selector base preset")
        return _json_response(False, _t("base_quick_delete_failed"), bases=all_base_presets())


def _register_api(_demo, app):
    @app.post("/adv-ar-selector/api/base/add")
    async def adv_ar_selector_add_base(request: Request):
        try:
            payload = await request.json()
        except Exception:
            payload = {}
        return add_custom_base_preset(payload.get("base"))

    @app.post("/adv-ar-selector/api/base/delete")
    async def adv_ar_selector_delete_base(request: Request):
        try:
            payload = await request.json()
        except Exception:
            payload = {}
        return delete_custom_base_preset(payload.get("base"))


script_callbacks.on_app_started(_register_api)

def load_custom_presets():
    if os.path.exists(PRESETS_FILE):
        try:
            with open(PRESETS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_custom_presets(presets):
    with open(PRESETS_FILE, "w", encoding="utf-8") as f:
        json.dump(presets, f, indent=4)

def calculate_ratio(w, h):
    if not w or not h: return ""
    try:
        w, h = int(w), int(h)
        if w <= 0 or h <= 0: return ""
        d = math.gcd(w, h)
        return f"{w//d}:{h//d}"
    except Exception:
        return ""

def _base_quick_manager_html():
    invalid = _html_attr(_t("base_quick_invalid"))
    added = _html_attr(_t("base_quick_added"))
    failed = _html_attr(_t("base_quick_failed"))
    confirm = _html_attr(_t("base_quick_delete_confirm"))
    confirm_final = _html_attr(_t("base_quick_delete_confirm_final"))
    return f"""
<div class="adv-ar-base-manager"
     data-add-url="adv-ar-selector/api/base/add"
     data-delete-url="adv-ar-selector/api/base/delete"
     data-invalid-message="{invalid}"
     data-added-message="{added}"
     data-failed-message="{failed}"
     data-delete-confirm="{confirm}"
     data-delete-confirm-final="{confirm_final}">
    <div class="adv-ar-base-title">{_t("base_quick_title")}</div>
    <div class="adv-ar-base-hint">{_t("base_quick_hint")}</div>
    <div class="adv-ar-base-form">
        <input class="adv-ar-base-input" type="number" min="64" step="64" placeholder="{_html_attr(_t("base_quick_placeholder"))}">
        <button class="adv-ar-base-add" type="button">{_t("base_quick_add")}</button>
    </div>
    <div class="adv-ar-base-status" aria-live="polite"></div>
</div>
"""

class AdvancedResolutionScript(scripts.Script):
    def __init__(self):
        self.txt2img_w = None
        self.txt2img_h = None
        self.img2img_w = None
        self.img2img_h = None

    def title(self):
        return _t("title")

    def show(self, is_img2img):
        return scripts.AlwaysVisible

    def after_component(self, component, **kwargs):
        elem_id = kwargs.get("elem_id")
        
        # 捕获原生宽高组件，以便后续向它们发送数值
        if elem_id == "txt2img_width": self.txt2img_w = component
        if elem_id == "txt2img_height": self.txt2img_h = component
        if elem_id == "img2img_width": self.img2img_w = component
        if elem_id == "img2img_height": self.img2img_h = component

        # 注入点：cfg_scale (紧挨在种子设置上方)
        if elem_id in ["txt2img_cfg_scale", "img2img_cfg_scale"]:
            is_img2img = (elem_id == "img2img_cfg_scale")
            target_w = self.img2img_w if is_img2img else self.txt2img_w
            target_h = self.img2img_h if is_img2img else self.txt2img_h

            def create_buttons(data_dict):
                """辅助函数：遍历字典生成按钮并绑定点击事件"""
                for label, (w, h) in data_dict.items():
                    btn = gr.Button(value=label, size="sm")
                    btn.click(fn=lambda width=w, height=h: (width, height), inputs=[], outputs=[target_w, target_h])

            def create_resolution_tab(base, label, deletable=False):
                tab_label = f"{label} ×" if deletable else label
                with gr.Tab(tab_label):
                    data = build_resolution_set(base)
                    gr.HTML(f"<div class='ar-category-label'>🔲 {_t('square')}</div>")
                    with gr.Row(elem_classes="ar-button-row"):
                        create_buttons(data["square"])

                    gr.HTML(f"<div class='ar-category-label'>🖥️ {_t('landscape')}</div>")
                    with gr.Row(elem_classes="ar-button-row"):
                        create_buttons(data["landscape"])

                    gr.HTML(f"<div class='ar-category-label'>📱 {_t('portrait')}</div>")
                    with gr.Row(elem_classes="ar-button-row"):
                        create_buttons(data["portrait"])

            # 【核心修复】：增加外层 Wrapper 列，强制换行并铺满 100% 宽度
            with gr.Column(elem_classes="adv-res-wrapper"):
                with gr.Accordion("📐 " + _t("accordion"), open=False, elem_classes="adv-res-accordion"):
                    _intro_block()
                    with gr.Tabs():
                        create_resolution_tab(1024, _t("tab_1024"))
                        create_resolution_tab(1280, _t("tab_1280"))
                        create_resolution_tab(1536, _t("tab_1536"))
                        for custom_base in load_custom_base_presets():
                            create_resolution_tab(custom_base, f"{custom_base} {_t('tab_base_custom')}", deletable=True)

                        # --- 自定义选项卡 ---
                        with gr.Tab("🔧 " + _t("tab_custom")):
                            gr.HTML(_base_quick_manager_html())
                            with gr.Row():
                                custom_w = gr.Number(label=_t("custom_width"), value=1024, precision=0)
                                custom_h = gr.Number(label=_t("custom_height"), value=1024, precision=0)
                                calc_ratio = gr.Textbox(label=_t("auto_ratio"), value="1:1", interactive=False)
                            
                            with gr.Row():
                                save_name = gr.Textbox(label=_t("preset_name"), placeholder=_t("preset_name_placeholder"))
                                save_btn = gr.Button("💾 " + _t("save_preset"), variant="primary")
                            
                            with gr.Row():
                                initial_presets = load_custom_presets()
                                preset_choices = list(initial_presets.keys())
                                preset_dropdown = gr.Dropdown(
                                    label=_t("saved_presets"), 
                                    choices=preset_choices, 
                                    value=preset_choices[0] if preset_choices else None
                                )
                                apply_custom_btn = gr.Button("🚀 " + _t("apply_preset"))
                                del_custom_btn = gr.Button("🗑️ " + _t("delete_preset"))

            # --- 事件绑定区域 ---
            custom_w.change(fn=calculate_ratio, inputs=[custom_w, custom_h], outputs=[calc_ratio])
            custom_h.change(fn=calculate_ratio, inputs=[custom_w, custom_h], outputs=[calc_ratio])

            def save_preset_action(w, h, name):
                presets = load_custom_presets()
                w, h = int(w), int(h)
                ratio = calculate_ratio(w, h)
                preset_name = name.strip() if name.strip() else f"{ratio} ({w}x{h})"
                presets[preset_name] = [w, h]
                save_custom_presets(presets)
                return gr.update(choices=list(presets.keys()), value=preset_name)

            save_btn.click(fn=save_preset_action, inputs=[custom_w, custom_h, save_name], outputs=[preset_dropdown])

            def apply_preset_action(preset_name, cur_w, cur_h):
                presets = load_custom_presets()
                if preset_name in presets:
                    return presets[preset_name][0], presets[preset_name][1]
                return cur_w, cur_h

            apply_custom_btn.click(fn=apply_preset_action, inputs=[preset_dropdown, target_w, target_h], outputs=[target_w, target_h])

            def del_preset_action(preset_name):
                presets = load_custom_presets()
                if preset_name in presets:
                    del presets[preset_name]
                    save_custom_presets(presets)
                choices = list(presets.keys())
                new_val = choices[0] if choices else None
                return gr.update(choices=choices, value=new_val)

            del_custom_btn.click(fn=del_preset_action, inputs=[preset_dropdown], outputs=[preset_dropdown])
