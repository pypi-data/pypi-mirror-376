selector_to_html = {"a[href=\"#documentation\"]": "<h3 class=\"tippy-header\" style=\"margin-top: 0;\">Documentation<a class=\"headerlink\" href=\"#documentation\" title=\"Link to this heading\">#</a></h3>", "a[href=\"#changelog\"]": "<h1 class=\"tippy-header\" style=\"margin-top: 0;\">Changelog<a class=\"headerlink\" href=\"#changelog\" title=\"Link to this heading\">#</a></h1><h2>1.0.0a1 (2025-09-11)<a class=\"headerlink\" href=\"#a1-2025-09-11\" title=\"Link to this heading\">#</a></h2><h3>Feature<a class=\"headerlink\" href=\"#feature\" title=\"Link to this heading\">#</a></h3>", "a[href=\"#feature\"]": "<h3 class=\"tippy-header\" style=\"margin-top: 0;\">Feature<a class=\"headerlink\" href=\"#feature\" title=\"Link to this heading\">#</a></h3>", "a[href=\"#internal\"]": "<h3 class=\"tippy-header\" style=\"margin-top: 0;\">Internal<a class=\"headerlink\" href=\"#internal\" title=\"Link to this heading\">#</a></h3>", "a[href=\"#bugfix\"]": "<h3 class=\"tippy-header\" style=\"margin-top: 0;\">Bugfix<a class=\"headerlink\" href=\"#bugfix\" title=\"Link to this heading\">#</a></h3>", "a[href=\"#a1-2025-09-11\"]": "<h2 class=\"tippy-header\" style=\"margin-top: 0;\">1.0.0a1 (2025-09-11)<a class=\"headerlink\" href=\"#a1-2025-09-11\" title=\"Link to this heading\">#</a></h2><h3>Feature<a class=\"headerlink\" href=\"#feature\" title=\"Link to this heading\">#</a></h3>"}
skip_classes = ["headerlink", "sd-stretched-link"]

window.onload = function () {
    for (const [select, tip_html] of Object.entries(selector_to_html)) {
        const links = document.querySelectorAll(`article.bd-article ${select}`);
        for (const link of links) {
            if (skip_classes.some(c => link.classList.contains(c))) {
                continue;
            }

            tippy(link, {
                content: tip_html,
                allowHTML: true,
                arrow: true,
                placement: 'auto-end', maxWidth: 500, interactive: true,

            });
        };
    };
    console.log("tippy tips loaded!");
};
