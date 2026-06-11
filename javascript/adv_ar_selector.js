(function () {
    const STEP = 64;

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

    function reloadUi() {
        window.setTimeout(function () {
            window.location.reload();
        }, 250);
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
                if (result.ok) reloadUi();
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

    function tabText(tab) {
        return (tab.textContent || "").replace(/\s+/g, " ").trim();
    }

    function extractCustomBase(tab) {
        const match = tabText(tab).match(/^(\d+)\s+(?:基准|Base)\s*[x×]$/i);
        return match ? Number.parseInt(match[1], 10) : null;
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
                if (result.ok) reloadUi();
            } catch (error) {
                status(manager, manager.dataset.failedMessage || error.message, true);
            }
        };
    }

    function setupDeletableTabs() {
        const manager = document.querySelector(".adv-ar-base-manager");
        if (!manager) return;

        document.querySelectorAll("button, [role='tab']").forEach(function (tab) {
            const base = extractCustomBase(tab);
            if (!base || tab.dataset.advArDeleteReady === "1") return;

            tab.dataset.advArDeleteReady = "1";
            tab.classList.add("adv-ar-base-tab-delete");
            tab.title = template(manager.dataset.deleteConfirm, base);

            const label = tabText(tab).replace(/\s*[x×]\s*$/i, "");
            tab.textContent = "";
            const labelNode = document.createElement("span");
            labelNode.textContent = label;
            const deleteNode = document.createElement("span");
            deleteNode.className = "adv-ar-base-delete-x";
            deleteNode.setAttribute("aria-label", template(manager.dataset.deleteConfirm, base));
            deleteNode.textContent = "×";
            deleteNode.addEventListener("click", makeDeleteHandler(manager, base), true);
            tab.append(labelNode, deleteNode);
        });
    }

    function scan() {
        document.querySelectorAll(".adv-ar-base-manager").forEach(setupBaseManager);
        setupDeletableTabs();
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
