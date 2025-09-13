selector_to_html = {"a[href=\"#register-a-new-converter\"]": "<h1 class=\"tippy-header\" style=\"margin-top: 0;\">Register a new converter<a class=\"headerlink\" href=\"#register-a-new-converter\" title=\"Link to this heading\">#</a></h1><p>To implement a new block converter in <code class=\"docutils literal notranslate\"><span class=\"pre\">collective.html2blocks</span></code>, you typically register a function using the <code class=\"docutils literal notranslate\"><span class=\"pre\">@registry.block_converter</span></code> or <code class=\"docutils literal notranslate\"><span class=\"pre\">@registry.element_converter</span></code> decorator.</p><p>The <code class=\"docutils literal notranslate\"><span class=\"pre\">@registry.block_converter</span></code> decorator is used for functions that return a Volto block\u2014an object with an <code class=\"docutils literal notranslate\"><span class=\"pre\">@type</span></code> key and other properties expected by Volto editors. These blocks are inserted directly into the output and can represent custom or third-party block types.</p>", "a[href=\"#a-new-block-converter-for-the-code-element\"]": "<h2 class=\"tippy-header\" style=\"margin-top: 0;\">A new block converter for the <code class=\"docutils literal notranslate\"><span class=\"pre\">&lt;code&gt;</span></code> element<a class=\"headerlink\" href=\"#a-new-block-converter-for-the-code-element\" title=\"Link to this heading\">#</a></h2><p>This function receives a BeautifulSoup element and returns a dictionary in the Volto block format. For example, to handle the <code class=\"docutils literal notranslate\"><span class=\"pre\">&lt;code&gt;</span></code> element and produce a code block compatible with <code class=\"docutils literal notranslate\"><span class=\"pre\">@plonegovbr/volto-code-block</span></code>, you would define a converter that extracts the code content and returns the required JSON structure.</p><p>Here is a sample implementation for a <code class=\"docutils literal notranslate\"><span class=\"pre\">&lt;code&gt;</span></code> block converter:</p>"}
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
