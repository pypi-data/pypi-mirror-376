# Ryland

A simple static site generation library


## Current Features

- use of Jinja2 templates
- render page-level markdown including frontmatter support
- render markdown within data using filter
- pull data directly from JSON or YAML files within templates
- copy static files and directory trees (for stylesheets, scripts, fonts, images)
- generate hash for cache-busting
- built-in and custom compositional context transformations ("tubes") including ability to calculate some context variables from others


## History

I've generally found the framework-approach of most static site generators to either be far too complex for my needs or too restricted to just blogs or similar. Over the years, I've generated many static sites with lightweight, bespoke Python code and hosted them on GitHub pages. I've ended up repeating myself a lot so I'm now cleaning it all up and generalizing my prior work as this library.


## Changelog

Now see `CHANGELOG.md`


## Example Usage

`pip install ryland` (or equivalent).

Then write a build script of the following form:

```python
from ryland import Ryland

ROOT_DIR = Path(__file__).parent.parent
OUTPUT_DIR = ROOT_DIR / "output"
PANTRY_DIR = ROOT_DIR / "pantry"
TEMPLATE_DIR = ROOT_DIR / "templates"

ryland = Ryland(output_dir=OUTPUT_DIR, template_dir=TEMPLATE_DIR)

ryland.clear_output()

## copy and hash static files

ryland.copy_to_output(PANTRY_DIR / "style.css")
ryland.add_hash("style.css")

## render templates

ryland.render_template("404.html", "404.html")
ryland.render_template("about_us.html", "about-us/index.html")

# construct context variables

ryland.render_template("homepage.html", "index.html", {
    # context variables
})

## and/or generate from Markdown files

PAGES_DIR = Path(__file__).parent / "pages"

for page_file in PAGES_DIR.glob("*.md"):
    ryland.render_markdown(page_file, "page.html")
```

or, for more control, context transformations (or "tubes") can be explicitly composed together:

```python
for page_file in sorted(PAGES_DIR.glob("*.md")):
    ryland.render(
        load(page_file),
        markdown(frontmatter=True),
        {"url": f"/{page_file.stem}/"},
        collect_tags(),
        {"template_name": "page.html"},
    )
```

Also see `examples/` in this repo.


## Cache-Busting Hashes

The `add_hash` makes it possible to do

```html
<link rel="stylesheet" href="/style.css?{{ HASHES['style.css'] }}">
```

in the templates to bust the browser cache when a change is made to a stylesheet, script, etc.


## Render Markdown Method

`ryland.render_markdown` takes a `Path` to a Markdown file and a template name.

The Markdown is rendered to HTML and passed to the template as `content`. The YAML frontmatter (if it exists) is passed to the template as `frontmatter`.


## Markdown Filter

To render a markdown context variable:

```html
{{ content | markdown }}
```


## Data Function

You can put together your template context in your Python build script or you can pull data directly from a JSON or YAML file within a template.

Here's an example of the latter:

```html
<div>
  <h2>Latest News</h2>

  {% for news_item in data("news_list.json")[:3] %}
    <div>
      <div class="news-dateline">{{ news_item.dateline }}</div>
      <p>{{ news_item.content }}</p>
    </div>
  {% endfor %}
</div>
```


## Tubes

A "tube" is a function that takes a context dictionary and returns a new one while also being able to access the Ryland instance.

Built-in tubes in `ryland.tubes` include the follow:

- `load(source_path: Path)` loads the given path and puts it on the context as `source_path` and the contents as `source_content`.
- `markdown(frontmatter=False)` converts the Markdown in `source_content` to HTML and puts it in `content`. Optionally puts the YAML frontmatter in `frontmatter`
- `debug(pretty=True)` outputs the context at that point to stderr (by default pretty-printing it)
- `project(keys: list[str])` keeps only the listed keys in the context

Developers can write their own tubes, for example here to collect pages by tag:

```python
tags = defaultdict(list)

def collect_tags():
    def inner(ryland: Ryland, context: dict) -> dict:
        frontmatter = context["frontmatter"]
        for tag in frontmatter.get("tags", []):
            tags[tag].append(
                ryland.process(
                    context,
                    project(["frontmatter", "url"]),
                )
            )
        return context
    return inner
```

This builds up a dictionary `tags` which, for each tag, contains a list of contexts containing the frontmatter and url for each page with that tag in its frontmatter.

## Process Method 

The `ryland.process` method takes a series of dictionaries and tubes and builds up a new context.

## Render Method

The `ryland.render` method processes a series of dictionary and tubes and then uses the resultant context to render a template. The template name is given by `template_name` in the context and the output path is determined by the `url` in the context.

For example:

```python
for tag in tags:
    ryland.render(
        {
            "tag": tag,
            "pages": tags[tag],
            "url": f"/tag/{tag}/",
            "template_name": "tag.html",
        },
    )
```

## The Get Context Helper

`ryland.helpers.get_context` allows the retrieval of values from a context using dotted path notation and with defaulting.

For example, in 

```python
for page_file in sorted(PAGES_DIR.glob("*.md")):
    ryland.render(
        load(page_file),
        markdown(frontmatter=True),
        {"url": get_context("frontmatter.url", f"/{page_file.stem}/")},
        collect_tags(),
        {"template_name": get_context("frontmatter.template_name", "page.html")},
    )
```

the `url` and `template_name` can be overridden in the page's frontmatter.


## Sites Currently Using Ryland

- <https://projectamaze.com>
- <https://digitaltolkien.com>
- <https://jktauber.com>
- <https://cite.digitaltolkien.com>


## Roadmap

In no particular order:

- helpers for pagination
- move over other sites to use Ryland
- incorporate more common elements that emerge
- improve error handling
- produce a Ryland-generated website for Ryland
- document how to automatically build with GitHub actions
- write up a cookbook
- add a command-line tool for starting a Ryland-based site

Because Ryland is a library, a lot of missing features can just be implemented by the site developer.
However, if three or more sites duplicate effort in their build script, I'll consider at least adding helper code to Ryland.

Once five independent people are running sites built with Ryland, I will declare 1.0.0.
