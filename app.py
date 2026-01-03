#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import io
import random
import re
from datetime import datetime
from typing import List, Tuple

from flask import Flask, request, render_template_string, send_file
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

app = Flask(__name__)

# ----------------------------
# Frontend (oldschool AoC-ish)
# ----------------------------
HTML = r"""
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Math worksheet generator</title>
  <style>
    :root{
      --bg: #05142c;         /* dark blue */
      --panel: #040f22;      /* slightly darker */
      --text: #ffffff;
      --muted: rgba(255,255,255,.75);
      --border: rgba(255,255,255,.65);
      --border2: rgba(255,255,255,.25);
      --inputbg: #000000;
      --accent: rgba(255,255,255,.9);
    }

    html, body { height: 100%; }
    body{
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font-family: "Courier New", Courier, ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      font-size: 15px;
      line-height: 1.35;
    }

    .wrap{
      max-width: 980px;
      margin: 0 auto;
      padding: 24px 18px 40px 18px;
    }

    h1{
      margin: 0 0 10px 0;
      font-size: 22px;
      font-weight: 700;
      letter-spacing: .3px;
    }

    .subtitle{
      margin: 0 0 18px 0;
      color: var(--muted);
    }

    .panel{
      border: 1px solid var(--border2);
      background: var(--panel);
      padding: 16px;
    }

    form{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 14px 18px;
      align-items: start;
    }

    .full{ grid-column: 1 / -1; }

    label{
      display:block;
      font-weight: 700;
      margin-bottom: 6px;
    }

    input[type="text"], input[type="number"]{
      width: 100%;
      box-sizing: border-box;
      padding: 10px 10px;
      border: 1px solid var(--border);
      border-radius: 0;
      background: var(--inputbg);
      color: var(--text);
      font-family: inherit;
      font-size: 14px;
      outline: none;
    }
    input[type="text"]:focus, input[type="number"]:focus{
      border-color: var(--accent);
    }

    .hint{
      margin-top: 6px;
      font-size: 12px;
      color: var(--muted);
    }

    .checks{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px 14px;
      margin-top: 6px;
    }
    .check{
      display:flex;
      align-items:center;
      gap: 10px;
      color: var(--text);
    }
    /* ASCII checkboxes */
    .ascii-check{
    cursor: pointer;
    user-select: none;
    }

    .ascii-check input[type="checkbox"]{
    /* keep it in the DOM for form submit + accessibility, but visually hide */
    position: absolute;
    opacity: 0;
    width: 1px;
    height: 1px;
    pointer-events: none;
    }

    .ascii-check .box{
    display: inline-block;
    min-width: 3ch;           /* enough for "[x]" */
    }

    .ascii-check .box::before{
    content: "[ ]";
    }

    .ascii-check input[type="checkbox"]:checked + .box::before{
    content: "[x]";
    }

    /* keyboard focus (tabbing) */
    .ascii-check input[type="checkbox"]:focus + .box::before{
    outline: 1px solid var(--border);
    outline-offset: 2px;
    }

    /* optional: slightly dim label like AoC */
    .ascii-check .label{
    color: var(--text);
    }

    .btnrow{
      display:flex;
      gap: 12px;
      align-items:center;
      margin-top: 8px;
    }

    button{
      border: 1px solid var(--border);
      background: #000;
      color: var(--text);
      font-family: inherit;
      font-size: 14px;
      padding: 10px 14px;
      cursor: pointer;
    }
    button:hover{
      background: rgba(255,255,255,.08);
    }

    .err{
      margin: 12px 0 0 0;
      color: #ffb3b3;
      font-weight: 700;
      white-space: pre-wrap;
    }

    .footer{
      margin-top: 14px;
      color: var(--muted);
      font-size: 12px;
    }

    code{
      font-family: inherit;
      border: 1px solid var(--border2);
      padding: 1px 6px;
      background: rgba(0,0,0,.35);
    }

    @media (max-width: 820px){
      form{ grid-template-columns: 1fr; }
      .checks{ grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <div class="wrap">
    <h1>Math worksheet generator</h1>
    <p class="subtitle">
      Generates worksheets as PDF.
    </p>

    <div class="panel">
      <form method="post" action="/generate">
        <div>
          <label for="a">Allowed values for first number</label>
          <input id="a" name="a" type="text" value="{{defaults.a}}" />
          <div class="hint">Examples: <code>0-10</code>, <code>-10--5</code>, <code> .1 -.2 .3 .456</code></div>
        </div>

        <div>
          <label for="b">Allowed values for second number</label>
          <input id="b" name="b" type="text" value="{{defaults.b}}" />
          <div class="hint">Examples: <code>6-10, 100, -99, .1</code>, <code>3</code></div>
        </div>

        <div>
          <label for="ops">Operators</label>
          <input id="ops" name="ops" type="text" value="{{defaults.ops}}" />
          <div class="hint">Examples: <code>+</code>, <code>+-*</code>, <code>/ ×</code> <code>•,÷</code></div>
        </div>

        <div>
          <label for="pages">Number of pages</label>
          <input id="pages" name="pages" type="number" min="1" max="100" value="{{defaults.pages}}" />
          <div class="hint">Each page contains 60 problems.</div>
        </div>

        <div class="full">
          <label for="title">Header</label>
          <input id="title" name="title" type="text" value="{{defaults.title}}" />
        </div>

        <div class="full">
          <div class="checks">
            <label class="check ascii-check">
                <input type="checkbox" name="answers" {% if defaults.answers %}checked{% endif %}/>
                <span class="box" aria-hidden="true"></span>
                <span class="label">answers</span>
            </label>

            <label class="check ascii-check">
                <input type="checkbox" name="numbered" {% if defaults.numbered %}checked{% endif %}/>
                <span class="box" aria-hidden="true"></span>
                <span class="label">numbering</span>
            </label>

            <label class="check ascii-check">
                <input type="checkbox" name="avoid_negative" {% if defaults.avoid_negative %}checked{% endif %}/>
                <span class="box" aria-hidden="true"></span>
                <span class="label">non-negative answers (subtraction)</span>
            </label>

            <label class="check ascii-check">
                <input type="checkbox" name="integer_division" {% if defaults.integer_division %}checked{% endif %}/>
                <span class="box" aria-hidden="true"></span>
                <span class="label">integer answers (division)</span>
            </label>
          </div>
        </div>

        <div class="full">
          <div class="btnrow">
            <button type="submit">Generate PDF</button>
          </div>
          {% if error %}
            <div class="err">{{error}}</div>
          {% endif %}
          <div class="footer">
          </div>
        </div>
      </form>
    </div>
  </div>
</body>
</html>
"""

# ----------------------------
# Parsing + math generation
# ----------------------------
NUM_RE = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)$")
RANGE_RE = re.compile(r"^\s*([+-]?(?:\d+(?:\.\d*)?|\.\d+))\s*-\s*([+-]?(?:\d+(?:\.\d*)?|\.\d+))\s*$")

Problem = Tuple[float, str, float]  # (a, op_symbol, b)

OP_SYMBOLS = {"+", "-", "*", "/", "•", "×", "÷"}
OP_TO_INTERNAL = {
    "+": "+",
    "-": "-",
    "*": "*",
    "•": "*",
    "×": "*",
    "/": "/",
    "÷": "/",
}


def defaults():
    return {
        "a": "0-10",
        "b": "0-10",
        "ops": "+",
        "pages": 1,
        "answers": True,
        "numbered": True,
        "avoid_negative": False,
        "integer_division": True,
        "title": "Math worksheet",
    }


def parse_number(token: str) -> float:
    t = token.strip()
    if not NUM_RE.match(t):
        raise ValueError(f"Invalid number: {token!r}")
    return float(t)


def is_int_like(x: float, tol: float = 1e-12) -> bool:
    return abs(x - round(x)) <= tol


def parse_number_set(spec: str) -> List[float]:
    spec = (spec or "").strip()
    if not spec:
        raise ValueError("Empty number specification.")

    tokens = [t for t in re.split(r"[,\s]+", spec) if t.strip()]
    out: List[float] = []

    for tok in tokens:
        m = RANGE_RE.match(tok)
        if m:
            a = parse_number(m.group(1))
            b = parse_number(m.group(2))
            if not (is_int_like(a) and is_int_like(b)):
                raise ValueError(f"Ranges require integer endpoints: {tok!r}")
            ai, bi = int(round(a)), int(round(b))
            step = 1 if bi >= ai else -1
            out.extend([float(i) for i in range(ai, bi + step, step)])
        else:
            out.append(parse_number(tok))

    # stable unique
    seen = set()
    uniq: List[float] = []
    for x in out:
        key = round(float(x), 12)
        if key in seen:
            continue
        seen.add(key)
        uniq.append(float(x))

    if not uniq:
        raise ValueError("No valid numbers parsed.")
    return uniq


def parse_ops(spec: str) -> List[str]:
    spec = (spec or "").strip()
    if not spec:
        return ["+"]

    if "," in spec:
        ops = [s.strip() for s in spec.split(",") if s.strip()]
    else:
        ops = list(spec)

    ops = [o for o in ops if o in OP_SYMBOLS]
    if not ops:
        raise ValueError("No valid operators.")
    return ops


def division_ok(a: float, b: float, require_int: bool, tol: float = 1e-9) -> bool:
    if b == 0:
        return False
    if not require_int:
        return True
    q = a / b
    return abs(q - round(q)) <= tol


def compute_answer(a: float, op_symbol: str, b: float) -> float:
    op = OP_TO_INTERNAL[op_symbol]
    if op == "+":
        return a + b
    if op == "-":
        return a - b
    if op == "*":
        return a * b
    if op == "/":
        return a / b
    raise ValueError("Unknown operator")


def pick_problem(
    a_vals: List[float],
    b_vals: List[float],
    ops: List[str],
    avoid_negative: bool,
    integer_division: bool,
    tries: int = 50_000,
) -> Problem:
    for _ in range(tries):
        op_symbol = random.choice(ops)
        a = random.choice(a_vals)
        b = random.choice(b_vals)

        internal = OP_TO_INTERNAL[op_symbol]
        if internal == "/":
            if not division_ok(a, b, require_int=integer_division):
                continue
        if internal == "-" and avoid_negative:
            if a - b < 0:
                continue

        return a, op_symbol, b

    raise RuntimeError(
        "Could not generate problems with these constraints.\n"
        "Try widening a/b, disabling integer division, or removing some operators."
    )


def fmt_num(x: float) -> str:
    if is_int_like(x):
        return str(int(round(x)))
    return f"{x:.12g}"


def fmt_answer(x: float) -> str:
    if is_int_like(x):
        return str(int(round(x)))
    return f"{x:.12g}"


# ----------------------------
# PDF rendering (Courier header/footer)
# ----------------------------
def draw_header(c: canvas.Canvas, header: str):
    """
    Header in Courier (monospace). No date here.
    """
    width, height = A4
    margin_left = 50
    margin_top = 48  # a bit tighter than before

    c.setFont("Courier-Bold", 14)
    c.drawString(margin_left, height - margin_top, header)


def draw_footer(c: canvas.Canvas, date_str: str, page_num: int):
    """
    Footer in Courier: date on left, page number on right (just the number).
    """
    width, _ = A4
    margin_left = 50
    margin_right = 50
    y = 28

    c.setFont("Courier", 9)
    c.drawString(margin_left, y, date_str)
    c.drawRightString(width - margin_right, y, str(page_num))


def draw_page_problems(
    c: canvas.Canvas,
    problems: List[Problem],
    header: str,
    numbered: bool,
    date_str: str,
    page_num: int,
):
    width, height = A4
    margin_left = 50
    margin_right = 50
    margin_top = 48
    margin_bottom = 50

    cols = 3
    rows_per_col = 20
    col_gap = 30

    if len(problems) != cols * rows_per_col:
        raise ValueError("Internal error: expected exactly 60 problems per page.")

    usable_width = width - margin_left - margin_right - (col_gap * (cols - 1))
    col_w = usable_width / cols

    draw_header(c, header)
    draw_footer(c, date_str, page_num)

    c.setFont("Courier", 13)

    start_y = height - margin_top - 32
    usable_h = start_y - margin_bottom
    row_h = usable_h / rows_per_col

    for col in range(cols):
        x = margin_left + col * (col_w + col_gap)
        for r in range(rows_per_col):
            idx = col * rows_per_col + r
            a, op_symbol, b = problems[idx]
            y = start_y - r * row_h
            prefix = f"{idx+1:2d}) " if numbered else ""
            c.drawString(x, y, f"{prefix}{fmt_num(a)} {op_symbol} {fmt_num(b)} = ")


def draw_page_answers(
    c: canvas.Canvas,
    problems: List[Problem],
    header: str,
    numbered: bool,
    date_str: str,
    page_num: int,
):
    width, height = A4
    margin_left = 50
    margin_right = 50
    margin_top = 48
    margin_bottom = 50

    cols = 3
    rows_per_col = 20
    col_gap = 30

    if len(problems) != cols * rows_per_col:
        raise ValueError("Internal error: expected exactly 60 problems per page.")

    usable_width = width - margin_left - margin_right - (col_gap * (cols - 1))
    col_w = usable_width / cols

    draw_header(c, header)
    draw_footer(c, date_str, page_num)

    c.setFont("Courier", 12)

    start_y = height - margin_top - 32
    usable_h = start_y - margin_bottom
    row_h = usable_h / rows_per_col

    for col in range(cols):
        x = margin_left + col * (col_w + col_gap)
        for r in range(rows_per_col):
            idx = col * rows_per_col + r
            a, op_symbol, b = problems[idx]
            ans = compute_answer(a, op_symbol, b)
            y = start_y - r * row_h
            prefix = f"{idx+1:2d}) " if numbered else ""
            c.drawString(x, y, f"{prefix}{fmt_num(a)} {op_symbol} {fmt_num(b)} = {fmt_answer(ans)}")


# ----------------------------
# Field-wise fallback helpers
# ----------------------------
def safe_parse_number_set(user_spec: str, default_spec: str) -> List[float]:
    try:
        return parse_number_set(user_spec)
    except Exception:
        return parse_number_set(default_spec)


def safe_parse_ops(user_spec: str, default_spec: str) -> List[str]:
    try:
        return parse_ops(user_spec)
    except Exception:
        return parse_ops(default_spec)


def safe_int(user_value: str, default_value: int, lo: int, hi: int) -> int:
    try:
        v = int(str(user_value).strip())
        if v < lo or v > hi:
            return default_value
        return v
    except Exception:
        return default_value


def safe_header(user_value: str, default_value: str) -> str:
    # Treat empty/whitespace as "junk" => fallback
    if user_value is None:
        return default_value
    s = str(user_value).strip()
    return s if s else default_value


def build_pdf(
    a_spec: str,
    b_spec: str,
    ops_spec: str,
    pages: int,
    include_answers: bool,
    numbered: bool,
    avoid_negative: bool,
    integer_division: bool,
    header: str,
    defaults_dict: dict,
) -> bytes:
    # Field-wise fallback:
    a_vals = safe_parse_number_set(a_spec, defaults_dict["a"])
    b_vals = safe_parse_number_set(b_spec, defaults_dict["b"])
    ops = safe_parse_ops(ops_spec, defaults_dict["ops"])

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)

    date_str = datetime.now().strftime("%Y-%m-%d")
    
    current_page = 0

    # Alternative A: problems then answers (optional) for each worksheet page
    for worksheet_idx in range(1, pages + 1):
        problems: List[Problem] = []
        for _ in range(60):
            problems.append(
                pick_problem(
                    a_vals=a_vals,
                    b_vals=b_vals,
                    ops=ops,
                    avoid_negative=avoid_negative,
                    integer_division=integer_division,
                )
            )

        # Problems page
        current_page += 1
        header_p = header if pages == 1 else f"{header} (Set {worksheet_idx})"
        draw_page_problems(
            c, problems, header_p, numbered, date_str, current_page
        )
        c.showPage()

        # Answers page (optional)
        if include_answers:
            current_page += 1
            header_a = (header + " – Answers") if pages == 1 else f"{header} – Answers (Set {worksheet_idx})"
            draw_page_answers(
                c, problems, header_a, numbered, date_str, current_page
            )
            c.showPage()

    c.save()
    buf.seek(0)
    return buf.read()


# ----------------------------
# Flask routes
# ----------------------------
@app.get("/")
def index():
    return render_template_string(HTML, defaults=defaults(), error=None)


@app.post("/generate")
def generate():
    d = defaults()

    # Always keep user's inputs in the form (even if we fallback in generation)
    form_defaults = {
        "a": request.form.get("a", d["a"]),
        "b": request.form.get("b", d["b"]),
        "ops": request.form.get("ops", d["ops"]),
        "pages": request.form.get("pages", d["pages"]),
        "answers": request.form.get("answers") is not None,
        "numbered": request.form.get("numbered") is not None,
        "avoid_negative": request.form.get("avoid_negative") is not None,
        "integer_division": request.form.get("integer_division") is not None,
        "title": request.form.get("title", d["title"]),
    }

    try:
        # Read raw strings
        a_raw = request.form.get("a", d["a"])
        b_raw = request.form.get("b", d["b"])
        ops_raw = request.form.get("ops", d["ops"])
        pages_raw = request.form.get("pages", str(d["pages"]))
        header_raw = request.form.get("title", d["title"])

        # Checkboxes
        include_answers = request.form.get("answers") is not None
        numbered = request.form.get("numbered") is not None
        avoid_negative = request.form.get("avoid_negative") is not None
        integer_division = request.form.get("integer_division") is not None

        # Per-field fallback:
        pages = safe_int(pages_raw, d["pages"], lo=1, hi=100)
        header = safe_header(header_raw, d["title"])

        pdf_bytes = build_pdf(
            a_spec=a_raw,
            b_spec=b_raw,
            ops_spec=ops_raw,
            pages=pages,
            include_answers=include_answers,
            numbered=numbered,
            avoid_negative=avoid_negative,
            integer_division=integer_division,
            header=header,
            defaults_dict=d,
        )

        filename = f"worksheet_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype="application/pdf",
            as_attachment=True,
            download_name=filename,
        )

    except Exception as e:
        # This should now mainly trigger only for truly unexpected issues
        return render_template_string(HTML, defaults=form_defaults, error=str(e)), 400


# if __name__ == "__main__":
#     app.run()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)