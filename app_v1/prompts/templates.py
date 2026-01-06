"""Jinja2 templates loader and environment configuration."""

from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape

# Определяем путь к папке с шаблонами
TEMPLATES_DIR = Path(__file__).parent

# Создаём Jinja2 environment
jinja_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html", "xml"]),
    trim_blocks=True,
    lstrip_blocks=True,
)

PROMPT_TEMPLATES = {
    "first_text_base": jinja_env.get_template("first/caption/base.j2"),
    "first_text_context": jinja_env.get_template("first/caption/input.j2"),
    "first_image_base": jinja_env.get_template("first/image/base.j2"),
    "first_image_context": jinja_env.get_template("first/image/context.j2"),
    "readings_base": jinja_env.get_template("readings/base.j2"),
    "readings_context": jinja_env.get_template("readings/input.j2"),
    "ai_portraits_image_base": jinja_env.get_template("ai-portraits/image/base.j2"),
    "ai_portraits_image_context": jinja_env.get_template(
        "ai-portraits/image/context.j2"
    ),
    #  Не используется
    "ai_portraits_mode_explanation": jinja_env.get_template(
        "ai-portraits/image/mode_explanation.j2"
    ),
    "daily_card_image_base": jinja_env.get_template("daily_card/image/base.j2"),
    "daily_card_text_base": jinja_env.get_template("daily_card/text/base.j2"),
}
