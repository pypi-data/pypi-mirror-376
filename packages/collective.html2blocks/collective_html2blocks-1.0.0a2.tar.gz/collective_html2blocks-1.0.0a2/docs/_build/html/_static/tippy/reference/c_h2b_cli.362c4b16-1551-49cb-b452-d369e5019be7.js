selector_to_html = {"a[href=\"#collective.html2blocks.cli.main\"]": "<dt class=\"sig sig-object py\" id=\"collective.html2blocks.cli.main\">\n<span class=\"sig-prename descclassname\"><span class=\"pre\">collective.html2blocks.cli.</span></span><span class=\"sig-name descname\"><span class=\"pre\">main</span></span><span class=\"sig-paren\">(</span><em class=\"sig-param\"><span class=\"n\"><span class=\"pre\">ctx</span></span><span class=\"p\"><span class=\"pre\">:</span></span><span class=\"w\"> </span><span class=\"n\"><span class=\"pre\">Context</span></span></em><span class=\"sig-paren\">)</span><a class=\"reference internal\" href=\"../_modules/collective/html2blocks/cli.html#main\"><span class=\"viewcode-link\"><span class=\"pre\">[source]</span></span></a></dt><dd><p>Main CLI callback for <code class=\"docutils literal notranslate\"><span class=\"pre\">collective.html2blocks</span></code>.</p><p>This function is invoked when the CLI is run without a subcommand. It displays\na welcome message and help information for available commands.</p><p class=\"rubric\">Example</p></dd>", "a[href=\"#module-collective.html2blocks.cli\"]": "<h1 class=\"tippy-header\" style=\"margin-top: 0;\"><code class=\"docutils literal notranslate\"><span class=\"pre\">collective.html2blocks.cli</span></code><a class=\"headerlink\" href=\"#module-collective.html2blocks.cli\" title=\"Link to this heading\">#</a></h1><p>CLI entry point for <code class=\"docutils literal notranslate\"><span class=\"pre\">collective.html2blocks</span></code>.</p><p>This module provides the Typer-based command-line interface for converting HTML\ncontent to Volto blocks, inspecting conversion info, and running the API server.</p>", "a[href=\"#collective.html2blocks.cli.cli\"]": "<dt class=\"sig sig-object py\" id=\"collective.html2blocks.cli.cli\">\n<span class=\"sig-prename descclassname\"><span class=\"pre\">collective.html2blocks.cli.</span></span><span class=\"sig-name descname\"><span class=\"pre\">cli</span></span><span class=\"sig-paren\">(</span><span class=\"sig-paren\">)</span><a class=\"reference internal\" href=\"../_modules/collective/html2blocks/cli.html#cli\"><span class=\"viewcode-link\"><span class=\"pre\">[source]</span></span></a></dt><dd><p>Run the collective.html2blocks CLI application.</p><p>This function serves as the entry point for the CLI, invoking the Typer app.</p><p class=\"rubric\">Example</p></dd>"}
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
