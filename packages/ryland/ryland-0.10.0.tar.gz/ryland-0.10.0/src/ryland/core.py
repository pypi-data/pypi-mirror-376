from hashlib import md5
import json
from os import makedirs
from pathlib import Path
from shutil import copy, copytree, rmtree
from typing import Any, Optional

import jinja2
import markdown as markdown_lib
import yaml

from .tubes import load, markdown


class Ryland:
    def __init__(
        self,
        root_file: Optional[str] = None,
        output_dir: Optional[Path] = None,
        template_dir: Optional[Path] = None,
    ):
        if output_dir is None:
            if root_file is not None:
                output_dir = Path(root_file).parent / "output"
            else:
                raise ValueError("root_file must be provided if output_dir is not")

        if template_dir is None:
            if root_file is not None:
                template_dir = Path(root_file).parent / "templates"
            else:
                raise ValueError("root_file must be provided if template_dir is not")

        self.output_dir = output_dir
        self.template_dir = template_dir

        self.hashes = {}

        self._markdown = markdown_lib.Markdown(
            extensions=["fenced_code", "codehilite", "tables", "full_yaml_metadata"]
        )

        self.jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(template_dir)
        )
        self.jinja_env.globals["data"] = load_data
        self.jinja_env.filters["markdown"] = self._markdown.convert

    def clear_output(self) -> None:
        makedirs(self.output_dir, exist_ok=True)
        for child in self.output_dir.iterdir():
            if child.is_dir():
                rmtree(child)
            else:
                child.unlink()

    def copy_to_output(self, source: Path) -> None:
        if source.is_dir():
            dest = self.output_dir / source.name
            copytree(source, dest, dirs_exist_ok=True)
        else:
            copy(source, self.output_dir / source.name)

    def add_hash(self, filename: str) -> None:
        self.hashes[filename] = make_hash(self.output_dir / filename)

    def render_template(
        self, template_name: str, output_filename: str, context: Optional[dict] = None
    ) -> None:
        context = context or {}
        template = self.jinja_env.get_template(template_name)
        output_path = self.output_dir / output_filename
        makedirs(output_path.parent, exist_ok=True)
        with open(output_path, "w") as f:
            f.write(
                template.render(
                    {
                        "HASHES": self.hashes,
                        **context,
                    }
                )
            )

    def process(self, *tubes) -> dict:
        context = {}
        for tube in tubes:
            if isinstance(tube, dict):
                context = {
                    **context,
                    **{
                        key: value(context) if callable(value) else value
                        for key, value in tube.items()
                    },
                }
            else:
                context = tube(self, context)
        return context

    def render(self, *tubes) -> None:
        context = self.process(*tubes)
        template_name = context["template_name"]
        output_filename = context["url"].lstrip("/")
        if output_filename.endswith("/"):
            output_filename += "index.html"
        self.render_template(template_name, output_filename, context)

    def render_markdown(self, markdown_file: Path, template_name: str) -> None:
        file_path = f"{markdown_file.stem}/index.html"
        self.render_template(
            template_name,
            file_path,
            self.process(load(markdown_file), markdown(frontmatter=True)),
        )


def make_hash(path) -> str:
    hasher = md5()
    hasher.update(path.read_bytes())
    return hasher.hexdigest()


def load_data(filename) -> Any:
    if filename.endswith(".json"):
        return json.load(open(filename))
    elif filename.endswith((".yml", ".yaml")):
        return yaml.safe_load(open(filename))
