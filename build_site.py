# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "markdown",
# ]
# ///
import re
import os
import markdown
from markdown.extensions.toc import TocExtension

def slugify(value, separator):
    value = re.sub(r'[^\w\s-]', '', value.lower().strip())
    return re.sub(r'[-\s]+', separator, value).strip(separator)

class Page:
    def __init__(self, title, slug, filename, level):
        self.title = title
        self.slug = slug
        self.filename = filename
        self.level = level
        self.lines = []

def main():
    with open("README.md", "r", encoding="utf-8") as f:
        lines = f.readlines()

    seen_slugs = {}
    def get_slug(text):
        base_slug = slugify(text, '-')
        if base_slug in seen_slugs:
            seen_slugs[base_slug] += 1
            return f"{base_slug}-{seen_slugs[base_slug]}"
        else:
            seen_slugs[base_slug] = 0
            return base_slug

    pages = []
    current_page = None
    in_code_block = False
    slug_mapping = {}

    for line in lines:
        if line.startswith('```'):
            in_code_block = not in_code_block
        
        if not in_code_block:
            m = re.match(r'^(#{1,6})\s+(.*)', line)
            if m:
                level = len(m.group(1))
                title = m.group(2).strip()
                clean_title = re.sub(r'<!--.*?-->', '', title).strip()
                slug = get_slug(clean_title)
                
                if level <= 2:
                    filename = "index.html" if len(pages) == 0 else f"{slug}.html"
                    current_page = Page(clean_title, slug, filename, level)
                    pages.append(current_page)
                    slug_mapping[slug] = (filename, "")
                    base_slug = slugify(clean_title, '-')
                    if base_slug not in slug_mapping:
                        slug_mapping[base_slug] = (filename, "")
                else:
                    if current_page:
                        slug_mapping[slug] = (current_page.filename, f"#{slug}")
                        base_slug = slugify(clean_title, '-')
                        if base_slug not in slug_mapping:
                            slug_mapping[base_slug] = (current_page.filename, f"#{slug}")
        
        if current_page:
            current_page.lines.append(line)

    if not pages:
        print("No headers found.")
        return

    # Generate sidebar HTML once
    sidebar_html = "<nav class='sidebar'>\n<ul>\n"
    for p in pages:
        cls_name = "level-1" if p.level == 1 else "level-2"
        sidebar_html += f"<li class='{cls_name}'><a href='{p.filename}'>{p.title}</a></li>\n"
    sidebar_html += "</ul>\n</nav>"

    html_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - The Concise TypeScript Book</title>
    <link rel="stylesheet" href="site.css">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
</head>
<body>
    <div class="layout">
        {sidebar}
        <main class="content">
            {content}
        </main>
    </div>
</body>
</html>"""

    def replace_link(match):
        text = match.group(1)
        target_slug = match.group(2)
        if target_slug in slug_mapping:
            filename, anchor = slug_mapping[target_slug]
            return f"[{text}]({filename}{anchor})"
        return match.group(0)

    md = markdown.Markdown(extensions=[
        'fenced_code', 
        'tables', 
        TocExtension(slugify=slugify)
    ])

    for p in pages:
        content_md = "".join(p.lines)
        # Update intra-page `#hash` links to point to correct html files
        content_md = re.sub(r'\[(.*?)\]\(#([^\)]+)\)', replace_link, content_md)
        
        md.reset()
        content_html = md.convert(content_md)
        
        final_html = html_template.format(
            title=p.title,
            sidebar=sidebar_html,
            content=content_html
        )
        
        with open(p.filename, "w", encoding="utf-8") as f:
            f.write(final_html)

    print(f"Generated {len(pages)} HTML pages in {os.getcwd()}")

if __name__ == "__main__":
    main()
