selector_to_html = {"a[href=\"#collective-html2blocks\"]": "<h1 class=\"tippy-header\" style=\"margin-top: 0;\"><code class=\"docutils literal notranslate\"><span class=\"pre\">collective.html2blocks</span></code><a class=\"headerlink\" href=\"#collective-html2blocks\" title=\"Link to this heading\">#</a></h1><p><strong>collective.html2blocks</strong> is an open-source Python package designed to facilitate the migration of content from legacy <a class=\"reference internal\" href=\"glossary.html#term-Plone\"><span class=\"xref std std-term\">Plone</span></a> sites and other <a class=\"reference internal\" href=\"glossary.html#term-CMS\"><span class=\"xref std std-term\">CMS</span></a>s to <a class=\"reference internal\" href=\"glossary.html#term-Volto\"><span class=\"xref std std-term\">Volto</span></a>. It provides robust tools for converting HTML content into Volto blocks, making it easier to modernize and restructure existing websites without manual reformatting.</p><p>The package offers a flexible registry and converter system for parsing HTML, handling complex content structures, and generating Volto-compatible JSON. It supports CLI and REST API, enabling batch processing, automation, and integration into existing migration workflows. With <code class=\"docutils literal notranslate\"><span class=\"pre\">collective.html2blocks</span></code>, developers can streamline migrations, preserve rich content, and take advantage of Volto's block-based editing experience.</p>"}
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
