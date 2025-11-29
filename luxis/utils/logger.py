import logging
import re
import sys

from http import HTTPStatus
from loguru import logger


level_icons = {
    "DEBUG": "🐞",
    "INFO": "ℹ️ ",
    "SUCCESS": " ✅",
    "WARNING": "⚠️ ",
    "ERROR": "🛑",
    "CRITICAL": "💥",
}

tags = ["red", "blue", "green", "magenta", "yellow", "blink", "bold", "white", "cyan", "black", "bold", "blink", "level", "le"]


def color_http(text):
    HTTP_METHODS = ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH", "HEAD"]

    def code_color(code):
        if 200 <= code < 300:
            return "green"
        elif 300 <= code < 400:
            return "yellow"
        elif 400 <= code < 600:
            return "red"
        else:
            return "white"

    for method in HTTP_METHODS:
        pattern = rf"\b{method}\b"
        replacement = f"<blue>{method}</blue>"
        text = re.sub(pattern, replacement, text)

    text = re.sub(
        r"\bhttps?\b",
        lambda m: f"<magenta>{m.group(0)}</magenta>",
        text,
        flags=re.IGNORECASE,
    )

    for status in HTTPStatus:
        code = str(status.value)
        color = code_color(status.value)
        pattern = rf"\b{code}\b"
        replacement = f"<{color}>{code}</{color}>"
        text = re.sub(pattern, replacement, text)

    return text


def colorize_outside_tags(text):
    result = []
    i = 0

    while i < len(text):
        if text[i] == "<":
            # Find the end of this potential tag
            tag_end = text.find(">", i)
            if tag_end != -1:
                potential_tag = text[i : tag_end + 1]
                # Check if it's a valid Loguru tag (including closing tags)
                if re.match(r"</?(?:red|green|blue|yellow|magenta|cyan|white|black|bold|blink|level|reset)>", potential_tag):
                    result.append(potential_tag)
                    i = tag_end + 1
                    continue

        # Colorize individual characters
        c = text[i]
        if c == ":":
            result.append("<red>:</red>")
        elif c == "/":
            result.append("<yellow>/</yellow>")
        elif c == ".":
            result.append("<green>.</green>")
        elif c == "{":
            result.append("<red>{</red>")
        elif c == "}":
            result.append("<red>}</red>")
        elif c == "[":
            result.append("<cyan>[</cyan>")
        elif c == "]":
            result.append("<cyan>]</cyan>")
        elif c == "'":
            result.append("<green>'</green>")
        elif c == '"':
            result.append('<green>"</green>')
        elif c == "_":
            result.append("<magenta>_</magenta>")
        elif c == "@":
            result.append("<magenta>@</magenta>")
        elif c == "*":
            result.append("<magenta>*</magenta>")
        elif c == "-":
            result.append("<magenta>-</magenta>")
        elif c == ",":
            result.append("<green>,</green>")
        else:
            result.append(c)
        i += 1

    return "".join(result)


def validate_balanced_tags(text):
    tags = {"red", "blue", "green", "magenta", "yellow", "blink", "bold", "white", "cyan", "black", "level"}
    tag_pattern = re.compile(r"<(/?)(\w+)>")
    stack = []
    for match in tag_pattern.finditer(text):
        is_close = match.group(1) == "/"
        name = match.group(2)
        if name not in tags:
            start, end = match.span()
            text = text[:start] + text[start:end].replace("<", "\\<") + text[end:]
            continue
        if not is_close:
            stack.append(name)
        else:
            if not stack or stack[-1] != name:
                return tag_pattern.sub(lambda m: "" if m.group(2) in tags else m.group(0), text)
            stack.pop()
    if stack:
        return tag_pattern.sub(lambda m: "" if m.group(2) in tags else m.group(0), text)
    return text


def escape(text):
    message_str = text.replace("{", "{{").replace("}", "}}")
    pattern = re.compile(r"(<[^>]+>|[A-Za-z0-9_]+>)")

    def escape_match(m):
        s = m.group(0)
        for tag in tags:
            if f"<{tag}>" == s:
                return s
            if f"</{tag}>" == s:
                return s
        return s.replace("<", "\\<")

    text = pattern.sub(escape_match, message_str)
    return text


def formatter(record):
    time_str = f"<green>{record['time']:%y-%m-%d %H:%M:%S}</green>"
    icon = level_icons.get(record["level"].name, "")
    if record["level"].name in ["WARNING", "ERROR", "CRITICAL"]:
        icon = f"<blink>{icon}</blink>"

    file_path = record["file"].path
    parts = file_path.split("migros-rag-service")
    file_path = "." + parts[-1]
    max_len = 40
    loc_content = f"{file_path}:{record['line']}"
    if len(loc_content) > max_len:
        loc_content = "..." + loc_content[-(max_len - 3) :]
    else:
        loc_content = loc_content.ljust(max_len)
    for base_dir in ["src", "eval", "tests"]:
        if base_dir in file_path:
            loc_content = f"<bold>{loc_content}</bold>"
            break
    loc_str = f"<white>{loc_content}</white>"

    message_str = str(record["message"])
    # message_str = message_str[:1024]

    message_str = colorize_outside_tags(message_str)
    message_str = color_http(message_str)
    message_str = escape(message_str)
    message_str = validate_balanced_tags(message_str)

    return "|".join([time_str, icon, loc_str + " ", " " + message_str]) + "\n"


def setup_logging(log_level="INFO", settings=None):
    if settings and hasattr(settings, "log_level"):
        log_level = settings.log_level
    logger.remove()
    logger.add(
        sys.stderr,
        colorize=True,
        format=formatter,
        level=log_level,
    )
    logging.basicConfig(handlers=[], level=0, force=True)

    class InterceptHandler(logging.Handler):
        def emit(self, record):
            try:
                level = logger.level(record.levelname).name
            except Exception:
                level = record.levelno
            logger_opt = logger.opt(depth=6, exception=record.exc_info)
            logger_opt.log(level, record.getMessage())

    logging.getLogger("uvicorn.error").handlers = [InterceptHandler()]
    logging.getLogger("uvicorn.access").handlers = [InterceptHandler()]
