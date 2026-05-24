import modules.scripts as scripts
import gradio as gr
import platform
import ctypes
import os
import json
import math

from modules import script_callbacks, shared

LANGUAGE_OPTION = "adv_ar_selector_language"
LANGUAGE_CHOICES = ("zh", "en")
LANG = {
    "zh": {
        "title": "高级分辨率与自定义桶",
        "accordion": "预设分辨率与自定义比例",
        "tab_1024": "1024 基准 (标准)",
        "tab_1536": "1536 基准 (超高分)",
        "tab_custom": "自定义 & 保存",
        "square": "方形 (Square)",
        "landscape": "横向 (Landscape)",
        "portrait": "竖向 (Portrait)",
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
        "title": "Advanced Resolution and Custom Buckets",
        "accordion": "Preset Resolutions and Custom Ratios",
        "tab_1024": "1024 Base (Standard)",
        "tab_1536": "1536 Base (Ultra High)",
        "tab_custom": "Custom & Save",
        "square": "Square",
        "landscape": "Landscape",
        "portrait": "Portrait",
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
INTRO_EN = "Quickly set common 1024/1536-base resolutions, calculate custom aspect ratios, and save reusable width/height presets."
INTRO_ZH = "快速设置常用 1024/1536 基准分辨率，计算自定义比例，并保存可复用的宽高预设。"


def _language():
    value = getattr(shared.opts, LANGUAGE_OPTION, "zh")
    return value if value in LANGUAGE_CHOICES else "zh"


def _t(key):
    return LANG.get(_language(), LANG["zh"]).get(key, key)


def _intro_text(language):
    return INTRO_ZH if language == "中文" else INTRO_EN


def _intro_block():
    with gr.Row():
        intro_language = gr.Radio(
            choices=["English", "中文"],
            value="English",
            label="Description language / 说明语言",
        )
    intro = gr.Markdown(value=INTRO_EN)
    intro_language.change(fn=_intro_text, inputs=[intro_language], outputs=[intro], queue=False, show_progress=False)


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

            # --- 1024 基准比例字典库 ---
            res_1024 = {
                "square": {"1:1 (1024x1024)": (1024, 1024)},
                "landscape": {
                    "5:4 (1152x896)": (1152, 896),
                    "4:3 (1152x832)": (1152, 832),
                    "3:2 (1216x832)": (1216, 832),
                    "16:9 (1344x768)": (1344, 768),
                    "1.85:1 宽银幕 (1408x768)": (1408, 768),
                    "2:1 电影 (1472x704)": (1472, 704),
                    "21:9 超宽 (1536x640)": (1536, 640),
                    "3:1 全景 (1728x576)": (1728, 576)
                },
                "portrait": {
                    "4:5 (896x1152)": (896, 1152),
                    "3:4 (832x1152)": (832, 1152),
                    "2:3 (832x1216)": (832, 1216),
                    "9:16 (768x1344)": (768, 1344),
                    "1:1.85 竖银幕 (768x1408)": (768, 1408),
                    "1:2 竖向 (704x1472)": (704, 1472),
                    "9:21 极窄 (640x1536)": (640, 1536),
                    "1:3 竖条 (576x1728)": (576, 1728)
                }
            }

            # --- 1536 基准比例字典库 (适配24G显存) ---
            res_1536 = {
                "square": {"1:1 (1536x1536)": (1536, 1536)},
                "landscape": {
                    "5:4 (1728x1344)": (1728, 1344),
                    "4:3 (1728x1280)": (1728, 1280),
                    "3:2 (1856x1216)": (1856, 1216),
                    "16:9 (2048x1152)": (2048, 1152),
                    "1.85:1 宽银幕 (2112x1152)": (2112, 1152),
                    "2:1 电影 (2240x1088)": (2240, 1088),
                    "21:9 超宽 (2304x960)": (2304, 960),
                    "3:1 全景 (2560x832)": (2560, 832)
                },
                "portrait": {
                    "4:5 (1344x1728)": (1344, 1728),
                    "3:4 (1280x1728)": (1280, 1728),
                    "2:3 (1216x1856)": (1216, 1856),
                    "9:16 (1152x2048)": (1152, 2048),
                    "1:1.85 竖银幕 (1152x2112)": (1152, 2112),
                    "1:2 竖向 (1088x2240)": (1088, 2240),
                    "9:21 极窄 (960x2304)": (960, 2304),
                    "1:3 竖条 (832x2560)": (832, 2560)
                }
            }

            def create_buttons(data_dict):
                """辅助函数：遍历字典生成按钮并绑定点击事件"""
                for label, (w, h) in data_dict.items():
                    btn = gr.Button(value=label, size="sm")
                    btn.click(fn=lambda width=w, height=h: (width, height), inputs=[], outputs=[target_w, target_h])

            # 【核心修复】：增加外层 Wrapper 列，强制换行并铺满 100% 宽度
            with gr.Column(elem_classes="adv-res-wrapper"):
                with gr.Accordion("📐 " + _t("accordion"), open=False, elem_classes="adv-res-accordion"):
                    _intro_block()
                    with gr.Tabs():
                        # --- 1024 选项卡 ---
                        with gr.Tab(_t("tab_1024")):
                            gr.HTML(f"<div class='ar-category-label'>🔲 {_t('square')}</div>")
                            with gr.Row(elem_classes="ar-button-row"):
                                create_buttons(res_1024["square"])
                                
                            gr.HTML(f"<div class='ar-category-label'>🖥️ {_t('landscape')}</div>")
                            with gr.Row(elem_classes="ar-button-row"):
                                create_buttons(res_1024["landscape"])
                                
                            gr.HTML(f"<div class='ar-category-label'>📱 {_t('portrait')}</div>")
                            with gr.Row(elem_classes="ar-button-row"):
                                create_buttons(res_1024["portrait"])

                        # --- 1536 选项卡 ---
                        with gr.Tab(_t("tab_1536")):
                            gr.HTML(f"<div class='ar-category-label'>🔲 {_t('square')}</div>")
                            with gr.Row(elem_classes="ar-button-row"):
                                create_buttons(res_1536["square"])
                                
                            gr.HTML(f"<div class='ar-category-label'>🖥️ {_t('landscape')}</div>")
                            with gr.Row(elem_classes="ar-button-row"):
                                create_buttons(res_1536["landscape"])
                                
                            gr.HTML(f"<div class='ar-category-label'>📱 {_t('portrait')}</div>")
                            with gr.Row(elem_classes="ar-button-row"):
                                create_buttons(res_1536["portrait"])

                        # --- 自定义选项卡 ---
                        with gr.Tab("🔧 " + _t("tab_custom")):
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
