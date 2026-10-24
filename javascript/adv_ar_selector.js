(function () {
    const STEP = 64;
    const LOCALE = {
        zh: {
            accordion: "📐 预设分辨率与自定义比例",
            introLanguage: "界面语言",
            tab1024: "1024 基准 (标准)",
            tab1280: "1280 基准 (高清)",
            tab1536: "1536 基准 (超高分)",
            tabBaseCustom: "基准",
            tabCustom: "🔧 自定义 & 保存",
            square: "🔲 方形 (Square)",
            landscape: "🖥️ 横向 (Landscape)",
            portrait: "📱 竖向 (Portrait)",
            baseQuickTitle: "基础分辨率快速设置",
            baseQuickHint: "输入 64 的倍数，自动计算桶分辨率并添加到快速设置栏。",
            baseQuickPlaceholder: "例如: 1600",
            baseQuickAdd: "添加到快速设置栏",
            baseQuickInvalid: "请输入一个大于 0 且为 64 倍数的整数。",
            baseQuickAdded: "已添加 {base} 基准快速设置，正在刷新插件面板。",
            baseQuickFailed: "保存基础分辨率失败，请检查控制台日志。",
            baseQuickDeleteConfirm: "删除 {base} 基准快速设置？",
            baseQuickDeleteConfirmFinal: "再次确认删除 {base} 基准预设？此操作会刷新插件面板。",
            customWidth: "自定义宽度",
            customHeight: "自定义高度",
            autoRatio: "自动计算比例",
            presetName: "预设名称 (留空则自动生成)",
            presetPlaceholder: "例如: 宽屏电影 16:9",
            savePreset: "💾 计算并保存为预设",
            savedPresets: "已保存的自定义预设",
            applyPreset: "🚀 应用选中预设",
            deletePreset: "🗑️ 删除选中预设",
            noteWidescreen: "宽银幕",
            noteCinematic: "电影",
            noteUltrawide: "超宽",
            notePanorama: "全景",
            noteVerticalWidescreen: "竖银幕",
            noteVertical: "竖向",
            noteNarrow: "极窄",
            noteStrip: "竖条",
        },
        en: {
            accordion: "📐 Preset Resolutions and Custom Ratios",
            introLanguage: "UI language",
            tab1024: "1024 Base (Standard)",
            tab1280: "1280 Base (HD)",
            tab1536: "1536 Base (Ultra High)",
            tabBaseCustom: "Base",
            tabCustom: "🔧 Custom & Save",
            square: "🔲 Square",
            landscape: "🖥️ Landscape",
            portrait: "📱 Portrait",
            baseQuickTitle: "Base resolution quick preset",
            baseQuickHint: "Enter a multiple of 64 to calculate bucket resolutions and add them to the quick preset bar.",
            baseQuickPlaceholder: "Example: 1600",
            baseQuickAdd: "Add to quick presets",
            baseQuickInvalid: "Enter a positive integer that is divisible by 64.",
            baseQuickAdded: "Added the {base} base quick preset. Refreshing the plugin panel.",
            baseQuickFailed: "Failed to save the base resolution. Check the console log.",
            baseQuickDeleteConfirm: "Delete the {base} base quick preset?",
            baseQuickDeleteConfirmFinal: "Confirm deletion of the {base} base preset? The plugin panel will refresh.",
            customWidth: "Custom width",
            customHeight: "Custom height",
            autoRatio: "Calculated ratio",
            presetName: "Preset name (auto-generated when empty)",
            presetPlaceholder: "Example: Cinematic 16:9",
            savePreset: "💾 Calculate and save preset",
            savedPresets: "Saved custom presets",
            applyPreset: "🚀 Apply selected preset",
            deletePreset: "🗑️ Delete selected preset",
            noteWidescreen: "Widescreen",
            noteCinematic: "Cinema",
            noteUltrawide: "Ultrawide",
            notePanorama: "Panorama",
            noteVerticalWidescreen: "Vertical widescreen",
            noteVertical: "Vertical",
            noteNarrow: "Narrow",
            noteStrip: "Strip",
        },
    };
    const BUILTIN_BASES = [1024, 1280, 1536];
    const BUCKETS_1024 = {
        square: [["1:1", "", [1024, 1024]]],
        landscape: [
            ["5:4", "", [1152, 896]],
            ["4:3", "", [1152, 832]],
            ["3:2", "", [1216, 832]],
            ["16:9", "", [1344, 768]],
            ["1.85:1", "noteWidescreen", [1408, 768]],
            ["2:1", "noteCinematic", [1472, 704]],
            ["21:9", "noteUltrawide", [1536, 640]],
            ["3:1", "notePanorama", [1728, 576]],
        ],
        portrait: [
            ["4:5", "", [896, 1152]],
            ["3:4", "", [832, 1152]],
            ["2:3", "", [832, 1216]],
            ["9:16", "", [768, 1344]],
            ["1:1.85", "noteVerticalWidescreen", [768, 1408]],
            ["1:2", "noteVertical", [704, 1472]],
            ["9:21", "noteNarrow", [640, 1536]],
            ["1:3", "noteStrip", [576, 1728]],
        ],
    };
    const STATIC_SIZES = {
        1024: {
            square: [[1024, 1024]],
            landscape: [[1152, 896], [1152, 832], [1216, 832], [1344, 768], [1408, 768], [1472, 704], [1536, 640], [1728, 576]],
            portrait: [[896, 1152], [832, 1152], [832, 1216], [768, 1344], [768, 1408], [704, 1472], [640, 1536], [576, 1728]],
        },
        1536: {
            square: [[1536, 1536]],
            landscape: [[1728, 1344], [1728, 1280], [1856, 1216], [2048, 1152], [2112, 1152], [2240, 1088], [2304, 960], [2560, 832]],
            portrait: [[1344, 1728], [1280, 1728], [1216, 1856], [1152, 2048], [1152, 2112], [1088, 2240], [960, 2304], [832, 2560]],
        },
    };

    function apiUrl(path) {
        return new URL(path, window.location.href).toString();
    }

    function status(manager, message, isError) {
        const node = manager.querySelector(".adv-ar-base-status");
        if (!node) return;
        node.textContent = message || "";
        node.classList.toggle("adv-ar-base-status-error", Boolean(isError));
    }

    function template(text, base) {
        return String(text || "").replace(/\{base\}/g, base);
    }

    function roundBucket(value) {
        return Math.max(STEP, Math.round(Number(value) / STEP) * STEP);
    }

    function bucketEntries(base, category) {
        const canonical = BUCKETS_1024[category];
        if (STATIC_SIZES[base]) {
            return canonical.map(function (entry, index) {
                return [entry[0], entry[1], STATIC_SIZES[base][category][index]];
            });
        }
        const scale = base / 1024;
        return canonical.map(function (entry) {
            const size = category === "square" ? [base, base] : [roundBucket(entry[2][0] * scale), roundBucket(entry[2][1] * scale)];
            return [entry[0], entry[1], size];
        });
    }

    function labelForBucket(entry, t) {
        const note = entry[1] ? " " + t[entry[1]] : "";
        return entry[0] + note + " (" + entry[2][0] + "x" + entry[2][1] + ")";
    }

    function setGradioNumber(elemId, value) {
        const app = window.gradioApp ? window.gradioApp() : document;
        const root = app.getElementById(elemId) || document.getElementById(elemId);
        const input = root && root.querySelector("input");
        if (!input) return;
        const nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
        nativeSetter.call(input, String(value));
        input.dispatchEvent(new Event("input", { bubbles: true }));
        input.dispatchEvent(new Event("change", { bubbles: true }));
    }

    function applySize(manager, width, height) {
        setGradioNumber(manager.dataset.widthId, width);
        setGradioNumber(manager.dataset.heightId, height);
    }

    function textIs(node, values) {
        const text = (node.textContent || "").replace(/\s+/g, " ").trim();
        return values.some(function (value) {
            return text === value;
        });
    }

    function setLabelByKnownText(root, zhText, enText, targetText) {
        root.querySelectorAll("span, button, [role='tab'], label").forEach(function (node) {
            // 仅替换无子元素的纯文本叶子节点，防止误删 <label> 内部的 <input> 组件
            if (node.children.length === 0 && textIs(node, [zhText, enText])) {
                node.textContent = targetText;
            }
        });
    }

    function setInputLabel(input, zhText, enText, targetText, placeholder) {
        const wrap = input && input.closest(".form, .block, .gradio-container, div");
        const root = (wrap && wrap.parentElement) || document;
        setLabelByKnownText(root, zhText, enText, targetText);
        if (placeholder && input) input.setAttribute("placeholder", placeholder);
    }

    function syncAllManagersBases(bases, locale) {
        const serialized = JSON.stringify(bases || []);
        const app = window.gradioApp ? window.gradioApp() : document;
        app.querySelectorAll(".adv-ar-base-manager").forEach(function (m) {
            m.dataset.bases = serialized;
            renderDynamicBaseTabs(m, bases || []);
        });
        refreshPluginLanguage(locale || "zh");
    }

    function refreshPluginLanguage(language) {
        const lang = LOCALE[language] ? language : "zh";
        const t = LOCALE[lang];
        const app = window.gradioApp ? window.gradioApp() : document;
        const managers = app.querySelectorAll(".adv-ar-base-manager");
        const noteKeys = [
            "noteWidescreen", "noteCinematic", "noteUltrawide", "notePanorama",
            "noteVerticalWidescreen", "noteVertical", "noteNarrow", "noteStrip",
        ];

        managers.forEach(function (manager) {
            const wrapper = manager.closest(".adv-res-wrapper") || app;
            manager.dataset.advArLocale = lang;
            manager.dataset.invalidMessage = t.baseQuickInvalid;
            manager.dataset.addedMessage = t.baseQuickAdded;
            manager.dataset.failedMessage = t.baseQuickFailed;
            manager.dataset.deleteConfirm = t.baseQuickDeleteConfirm;
            manager.dataset.deleteConfirmFinal = t.baseQuickDeleteConfirmFinal;
            renderDynamicBaseTabs(manager, parseBases(manager.dataset.bases));

            const title = manager.querySelector(".adv-ar-base-title");
            const hint = manager.querySelector(".adv-ar-base-hint");
            const input = manager.querySelector(".adv-ar-base-input");
            const add = manager.querySelector(".adv-ar-base-add");
            if (title) title.textContent = t.baseQuickTitle;
            if (hint) hint.textContent = t.baseQuickHint;
            if (input) input.setAttribute("placeholder", t.baseQuickPlaceholder);
            if (add) add.textContent = t.baseQuickAdd;

            // 精准选中标题文字 span，避免覆盖右侧折叠箭头图标
            const accordionLabel = wrapper.querySelector(".label-wrap > span:first-child") || wrapper.querySelector(".label-wrap span");
            if (accordionLabel && /Preset Resolutions|预设分辨率/.test(accordionLabel.textContent || "")) {
                accordionLabel.textContent = t.accordion;
            }

            wrapper.querySelectorAll(".ar-category-label").forEach(function (node) {
                const text = node.textContent || "";
                if (/Square|方形/.test(text)) node.textContent = t.square;
                if (/Landscape|横向/.test(text)) node.textContent = t.landscape;
                if (/Portrait|竖向/.test(text)) node.textContent = t.portrait;
            });

            // 翻译内置 1024/1280/1536 标签页内的按钮后缀注释
            wrapper.querySelectorAll(".ar-button-row button").forEach(function (btn) {
                let label = btn.textContent || "";
                noteKeys.forEach(function (key) {
                    const zhNote = " " + LOCALE.zh[key] + " (";
                    const enNote = " " + LOCALE.en[key] + " (";
                    const targetNote = " " + t[key] + " (";
                    if (label.includes(zhNote)) label = label.replace(zhNote, targetNote);
                    else if (label.includes(enNote)) label = label.replace(enNote, targetNote);
                });
                if (btn.textContent !== label) btn.textContent = label;
            });

            wrapper.querySelectorAll("button, [role='tab']").forEach(function (tab) {
                if (tab.children.length > 0) return;
                if (textIs(tab, [LOCALE.zh.tab1024, LOCALE.en.tab1024])) tab.textContent = t.tab1024;
                if (textIs(tab, [LOCALE.zh.tab1280, LOCALE.en.tab1280])) tab.textContent = t.tab1280;
                if (textIs(tab, [LOCALE.zh.tab1536, LOCALE.en.tab1536])) tab.textContent = t.tab1536;
                if (textIs(tab, [LOCALE.zh.tabCustom, LOCALE.en.tabCustom])) tab.textContent = t.tabCustom;
                if (textIs(tab, [LOCALE.zh.savePreset, LOCALE.en.savePreset])) tab.textContent = t.savePreset;
                if (textIs(tab, [LOCALE.zh.applyPreset, LOCALE.en.applyPreset])) tab.textContent = t.applyPreset;
                if (textIs(tab, [LOCALE.zh.deletePreset, LOCALE.en.deletePreset])) tab.textContent = t.deletePreset;
            });

            setLabelByKnownText(wrapper, LOCALE.zh.introLanguage, LOCALE.en.introLanguage, t.introLanguage);

            const inputs = wrapper.querySelectorAll("input, textarea");
            inputs.forEach(function (inp) {
                const placeholder = inp.getAttribute("placeholder") || "";
                if (placeholder === LOCALE.zh.presetPlaceholder || placeholder === LOCALE.en.presetPlaceholder) {
                    setInputLabel(inp, LOCALE.zh.presetName, LOCALE.en.presetName, t.presetName, t.presetPlaceholder);
                }
            });

            setLabelByKnownText(wrapper, LOCALE.zh.customWidth, LOCALE.en.customWidth, t.customWidth);
            setLabelByKnownText(wrapper, LOCALE.zh.customHeight, LOCALE.en.customHeight, t.customHeight);
            setLabelByKnownText(wrapper, LOCALE.zh.autoRatio, LOCALE.en.autoRatio, t.autoRatio);
            setLabelByKnownText(wrapper, LOCALE.zh.savedPresets, LOCALE.en.savedPresets, t.savedPresets);
        });
    }

    function parseBases(value) {
        try {
            const parsed = JSON.parse(value || "[]");
            return Array.isArray(parsed) ? parsed.map(Number).filter(Number.isFinite) : [];
        } catch (error) {
            return [];
        }
    }

    function categoryBlock(manager, base, key, title, t) {
        const block = document.createElement("div");
        const heading = document.createElement("div");
        heading.className = "ar-category-label";
        heading.textContent = title;
        const row = document.createElement("div");
        row.className = "ar-button-row";
        bucketEntries(base, key).forEach(function (entry) {
            const button = document.createElement("button");
            button.type = "button";
            button.textContent = labelForBucket(entry, t);
            button.addEventListener("click", function () {
                applySize(manager, entry[2][0], entry[2][1]);
            });
            row.appendChild(button);
        });
        block.append(heading, row);
        return block;
    }

    function renderDynamicBaseTabs(manager, bases) {
        const wrapper = manager.closest(".adv-res-wrapper") || document;
        const container = wrapper.querySelector(".adv-ar-dynamic-base-tabs");
        if (!container) return;
        const lang = LOCALE[manager.dataset.advArLocale] ? manager.dataset.advArLocale : "zh";
        const t = LOCALE[lang];
        const visibleBases = bases.filter(function (base) {
            return !BUILTIN_BASES.includes(base);
        });
        const renderKey = lang + ":" + visibleBases.join(",");
        if (container.dataset.advArRenderKey === renderKey) return;
        container.dataset.advArRenderKey = renderKey;
        container.textContent = "";
        visibleBases.forEach(function (base, index) {
            const panel = document.createElement("section");
            panel.className = "adv-ar-dynamic-base-panel";
            if (index === 0) panel.classList.add("open");
            const header = document.createElement("button");
            header.type = "button";
            header.className = "adv-ar-dynamic-base-header";
            const headerLabel = document.createElement("span");
            headerLabel.textContent = base + " " + t.tabBaseCustom;
            const remove = document.createElement("span");
            remove.className = "adv-ar-base-delete-x";
            remove.textContent = "×";
            remove.title = template(t.baseQuickDeleteConfirm, base);
            remove.addEventListener("click", makeDeleteHandler(manager, base), true);
            header.append(headerLabel, remove);
            const body = document.createElement("div");
            body.className = "adv-ar-dynamic-base-body";
            body.append(
                categoryBlock(manager, base, "square", t.square, t),
                categoryBlock(manager, base, "landscape", t.landscape, t),
                categoryBlock(manager, base, "portrait", t.portrait, t),
            );
            header.addEventListener("click", function () {
                panel.classList.toggle("open");
            });
            panel.append(header, body);
            container.appendChild(panel);
        });
    }

    async function postJson(url, data) {
        const response = await fetch(apiUrl(url), {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data),
        });
        if (!response.ok) {
            throw new Error(response.statusText || "Request failed");
        }
        return response.json();
    }

    function setupBaseManager(manager) {
        if (manager.dataset.advArReady === "1") return;
        manager.dataset.advArReady = "1";

        const input = manager.querySelector(".adv-ar-base-input");
        const addButton = manager.querySelector(".adv-ar-base-add");
        if (!input || !addButton) return;

        async function addBasePreset() {
            const base = Number.parseInt(input.value, 10);
            if (!Number.isFinite(base) || base <= 0 || base % STEP !== 0) {
                status(manager, manager.dataset.invalidMessage, true);
                return;
            }

            addButton.disabled = true;
            try {
                const result = await postJson(manager.dataset.addUrl, { base });
                status(manager, result.message || template(manager.dataset.addedMessage, base), !result.ok);
                if (result.ok) {
                    input.value = "";
                    syncAllManagersBases(result.bases || [], manager.dataset.advArLocale);
                }
            } catch (error) {
                status(manager, manager.dataset.failedMessage || error.message, true);
            } finally {
                addButton.disabled = false;
            }
        }

        addButton.addEventListener("click", addBasePreset);
        input.addEventListener("keydown", function (event) {
            if (event.key === "Enter") {
                event.preventDefault();
                addBasePreset();
            }
        });
    }

    function makeDeleteHandler(manager, base) {
        return async function (event) {
            event.preventDefault();
            event.stopPropagation();

            if (!window.confirm(template(manager.dataset.deleteConfirm, base))) return;
            if (!window.confirm(template(manager.dataset.deleteConfirmFinal, base))) return;

            try {
                const result = await postJson(manager.dataset.deleteUrl, { base });
                status(manager, result.message, !result.ok);
                if (result.ok) {
                    syncAllManagersBases(result.bases || [], manager.dataset.advArLocale);
                }
            } catch (error) {
                status(manager, manager.dataset.failedMessage || error.message, true);
            }
        };
    }

    function setupLanguageRefresh() {
        document.querySelectorAll("[data-adv-ar-language-refresh]").forEach(function (marker) {
            if (marker.dataset.advArReloadReady === "1") return;
            marker.dataset.advArReloadReady = "1";
            refreshPluginLanguage(marker.dataset.advArLanguageRefresh);
        });
    }

    function scan() {
        document.querySelectorAll(".adv-ar-base-manager").forEach(function (manager) {
            setupBaseManager(manager);
            renderDynamicBaseTabs(manager, parseBases(manager.dataset.bases));
        });
        setupLanguageRefresh();
    }

    function start() {
        scan();
        const observer = new MutationObserver(scan);
        observer.observe(document.body, { childList: true, subtree: true });
    }

    if (window.onUiLoaded) {
        window.onUiLoaded(start);
    } else if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", start);
    } else {
        start();
    }
})();
