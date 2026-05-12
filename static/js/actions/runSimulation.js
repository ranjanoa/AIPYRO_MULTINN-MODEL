import { MOCK_CONFIG } from "../inits/config.js";
export async function runSimulation() {
    const checked = Array.from(document.querySelectorAll('.sim-check:checked')).map(cb => cb.value);
    if (checked.length < 2) return alert("Select 2+ vars");
    const container = document.getElementById('plotly-container');
    try {
        const res = await fetch(`${MOCK_CONFIG.API_URL}/api/history/visualize`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                tags: checked,
                minutes: document.getElementById('sim-time-window').value,
                color_by: document.getElementById('sim-color-var').value
            })
        });
        const json = await res.json();

        // ---------- ADD GAP LOGIC HERE ----------
        const dims = json.data[0].dimensions;
        //  Step 1: Short label (2 words) + store full label
        dims.forEach(dim => {
            const fullLabel = dim.label || "";

            dim._fullLabel = fullLabel;

            const words = fullLabel.split(" ");
            dim.label = words.length > 3
                ? words.slice(0, 3).join(" ") + "..."
                : words.join(" ");
        });
        let pos = 0;
        let prevGroup = "";

        dims.forEach(dim => {

            let label = dim.label || "";
            let group = label.split(" ")[0];

            pos += 0.15;

            if (prevGroup && group !== prevGroup) {
                pos += 0.4;
            }
            dim.position = pos;
            prevGroup = group;
        });
        // ----------------------------------------
        const axisCount = json.data[0].dimensions.length;

        json.layout = json.layout || {};
        if (axisCount > 5) {
            json.layout.width = axisCount * 140;
        }

        // background colors
        json.layout.paper_bgcolor = "#2A3B40";
        json.layout.plot_bgcolor = "#2A3B40";
        json.layout.font = {
            color: "#F1F4F6"
        };

        json.layout.margin = {
            ...(json.layout.margin || {}),
            l: 100   // left margin
        };


        Plotly.newPlot('plotly-container', json.data, json.layout, { responsive: true });
            
        const tooltip = document.getElementById("axis-tooltip") || (() => {
            const t = document.createElement("div");
            t.id = "axis-tooltip";
            t.style.position = "absolute";
            t.style.display = "none";
            t.style.background = "#111";
            t.style.color = "#fff";
            t.style.padding = "1px 6px 3px 6px";
            t.style.borderRadius = "4px";
            t.style.fontSize = "12px";
            t.style.pointerEvents = "none";
            t.style.zIndex = "1000";
            t.style.maxWidth = "250px";
            t.style.wordWrap = "nowrap";
            document.body.appendChild(t);
            return t;
        })();

        const axisLabels = container.querySelectorAll(".axis-title");
        axisLabels.forEach((label, index) => {
            label.addEventListener("mouseenter", function () {
                // const fullText = label.getAttribute("data-unformatted") || label.textContent;
                const fullText = dims[index]?._fullLabel || label.textContent;
                tooltip.innerHTML = fullText;
                tooltip.style.display = "block";
                const rect = label.getBoundingClientRect();

                const tooltipWidth = tooltip.offsetWidth || 150;
                const tooltipHeight = tooltip.offsetHeight || 40;
                const pageWidth = window.innerWidth;
                let left = rect.left + rect.width / 2 - tooltipWidth / 2;
                let top = rect.top - tooltipHeight - 8;
                 if (left + tooltipWidth > pageWidth) {
                    left = pageWidth - tooltipWidth - 10;
                }

                if (left < 0) {
                    left = 10;
                }

                // if no space above → show below
                if (top < 0) {
                    top = rect.bottom + 8;
                }

                tooltip.style.left = left + "px";
                tooltip.style.top = top + "px";
            });

            label.addEventListener("mouseleave", function () {
                tooltip.style.display = "none";
            });

        });
    } catch (e) {
        alert("Sim Error");
    }
}
