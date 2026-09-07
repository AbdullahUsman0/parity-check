from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.oxml.ns import nsmap
from pptx.oxml import parse_xml

# Design system
INK = RGBColor(15, 27, 51)
INK_LIGHT = RGBColor(29, 45, 79)
BG = RGBColor(250, 249, 246)
ACCENT = RGBColor(13, 148, 136)
ACCENT_LIGHT = RGBColor(230, 244, 243)
WARN = RGBColor(245, 158, 11)
DANGER = RGBColor(220, 38, 38)
MUTED = RGBColor(107, 114, 128)
BORDER = RGBColor(229, 231, 235)

SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)
MARGIN_L = Inches(0.75)
MARGIN_R = Inches(0.75)
MARGIN_T = Inches(0.9)
MARGIN_B = Inches(0.6)


def set_slide_bg(slide, color):
    background = slide.background
    fill = background.fill
    fill.solid()
    fill.fore_color.rgb = color


def add_textbox(slide, left, top, width, height, text, font_size=18, bold=False,
                color=INK, align=PP_ALIGN.LEFT, font_name="Calibri", italic=False):
    box = slide.shapes.add_textbox(left, top, width, height)
    tf = box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text
    p.alignment = align
    run = p.runs[0]
    run.font.size = Pt(font_size)
    run.font.bold = bold
    run.font.color.rgb = color
    run.font.name = font_name
    run.font.italic = italic
    return box


def add_footer(slide, number):
    add_textbox(slide, MARGIN_L, SLIDE_H - Inches(0.45), Inches(2), Inches(0.3),
                "ParityLens", font_size=11, bold=True, color=INK)
    add_textbox(slide, SLIDE_W - Inches(1.5), SLIDE_H - Inches(0.45), Inches(1), Inches(0.3),
                f"{number} / 15", font_size=11, color=MUTED, align=PP_ALIGN.RIGHT)
    line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, MARGIN_L, SLIDE_H - Inches(0.55), SLIDE_W - MARGIN_L - MARGIN_R, Inches(0.01))
    line.fill.solid()
    line.fill.fore_color.rgb = BORDER
    line.line.fill.background()


def add_header(slide, label):
    add_textbox(slide, MARGIN_L, Inches(0.25), Inches(6), Inches(0.3),
                label.upper(), font_size=10, bold=True, color=MUTED)


def add_headline(slide, text, top=Inches(1.0), font_size=32):
    return add_textbox(slide, MARGIN_L, top, SLIDE_W - MARGIN_L - MARGIN_R, Inches(1.0),
                       text, font_size=font_size, bold=True, color=INK)


def add_card(slide, left, top, width, height, title, body, tag=None):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = RGBColor(255, 255, 255)
    shape.line.color.rgb = BORDER
    shape.line.width = Pt(1)
    shape.adjustments[0] = 0.08

    if tag:
        tag_w = Inches(0.85)
        tag_h = Inches(0.22)
        tag_box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left + Inches(0.15), top + Inches(0.15), tag_w, tag_h)
        tag_box.fill.solid()
        tag_box.fill.fore_color.rgb = ACCENT_LIGHT
        tag_box.line.fill.background()
        tag_box.adjustments[0] = 0.2
        add_textbox(slide, left + Inches(0.15), top + Inches(0.15), tag_w, tag_h,
                    tag.upper(), font_size=9, bold=True, color=ACCENT, align=PP_ALIGN.CENTER)
        title_top = top + Inches(0.45)
    else:
        title_top = top + Inches(0.2)

    add_textbox(slide, left + Inches(0.15), title_top, width - Inches(0.3), Inches(0.35),
                title, font_size=13, bold=True, color=INK)
    add_textbox(slide, left + Inches(0.15), title_top + Inches(0.35), width - Inches(0.3), height - Inches(0.6),
                body, font_size=11, color=MUTED)


def add_bullet_list(slide, left, top, width, height, items, font_size=15):
    box = slide.shapes.add_textbox(left, top, width, height)
    tf = box.text_frame
    tf.word_wrap = True
    for i, item in enumerate(items):
        if i == 0:
            p = tf.paragraphs[0]
        else:
            p = tf.add_paragraph()
        p.text = "•  " + item
        p.level = 0
        p.space_after = Pt(10)
        run = p.runs[0]
        run.font.size = Pt(font_size)
        run.font.color.rgb = INK_LIGHT
        run.font.name = "Calibri"
    return box


def add_rounded_rect(slide, left, top, width, height, fill, stroke=None, stroke_width=Pt(1)):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill
    if stroke:
        shape.line.color.rgb = stroke
        shape.line.width = stroke_width
    else:
        shape.line.fill.background()
    shape.adjustments[0] = 0.08
    return shape


def add_arrow(slide, x1, y1, x2, y2, color=ACCENT, width=Pt(2)):
    line = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, x1, y1, x2, y2)
    line.line.color.rgb = color
    line.line.width = width
    # Note: python-pptx doesn't support arrowheads easily on connectors, so we add a small triangle
    return line


prs = Presentation()
prs.slide_width = SLIDE_W
prs.slide_height = SLIDE_H
blank_layout = prs.slide_layouts[6]  # blank

# Slide 1: Title
slide = prs.slides.add_slide(blank_layout)
set_slide_bg(slide, BG)
add_textbox(slide, 0, Inches(2.2), SLIDE_W, Inches(1.5), "ParityLens",
            font_size=72, bold=True, color=INK, align=PP_ALIGN.CENTER)
add_textbox(slide, 0, Inches(3.7), SLIDE_W, Inches(0.8),
            "Catching bilingual exam errors before they reach students.",
            font_size=22, color=INK_LIGHT, align=PP_ALIGN.CENTER)
add_textbox(slide, 0, Inches(4.8), SLIDE_W, Inches(0.5),
            "Alibaba Cloud AI Hackathon Pakistan 2026",
            font_size=13, color=MUTED, align=PP_ALIGN.CENTER)
add_footer(slide, 1)

# Slide 2: Problem
slide = prs.slides.add_slide(blank_layout)
set_slide_bg(slide, BG)
add_header(slide, "The Problem")
add_headline(slide, "Two students. One exam. Two different questions.")
add_textbox(slide, MARGIN_L, Inches(2.15), Inches(5.8), Inches(2.2),
            "Pakistani boards publish bilingual Urdu/English question papers so students can answer in the language they know best.\n\n"
            "A documented Lahore-board case found Urdu and English versions of the same Chemistry and Physics questions that asked genuinely different things — not awkward wording, different questions.\n\n"
            "This silently changes who gets which marks, based only on which language paper a student happened to read.",
            font_size=15, color=INK_LIGHT)
add_textbox(slide, MARGIN_L, Inches(4.6), Inches(5.8), Inches(0.3),
            "Source: reported Lahore board mismatch case", font_size=9, color=MUTED, italic=True)
# Example boxes
add_rounded_rect(slide, Inches(7.0), Inches(2.15), Inches(5.5), Inches(1.15), RGBColor(255, 255, 255), BORDER)
add_textbox(slide, Inches(7.15), Inches(2.25), Inches(5.2), Inches(0.25), "ENGLISH VERSION", font_size=9, bold=True, color=MUTED)
add_textbox(slide, Inches(7.15), Inches(2.55), Inches(5.2), Inches(0.5), 'Which gas is not a greenhouse gas?', font_size=14, color=INK)

add_rounded_rect(slide, Inches(7.0), Inches(3.55), Inches(5.5), Inches(1.55), RGBColor(254, 242, 242), DANGER)
add_textbox(slide, Inches(7.15), Inches(3.65), Inches(5.2), Inches(0.25), "URDU VERSION — ILLUSTRATIVE EXAMPLE", font_size=9, bold=True, color=MUTED)
add_textbox(slide, Inches(7.15), Inches(3.95), Inches(5.2), Inches(0.45), "کونسی گیس گرین ہاؤس گیس ہے؟", font_size=16, color=INK)
add_textbox(slide, Inches(7.15), Inches(4.45), Inches(5.2), Inches(0.3), '("Which gas is a greenhouse gas?")', font_size=11, color=MUTED)

add_textbox(slide, Inches(7.0), Inches(5.25), Inches(5.5), Inches(0.3), "Illustrative example, not a real leaked question.",
            font_size=9, color=MUTED, align=PP_ALIGN.CENTER)
add_footer(slide, 2)

# Slide 3: Growing
slide = prs.slides.add_slide(blank_layout)
set_slide_bg(slide, BG)
add_header(slide, "Growing Surface Area")
add_headline(slide, "This is expanding, not shrinking.")
add_textbox(slide, MARGIN_L, Inches(2.15), Inches(5.8), Inches(2.4),
            "In 2026, the Punjab Board of Technical Education announced it will run Diploma of Information Technology exams in both Urdu and English — explicitly to give students a fairer chance to show what they know.\n\n"
            "That is the right intention. But every new bilingual paper is a new surface for silent drift, and right now nothing checks this systematically at scale.",
            font_size=15, color=INK_LIGHT)
add_textbox(slide, MARGIN_L, Inches(4.85), Inches(5.8), Inches(0.3),
            "Source: Punjab Board of Technical Education, 2026 bilingual DIT announcement", font_size=9, color=MUTED, italic=True)
# Simple growth arrow
add_rounded_rect(slide, Inches(7.0), Inches(2.4), Inches(5.5), Inches(3.0), RGBColor(255, 255, 255), BORDER)
add_textbox(slide, Inches(7.3), Inches(2.6), Inches(4.9), Inches(0.4), "Bilingual exam adoption", font_size=14, bold=True, color=ACCENT, align=PP_ALIGN.CENTER)
# Draw arrow line
line = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(7.8), Inches(5.0), Inches(11.7), Inches(3.0))
line.line.color.rgb = ACCENT
line.line.width = Pt(3)
add_textbox(slide, Inches(7.4), Inches(5.1), Inches(1.0), Inches(0.3), "Today", font_size=10, color=MUTED, align=PP_ALIGN.CENTER)
add_textbox(slide, Inches(11.1), Inches(2.7), Inches(1.8), Inches(0.5), "More bilingual papers", font_size=10, color=MUTED, align=PP_ALIGN.CENTER)
add_textbox(slide, Inches(7.3), Inches(5.5), Inches(4.9), Inches(0.3), "Conceptual trend. No fabricated numeric data.", font_size=9, color=MUTED, align=PP_ALIGN.CENTER)
add_footer(slide, 3)

# Slide 4: AI gap
slide = prs.slides.add_slide(blank_layout)
set_slide_bg(slide, BG)
add_header(slide, "AI Readiness Gap")
add_headline(slide, "Urdu is still underserved by AI.")
add_textbox(slide, MARGIN_L, Inches(2.15), Inches(5.8), Inches(2.2),
            "Generic translation or QA tools do not already solve this.\n\n"
            "UrduMMLU (2026) is a benchmark built from 26,431 native Urdu multiple-choice questions drawn from real exam material. It found large performance gaps for current AI models on Urdu-language academic content.\n\n"
            "That is exactly why a system for this language pair has to be purpose-built, not borrowed off the shelf.",
            font_size=15, color=INK_LIGHT)
add_textbox(slide, MARGIN_L, Inches(4.6), Inches(5.8), Inches(0.3), "Source: UrduMMLU, 2026 benchmark", font_size=9, color=MUTED, italic=True)
# Gap bars
add_rounded_rect(slide, Inches(7.5), Inches(2.5), Inches(1.6), Inches(3.0), ACCENT_LIGHT, ACCENT)
add_rounded_rect(slide, Inches(9.8), Inches(4.45), Inches(1.6), Inches(1.05), RGBColor(243, 244, 246), BORDER)
add_textbox(slide, Inches(7.4), Inches(5.65), Inches(1.8), Inches(0.6), "Performance gap on Urdu academic content", font_size=10, color=INK, align=PP_ALIGN.CENTER)
add_textbox(slide, Inches(9.7), Inches(5.65), Inches(1.8), Inches(0.6), "English academic content", font_size=10, color=MUTED, align=PP_ALIGN.CENTER)
add_textbox(slide, Inches(7.0), Inches(6.35), Inches(5.5), Inches(0.3), "Illustrative comparison, not exact benchmark scores.", font_size=9, color=MUTED, align=PP_ALIGN.CENTER)
add_footer(slide, 4)

# Slide 5: What it is / is not
slide = prs.slides.add_slide(blank_layout)
set_slide_bg(slide, BG)
add_header(slide, "Product Definition")
add_headline(slide, "An independent QA gate that checks Urdu/English exam papers mean the same thing, before they print.", font_size=26)
# Is
add_rounded_rect(slide, MARGIN_L, Inches(2.4), Inches(5.7), Inches(3.8), RGBColor(255, 255, 255), BORDER)
add_textbox(slide, MARGIN_L + Inches(0.2), Inches(2.55), Inches(5.3), Inches(0.35), "WHAT IT IS", font_size=11, bold=True, color=ACCENT)
add_bullet_list(slide, MARGIN_L + Inches(0.2), Inches(3.0), Inches(5.3), Inches(3.0),
                ["An independent verification layer",
                 "Applied after both language versions already exist",
                 "Evidence-backed, with confidence scores",
                 "Human-reviewed before any verdict"], font_size=15)
# Is not
add_rounded_rect(slide, Inches(7.0), Inches(2.4), Inches(5.7), Inches(3.8), RGBColor(249, 250, 251), BORDER)
add_textbox(slide, Inches(7.2), Inches(2.55), Inches(5.3), Inches(0.35), "WHAT IT IS NOT", font_size=11, bold=True, color=MUTED)
add_bullet_list(slide, Inches(7.2), Inches(3.0), Inches(5.3), Inches(3.0),
                ["A translator",
                 "A question generator",
                 "An autograder",
                 "A fully automated rejection system"], font_size=15)
add_footer(slide, 5)

# Slide 6: Pipeline
slide = prs.slides.add_slide(blank_layout)
set_slide_bg(slide, BG)
add_header(slide, "How It Works")
add_headline(slide, "From upload to cleared paper.")
# Pipeline boxes
stages = [
    ("Upload", "PDF / images"),
    ("OCR &\nSegmentation", ""),
    ("Bilingual\nAlignment", ""),
    ("Deterministic\nRule Checks", "numbers, units, options..."),
    ("Risk-Ranked\nReviewer Queue", ""),
    ("Human\nReview", ""),
    ("Cleared\n/ Export", ""),
]
box_w = Inches(1.45)
box_h = Inches(0.85)
start_x = Inches(0.55)
y = Inches(2.5)
for i, (title, sub) in enumerate(stages):
    x = start_x + i * Inches(1.75)
    fill = ACCENT_LIGHT if "Rule" in title or "Deterministic" in title else RGBColor(255, 255, 255)
    stroke = ACCENT if "Rule" in title or "Deterministic" in title else BORDER
    add_rounded_rect(slide, x, y, box_w, box_h, fill, stroke)
    add_textbox(slide, x, y + Inches(0.08), box_w, Inches(0.45), title, font_size=10, bold=True, color=INK, align=PP_ALIGN.CENTER)
    if sub:
        add_textbox(slide, x, y + Inches(0.52), box_w, Inches(0.25), sub, font_size=8, color=MUTED, align=PP_ALIGN.CENTER)
    if i < len(stages) - 1:
        line = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, x + box_w, y + box_h / 2, x + Inches(1.75), y + box_h / 2)
        line.line.color.rgb = ACCENT
        line.line.width = Pt(2)
# Semantic box below
sx = start_x + 3 * Inches(1.75)
sy = Inches(3.65)
add_rounded_rect(slide, sx, sy, box_w, box_h, ACCENT_LIGHT, ACCENT)
add_textbox(slide, sx, sy + Inches(0.08), box_w, Inches(0.45), "Semantic\nEquivalence", font_size=10, bold=True, color=INK, align=PP_ALIGN.CENTER)
add_textbox(slide, sx, sy + Inches(0.52), box_w, Inches(0.25), "meaning-level drift", font_size=8, color=MUTED, align=PP_ALIGN.CENTER)
# Connect alignment to semantic
line = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, sx - Inches(0.3), y + box_h / 2, sx + box_w / 2, sy)
line.line.color.rgb = ACCENT
line.line.width = Pt(2)
# Connect semantic to reviewer queue
line = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, sx + box_w, sy + box_h / 2, sx + Inches(1.75), y + box_h / 2)
line.line.color.rgb = ACCENT
line.line.width = Pt(2)
add_textbox(slide, MARGIN_L, Inches(4.8), SLIDE_W - MARGIN_L - MARGIN_R, Inches(0.7),
            "Every flagged question is shown with the exact evidence that triggered it. A paper is only cleared after a human reviewer signs off.",
            font_size=15, color=INK_LIGHT, align=PP_ALIGN.CENTER)
add_footer(slide, 6)

# Slide 7: Taxonomy
slide = prs.slides.add_slide(blank_layout)
set_slide_bg(slide, BG)
add_header(slide, "Mismatch Taxonomy")
add_headline(slide, "Six ways a translation can quietly go wrong.")
cards = [
    ("Numeric", "Numeric mismatch", '"5 kg" becomes "50 kg"'),
    ("Unit", "Unit mismatch", "kg vs g, °C vs °F"),
    ("Polarity", "Negation / polarity", 'Missing or added "not," "except," "least"'),
    ("Options", "Answer-option mismatch", "Options don't match in count or content"),
    ("Formula", "Formula / symbol mismatch", "H₂O vs CO₂, F = ma vs wrong symbol"),
    ("Entity", "Named-entity mismatch", "Newton vs Einstein, Lahore vs Karachi"),
    ("Condition", "Missing condition", '"at constant temperature" dropped'),
    ("Semantic", "Semantic drift", "Both versions look fine, but ask different questions"),
]
card_w = Inches(2.85)
card_h = Inches(1.55)
for i, (tag, title, body) in enumerate(cards):
    row = i // 4
    col = i % 4
    x = MARGIN_L + col * (card_w + Inches(0.22))
    y = Inches(2.2) + row * (card_h + Inches(0.25))
    add_card(slide, x, y, card_w, card_h, title, body, tag=tag)
add_footer(slide, 7)

# Slide 8: Architecture
slide = prs.slides.add_slide(blank_layout)
set_slide_bg(slide, BG)
add_header(slide, "Technical Architecture")
add_headline(slide, "What's actually running under the hood.")
# Architecture boxes
boxes = [
    (MARGIN_L, Inches(2.6), Inches(2.2), Inches(1.0), "Vision-Language\nOCR", "RTL Urdu + LTR English", True),
    (Inches(3.3), Inches(2.6), Inches(2.5), Inches(1.0), "Question Segmentation\n& Bilingual Alignment", "", False),
    (Inches(6.3), Inches(2.0), Inches(2.3), Inches(1.0), "Deterministic\nRules Engine", "numbers, units, negation...", True),
    (Inches(6.3), Inches(3.4), Inches(2.3), Inches(1.0), "Cross-Lingual Semantic\nEquivalence Model", "meaning-level drift", True),
    (Inches(9.0), Inches(2.6), Inches(2.3), Inches(1.0), "Confidence-Scored\nEvidence Layer", "", False),
    (Inches(11.6), Inches(2.6), Inches(1.0), Inches(1.0), "Reviewer\nInterface", "", False),
]
for x, y, w, h, title, sub, hl in boxes:
    fill = ACCENT_LIGHT if hl else RGBColor(255, 255, 255)
    stroke = ACCENT if hl else BORDER
    add_rounded_rect(slide, x, y, w, h, fill, stroke)
    add_textbox(slide, x, y + Inches(0.1), w, Inches(0.5), title, font_size=10, bold=True, color=INK, align=PP_ALIGN.CENTER)
    if sub:
        add_textbox(slide, x, y + Inches(0.62), w, Inches(0.3), sub, font_size=8, color=MUTED, align=PP_ALIGN.CENTER)
# Connectors
connectors = [
    (Inches(2.95), Inches(3.1), Inches(3.3), Inches(3.1)),
    (Inches(5.8), Inches(3.1), Inches(6.3), Inches(2.65)),
    (Inches(5.8), Inches(3.1), Inches(6.3), Inches(4.05)),
    (Inches(8.6), Inches(2.65), Inches(9.0), Inches(3.1)),
    (Inches(8.6), Inches(4.05), Inches(9.0), Inches(3.1)),
    (Inches(11.3), Inches(3.1), Inches(11.6), Inches(3.1)),
]
for x1, y1, x2, y2 in connectors:
    line = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, x1, y1, x2, y2)
    line.line.color.rgb = ACCENT
    line.line.width = Pt(2)
add_textbox(slide, MARGIN_L, Inches(4.85), SLIDE_W - MARGIN_L - MARGIN_R, Inches(0.4),
            "Rules and semantic model run independently and are evaluated separately — a deliberate hybrid design.",
            font_size=11, color=MUTED, align=PP_ALIGN.CENTER, italic=True)
add_footer(slide, 8)

# Slide 9: Reviewer experience
slide = prs.slides.add_slide(blank_layout)
set_slide_bg(slide, BG)
add_header(slide, "Reviewer Experience")
add_headline(slide, "The human stays in control.")
# Mockup background
add_rounded_rect(slide, MARGIN_L, Inches(2.2), SLIDE_W - MARGIN_L - MARGIN_R, Inches(3.4), RGBColor(255, 255, 255), BORDER)
# Panels
add_rounded_rect(slide, Inches(1.0), Inches(2.4), Inches(5.5), Inches(1.4), RGBColor(248, 249, 250))
add_textbox(slide, Inches(1.15), Inches(2.5), Inches(5.2), Inches(0.25), "ENGLISH QUESTION", font_size=9, bold=True, color=MUTED)
add_textbox(slide, Inches(1.15), Inches(2.85), Inches(5.2), Inches(0.8), 'A car travels 60 km in 2 hours. What is its average speed?', font_size=13, color=INK)

add_rounded_rect(slide, Inches(6.8), Inches(2.4), Inches(5.5), Inches(1.4), RGBColor(248, 249, 250))
add_textbox(slide, Inches(6.95), Inches(2.5), Inches(5.2), Inches(0.25), "URDU QUESTION", font_size=9, bold=True, color=MUTED)
add_textbox(slide, Inches(6.95), Inches(2.85), Inches(5.2), Inches(0.5), "ایک کار 60 کلومیٹر فی گھنٹہ چلتی ہے۔ اوسط رفتار کتنی ہے؟", font_size=14, color=INK)
add_textbox(slide, Inches(6.95), Inches(3.4), Inches(5.2), Inches(0.3), '("60 km per hour" — unit/time condition differs)', font_size=10, color=MUTED)

# Evidence
add_rounded_rect(slide, Inches(1.0), Inches(4.0), Inches(11.3), Inches(0.7), RGBColor(255, 251, 235), WARN)
add_textbox(slide, Inches(1.2), Inches(4.15), Inches(10.9), Inches(0.4), "!    Unit / condition mismatch detected     English: \"in 2 hours\" · Urdu: \"per hour\" · Confidence: 0.91",
            font_size=12, bold=True, color=INK)
# Buttons
add_rounded_rect(slide, Inches(10.0), Inches(4.9), Inches(1.15), Inches(0.35), RGBColor(255, 255, 255), BORDER)
add_textbox(slide, Inches(10.0), Inches(4.95), Inches(1.15), Inches(0.25), "Reject flag", font_size=10, bold=True, color=INK, align=PP_ALIGN.CENTER)
add_rounded_rect(slide, Inches(11.3), Inches(4.9), Inches(1.0), Inches(0.35), ACCENT)
add_textbox(slide, Inches(11.3), Inches(4.95), Inches(1.0), Inches(0.25), "Accept flag", font_size=10, bold=True, color=RGBColor(255, 255, 255), align=PP_ALIGN.CENTER)

add_textbox(slide, MARGIN_L, Inches(5.8), SLIDE_W - MARGIN_L - MARGIN_R, Inches(0.4),
            "A paper is only cleared after human sign-off. The system never declares a paper wrong on its own.",
            font_size=15, color=INK_LIGHT, align=PP_ALIGN.CENTER)
add_footer(slide, 9)

# Slide 10: Validation
slide = prs.slides.add_slide(blank_layout)
set_slide_bg(slide, BG)
add_header(slide, "Validation")
add_headline(slide, "How we're proving it actually works.")
add_textbox(slide, MARGIN_L, Inches(2.15), Inches(5.8), Inches(1.4),
            "Benchmark of 100–300 real bilingual questions with controlled, seeded defects across every mismatch category.",
            font_size=16, color=INK_LIGHT)
add_bullet_list(slide, MARGIN_L, Inches(3.5), Inches(5.8), Inches(1.5),
                ["Precision, recall, F1 per category",
                 "False positives per 100 questions",
                 "End-to-end latency per paper"], font_size=15)
add_textbox(slide, MARGIN_L, Inches(5.1), Inches(5.8), Inches(0.4),
            "Three-way comparison: rules-only vs. semantic-only vs. hybrid.", font_size=15, color=INK_LIGHT)
# Placeholder box
add_rounded_rect(slide, Inches(7.0), Inches(2.4), Inches(5.7), Inches(2.5), ACCENT_LIGHT, ACCENT)
add_textbox(slide, Inches(7.2), Inches(2.7), Inches(5.3), Inches(0.5), "Live benchmark results — insert after evaluation run",
            font_size=15, bold=True, color=ACCENT, align=PP_ALIGN.CENTER)
add_textbox(slide, Inches(7.2), Inches(3.3), Inches(5.3), Inches(1.0), "Placeholder for precision / recall / F1 numbers",
            font_size=13, color=MUTED, align=PP_ALIGN.CENTER)
add_footer(slide, 10)

# Slide 11: Differentiation
slide = prs.slides.add_slide(blank_layout)
set_slide_bg(slide, BG)
add_header(slide, "Differentiation")
add_headline(slide, "We are not competing with authoring tools.")
add_textbox(slide, MARGIN_L, Inches(2.15), Inches(6.5), Inches(2.4),
            "The obvious question: don't multilingual assessment systems already exist?\n\n"
            "Some do — for authoring and translation. ParityLens is neither. It is an independent post-authoring verification gate built around the specific failure modes of Urdu/English exam pairs.\n\n"
            "As of an August 2026 public-web search, we did not find a close public Pakistan deployment matching this exact end-to-end workflow.",
            font_size=15, color=INK_LIGHT)
add_rounded_rect(slide, Inches(7.2), Inches(2.4), Inches(5.5), Inches(1.6), ACCENT_LIGHT, ACCENT)
add_textbox(slide, Inches(7.4), Inches(2.6), Inches(5.1), Inches(0.35), "Honest framing", font_size=14, bold=True, color=INK)
add_textbox(slide, Inches(7.4), Inches(3.0), Inches(5.1), Inches(0.9),
            "We are not claiming 'world\\'s first.' We are claiming a narrow, defensible gap that no public system we could find is closing.",
            font_size=13, color=INK_LIGHT)
add_footer(slide, 11)

# Slide 12: Use cases
slide = prs.slides.add_slide(blank_layout)
set_slide_bg(slide, BG)
add_header(slide, "Use Cases")
add_headline(slide, "Anywhere a bilingual exam gets printed.")
use_cases = [
    ("B", "Examination boards", "BISE-style boards clearing SSC/HSSC and diploma papers before print."),
    ("T", "Technical / diploma boards", "Bilingual diploma rollouts where numeric and unit drift is most likely."),
    ("S", "Schools & coaching centers", "In-house bilingual test papers with no dedicated proofreading staff."),
    ("P", "Publishers", "Bilingual practice material and past-paper compilations reproduced at scale."),
    ("G", "Beyond Pakistan", "Any multilingual education system facing the same structural risk."),
]
uc_w = Inches(2.3)
uc_h = Inches(2.2)
start_x = Inches(0.5)
for i, (icon, title, body) in enumerate(use_cases):
    x = start_x + i * (uc_w + Inches(0.25))
    add_card(slide, x, Inches(2.3), uc_w, uc_h, title, body)
    # Add icon circle
    circle = slide.shapes.add_shape(MSO_SHAPE.OVAL, x + Inches(0.15), Inches(2.5), Inches(0.4), Inches(0.4))
    circle.fill.solid()
    circle.fill.fore_color.rgb = ACCENT_LIGHT
    circle.line.fill.background()
    add_textbox(slide, x + Inches(0.15), Inches(2.55), Inches(0.4), Inches(0.3), icon, font_size=14, bold=True, color=ACCENT, align=PP_ALIGN.CENTER)
add_footer(slide, 12)

# Slide 13: Responsible AI
slide = prs.slides.add_slide(blank_layout)
set_slide_bg(slide, BG)
add_header(slide, "Responsible AI")
add_headline(slide, "Built to be trusted with confidential exam material.")
rai = [
    ("1", "Human review is final", "A paper is only cleared after a human reviewer signs off."),
    ("2", "No automatic verdicts", "Low-confidence flags are routed to a reviewer, never treated as fact."),
    ("3", "Secure by default", "Encrypted storage, short retention, role-based access. Uploaded papers are not used to train models by default."),
]
rai_w = Inches(3.8)
rai_h = Inches(2.4)
for i, (icon, title, body) in enumerate(rai):
    x = MARGIN_L + i * (rai_w + Inches(0.3))
    add_card(slide, x, Inches(2.3), rai_w, rai_h, title, body)
    circle = slide.shapes.add_shape(MSO_SHAPE.OVAL, x + Inches(0.15), Inches(2.5), Inches(0.4), Inches(0.4))
    circle.fill.solid()
    circle.fill.fore_color.rgb = ACCENT_LIGHT
    circle.line.fill.background()
    add_textbox(slide, x + Inches(0.15), Inches(2.55), Inches(0.4), Inches(0.3), icon, font_size=14, bold=True, color=ACCENT, align=PP_ALIGN.CENTER)
add_footer(slide, 13)

# Slide 14: Scope discipline
slide = prs.slides.add_slide(blank_layout)
set_slide_bg(slide, BG)
add_header(slide, "Scope Discipline")
add_headline(slide, "Deliberately narrow, on purpose.")
add_rounded_rect(slide, MARGIN_L, Inches(2.3), Inches(5.8), Inches(3.5), RGBColor(255, 255, 255), BORDER)
add_textbox(slide, MARGIN_L + Inches(0.2), Inches(2.45), Inches(5.4), Inches(0.35), "Not in scope", font_size=12, bold=True, color=MUTED)
add_bullet_list(slide, MARGIN_L + Inches(0.2), Inches(2.85), Inches(5.4), Inches(2.8),
                ["Student-facing app",
                 "LMS integration",
                 "Exam generator",
                 "Plagiarism detector",
                 "Full exam-board workflow replacement"], font_size=15)
add_rounded_rect(slide, Inches(6.9), Inches(2.3), Inches(5.8), Inches(1.6), ACCENT_LIGHT, ACCENT)
add_textbox(slide, Inches(7.1), Inches(2.45), Inches(5.4), Inches(0.35), "Why this matters", font_size=12, bold=True, color=ACCENT)
add_textbox(slide, Inches(7.1), Inches(2.9), Inches(5.4), Inches(0.8),
            "Staying narrow is what made a working, evidence-backed prototype possible in six days. One job, done well.",
            font_size=14, color=INK_LIGHT)
add_textbox(slide, Inches(6.9), Inches(4.2), Inches(5.8), Inches(1.0),
            "Judges see a lot of broad ideas. A clearly bounded one is easier to believe.",
            font_size=16, color=INK_LIGHT)
add_footer(slide, 14)

# Slide 15: Closing
slide = prs.slides.add_slide(blank_layout)
set_slide_bg(slide, BG)
add_textbox(slide, 0, Inches(2.2), SLIDE_W, Inches(1.5), "ParityLens",
            font_size=72, bold=True, color=INK, align=PP_ALIGN.CENTER)
add_textbox(slide, 0, Inches(3.7), SLIDE_W, Inches(0.9),
            "ParityLens doesn't grade the exam. It makes sure both versions are asking the same one.",
            font_size=24, color=INK_LIGHT, align=PP_ALIGN.CENTER)
add_textbox(slide, 0, Inches(4.9), SLIDE_W, Inches(0.5),
            "Next step: pilot with an examination board, school network, or publisher.",
            font_size=15, color=MUTED, align=PP_ALIGN.CENTER)
add_footer(slide, 15)

prs.save(r"C:\Users\Mahad Enterprises\Documents\Qoder\2026-09-07\289232f0\paritylens_deck.pptx")
print("Saved paritylens_deck.pptx")
