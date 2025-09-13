selector_to_html = {"a[href=\"../glossary.html#term-setuptools\"]": "<dt id=\"term-setuptools\">setuptools</dt><dd><p><a class=\"reference external\" href=\"https://setuptools.pypa.io/\">setuptools</a> is a Python package development and distribution library. It is commonly used to build, package, and install Python projects, especially those using a <code class=\"docutils literal notranslate\"><span class=\"pre\">setup.py</span></code> file.</p></dd>", "a[href=\"../glossary.html#term-uv\"]": "<dt id=\"term-uv\">uv</dt><dd><p><a class=\"reference external\" href=\"https://github.com/astral-sh/uv\">uv</a> is a fast Python package manager and build tool that supports modern workflows, including dependency management via <code class=\"docutils literal notranslate\"><span class=\"pre\">pyproject.toml</span></code>.</p></dd>", "a[href=\"#reinstall-with-updated-dependencies\"]": "<h2 class=\"tippy-header\" style=\"margin-top: 0;\">Reinstall with updated dependencies<a class=\"headerlink\" href=\"#reinstall-with-updated-dependencies\" title=\"Link to this heading\">#</a></h2><p>After updating your dependency file, re-run your project's installation command (for example, <code class=\"docutils literal notranslate\"><span class=\"pre\">pip</span> <span class=\"pre\">install</span> <span class=\"pre\">-r</span> <span class=\"pre\">requirements.txt</span></code>, <code class=\"docutils literal notranslate\"><span class=\"pre\">uv</span> <span class=\"pre\">sync</span></code>, or your build tool's equivalent). The package will be installed and available for use in your environment.</p><p>Refer to the official <a class=\"reference external\" href=\"https://packaging.python.org/en/latest/specifications/dependency-specifiers/\">Dependency specifiers</a> documentation for details on specifying versions and advanced dependency options.</p>", "a[href=\"#installation\"]": "<h1 class=\"tippy-header\" style=\"margin-top: 0;\">Installation<a class=\"headerlink\" href=\"#installation\" title=\"Link to this heading\">#</a></h1><p>You can install <code class=\"docutils literal notranslate\"><span class=\"pre\">collective.html2blocks</span></code> in your project using several supported methods, depending on your project's setup and preferred workflow.</p>", "a[href=\"../glossary.html#term-PEP-621\"]": "<dt id=\"term-PEP-621\">PEP 621</dt><dd><p><a class=\"reference external\" href=\"https://peps.python.org/pep-0621/\">PEP 621</a> is a Python Enhancement Proposal that standardizes how project metadata is specified in <code class=\"docutils literal notranslate\"><span class=\"pre\">pyproject.toml</span></code> files for Python packages.</p></dd>"}
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
