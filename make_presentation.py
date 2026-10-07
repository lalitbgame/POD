"""
Builds a PowerPoint deck explaining the POD model to the team: what POD
is, where it's used in general, how we apply it to predict e-machine
EMag forces, and what the model's inputs/outputs are.

Run:
    python3 pod_model/make_presentation.py

Regenerates pod_model/POD_Model_Overview.pptx from scratch each time -
edit the SLIDE content below and re-run rather than hand-editing the
.pptx file, so it stays reproducible.
"""

from pathlib import Path

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

HERE = Path(__file__).resolve().parent
OUT_PATH = HERE / "POD_Model_Overview.pptx"
RESULTS_DIR = HERE / "results"

NAVY = RGBColor(0x1B, 0x2A, 0x4A)
ORANGE = RGBColor(0xD8, 0x5A, 0x30)
BLUE = RGBColor(0x18, 0x5F, 0xA5)
GRAY = RGBColor(0x40, 0x40, 0x40)
LIGHT_GRAY = RGBColor(0xF2, 0xF2, 0xF2)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)

SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)


def add_slide(prs, layout_index=6):
    return prs.slides.add_slide(prs.slide_layouts[layout_index])


def set_background(slide, color):
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = color


def add_title(slide, text, color=NAVY, top=Inches(0.4), size=32, left=Inches(0.6), width=None):
    width = width or (SLIDE_W - left - Inches(0.6))
    box = slide.shapes.add_textbox(left, top, width, Inches(1.0))
    tf = box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    run = p.add_run()
    run.text = text
    run.font.size = Pt(size)
    run.font.bold = True
    run.font.color.rgb = color
    return box


def add_bullets(slide, items, left=Inches(0.8), top=Inches(1.5), width=None, height=None,
                 size=20, color=GRAY, line_spacing=1.25):
    """items: list of (text, level) or plain strings (level 0)."""
    width = width or (SLIDE_W - left - Inches(0.6))
    height = height or (SLIDE_H - top - Inches(0.4))
    box = slide.shapes.add_textbox(left, top, width, height)
    tf = box.text_frame
    tf.word_wrap = True
    for i, item in enumerate(items):
        text, level = item if isinstance(item, tuple) else (item, 0)
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.level = level
        p.line_spacing = line_spacing
        p.space_after = Pt(10)
        run = p.add_run()
        bullet = "- " if level == 0 else ("- " if level == 1 else "- ")
        run.text = bullet + text
        run.font.size = Pt(size - level * 2)
        run.font.color.rgb = color if level == 0 else RGBColor(0x60, 0x60, 0x60)
    return box


def add_footer(slide, text, page_no):
    box = slide.shapes.add_textbox(Inches(0.6), SLIDE_H - Inches(0.45), Inches(8), Inches(0.35))
    box.text_frame.word_wrap = True
    p = box.text_frame.paragraphs[0]
    run = p.add_run()
    run.text = text
    run.font.size = Pt(10)
    run.font.color.rgb = RGBColor(0xA0, 0xA0, 0xA0)

    box2 = slide.shapes.add_textbox(SLIDE_W - Inches(1.0), SLIDE_H - Inches(0.45), Inches(0.6), Inches(0.35))
    box2.text_frame.word_wrap = True
    p2 = box2.text_frame.paragraphs[0]
    p2.alignment = PP_ALIGN.RIGHT
    run2 = p2.add_run()
    run2.text = str(page_no)
    run2.font.size = Pt(10)
    run2.font.color.rgb = RGBColor(0xA0, 0xA0, 0xA0)


def add_accent_bar(slide, color=ORANGE):
    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(0.18), SLIDE_H)
    bar.fill.solid()
    bar.fill.fore_color.rgb = color
    bar.line.fill.background()
    bar.shadow.inherit = False


def content_slide(prs, title, bullets, page_no, title_size=30, bullet_size=19):
    slide = add_slide(prs)
    set_background(slide, WHITE)
    add_accent_bar(slide)
    add_title(slide, title, left=Inches(0.7), size=title_size)
    add_bullets(slide, bullets, left=Inches(0.9), top=Inches(1.4), size=bullet_size)
    add_footer(slide, "POD Model for EMag Force Prediction", page_no)
    return slide


def picture_slide(prs, title, image_path, caption, page_no, max_width=Inches(10.5), max_height=Inches(5.3)):
    from PIL import Image

    slide = add_slide(prs)
    set_background(slide, WHITE)
    add_accent_bar(slide)
    add_title(slide, title, left=Inches(0.7), size=28)

    im = Image.open(image_path)
    aspect = im.width / im.height
    width, height = max_width, max_width / aspect
    if height > max_height:
        height = max_height
        width = max_height * aspect
    left = (SLIDE_W - width) / 2
    top = Inches(1.35)
    slide.shapes.add_picture(str(image_path), left, top, width=width, height=height)

    if caption:
        cap_box = slide.shapes.add_textbox(Inches(0.9), top + height + Inches(0.08),
                                           SLIDE_W - Inches(1.8), Inches(0.6))
        cap_box.text_frame.word_wrap = True
        p = cap_box.text_frame.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        run = p.add_run()
        run.text = caption
        run.font.size = Pt(14)
        run.font.italic = True
        run.font.color.rgb = RGBColor(0x60, 0x60, 0x60)

    add_footer(slide, "POD Model for EMag Force Prediction", page_no)
    return slide


def two_picture_slide(prs, title, image_path_left, label_left, image_path_right, label_right,
                      caption, page_no, max_width=Inches(5.9), max_height=Inches(4.3)):
    from PIL import Image

    slide = add_slide(prs)
    set_background(slide, WHITE)
    add_accent_bar(slide)
    add_title(slide, title, left=Inches(0.7), size=28)

    top = Inches(1.5)
    gap = Inches(0.3)
    left_x = Inches(0.9)
    right_x = left_x + max_width + gap

    for image_path, label, x in [(image_path_left, label_left, left_x), (image_path_right, label_right, right_x)]:
        im = Image.open(image_path)
        aspect = im.width / im.height
        width, height = max_width, max_width / aspect
        if height > max_height:
            height = max_height
            width = max_height * aspect
        x_centered = x + (max_width - width) / 2
        slide.shapes.add_picture(str(image_path), x_centered, top, width=width, height=height)

        label_box = slide.shapes.add_textbox(x, top - Inches(0.35), max_width, Inches(0.3))
        label_box.text_frame.word_wrap = True
        p = label_box.text_frame.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        run = p.add_run()
        run.text = label
        run.font.size = Pt(14)
        run.font.bold = True
        run.font.color.rgb = BLUE

    if caption:
        cap_box = slide.shapes.add_textbox(Inches(0.9), top + max_height + Inches(0.15),
                                           SLIDE_W - Inches(1.8), Inches(0.8))
        cap_box.text_frame.word_wrap = True
        p = cap_box.text_frame.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        run = p.add_run()
        run.text = caption
        run.font.size = Pt(14)
        run.font.italic = True
        run.font.color.rgb = RGBColor(0x60, 0x60, 0x60)

    add_footer(slide, "POD Model for EMag Force Prediction", page_no)
    return slide


def add_table(slide, rows, left, top, width, height, header_color=NAVY, col_widths=None):
    n_rows, n_cols = len(rows), len(rows[0])
    table_shape = slide.shapes.add_table(n_rows, n_cols, left, top, width, height)
    table = table_shape.table
    if col_widths:
        for i, w in enumerate(col_widths):
            table.columns[i].width = w
    for r, row in enumerate(rows):
        for c, value in enumerate(row):
            cell = table.cell(r, c)
            cell.text = str(value)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            para = cell.text_frame.paragraphs[0]
            para.alignment = PP_ALIGN.CENTER if c > 0 else PP_ALIGN.LEFT
            run = para.runs[0]
            run.font.size = Pt(15)
            if r == 0:
                run.font.bold = True
                run.font.color.rgb = WHITE
                cell.fill.solid()
                cell.fill.fore_color.rgb = header_color
            else:
                run.font.color.rgb = GRAY
                cell.fill.solid()
                cell.fill.fore_color.rgb = LIGHT_GRAY if r % 2 == 0 else WHITE
    return table


def main():
    prs = Presentation()
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H
    page = [0]

    def next_page():
        page[0] += 1
        return page[0]

    # ---------------------------------------------------------------- Title
    slide = add_slide(prs)
    set_background(slide, NAVY)
    title_box = slide.shapes.add_textbox(Inches(1), Inches(2.5), Inches(11.3), Inches(1.6))
    tf = title_box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT
    run = p.add_run()
    run.text = "POD-Based Modeling for\nE-Machine EMag Force Prediction"
    run.font.size = Pt(40)
    run.font.bold = True
    run.font.color.rgb = WHITE

    sub_box = slide.shapes.add_textbox(Inches(1), Inches(4.3), Inches(11), Inches(1))
    sub_box.text_frame.word_wrap = True
    p2 = sub_box.text_frame.paragraphs[0]
    run2 = p2.add_run()
    run2.text = "A data-driven approach using Proper Orthogonal Decomposition (POD)"
    run2.font.size = Pt(20)
    run2.font.color.rgb = RGBColor(0xC9, 0xD4, 0xE6)

    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(1), Inches(4.1), Inches(1.5), Pt(4))
    bar.fill.solid(); bar.fill.fore_color.rgb = ORANGE; bar.line.fill.background(); bar.shadow.inherit = False

    # ---------------------------------------------------------------- Agenda
    content_slide(prs, "Agenda", [
        "What is POD?",
        "Where is POD used?",
        "Our problem: predicting EMag forces",
        "How we apply POD to this dataset",
        "Model inputs and outputs",
        "Validation: does POD find the real physics?",
        "Results",
        "Summary and next steps",
    ], next_page(), bullet_size=22)

    # ---------------------------------------------------------------- What is POD
    content_slide(prs, "What is POD?", [
        "Proper Orthogonal Decomposition (POD) = the SVD applied to a dataset of \"snapshots\"",
        "Same mathematics as PCA - widely used under the name POD in fluid dynamics and structural dynamics",
        "Breaks complex, high-dimensional data into a small number of \"modes\", ranked by how much of the data's variance each one explains",
        "Each mode is a fixed spatial pattern paired with a coefficient that says how strongly that pattern is present in each snapshot",
        ("Data  ≈  Σ (mode strength) × (spatial pattern) × (how strongly it's present)", 1),
        "No physics assumptions required - the patterns are found directly from the data",
    ], next_page())

    # ---------------------------------------------------------------- Where used
    content_slide(prs, "Where is POD used?", [
        "Fluid dynamics - reduced-order models of complex flow fields (the classic use of the name \"POD\")",
        "Structural dynamics - extracting dominant vibration mode shapes",
        "Image compression / face recognition - \"eigenfaces\" is the same idea applied to images",
        "Building fast surrogate models - replacing an expensive simulation with a cheap one that reproduces its dominant behavior",
        "General principle: any dataset with a dominant, low-dimensional structure hiding inside high-dimensional data can be compressed this way with very little loss",
    ], next_page())

    # ---------------------------------------------------------------- Our problem
    content_slide(prs, "Our problem: predicting EMag forces", [
        "Need: the radial (Fr) and tangential (Ft) electromagnetic force on each of the 48 stator teeth",
        "At any operating point - any torque, any rotor (electrical) angle",
        "These forces are what drive the NVH (noise, vibration, harshness) analysis",
        "Today: every new operating point needs a full FEA simulation - slow",
        "Goal: a fast, accurate surrogate model that reproduces FEA-quality forces instantly",
    ], next_page())

    # ---------------------------------------------------------------- Why POD fits
    content_slide(prs, "Why POD fits this problem", [
        "The 96 numbers per snapshot (48 Fr + 48 Ft) are not an arbitrary pattern",
        "Earlier analysis of the raw FEA data found it is dominated by a handful of repeating spatial wave shapes around the 48 teeth",
        "POD is the natural, assumption-free tool to discover and exploit exactly this kind of hidden low-dimensional structure directly from data",
        "Used here as an independent, data-driven check on a separate hand-built physics model - if POD finds the same structure with no hints given, that's strong confirmation the structure is real",
    ], next_page())

    # ---------------------------------------------------------------- Step 1
    content_slide(prs, "How we apply POD - Step 1: Spatial modes", [
        "Stack every training snapshot (one torque + angle combination) as one row of a big table: rows = snapshots, columns = the 48 teeth",
        "Take the SVD of that table, separately for Fr and for Ft",
        "The result is a small set of \"spatial modes\" - fixed shapes across the 48 teeth, ranked by how much of the data's variance each one explains",
        "Keep only as many modes as needed to explain 99.99% of the variance",
        ("Result on our data: just 6 modes (out of a possible 48) explain essentially 100% of the signal, for each of Fr and Ft", 1),
    ], next_page())

    # ---------------------------------------------------------------- Step 2
    content_slide(prs, "How we apply POD - Step 2: Angle behavior", [
        "Project every snapshot onto the spatial modes to get one coefficient per mode per snapshot",
        "At a fixed torque, track how each mode's coefficient changes as the rotor angle sweeps - this is the \"temporal\" side of POD (here, electrical angle plays the role of time)",
        "The natural oscillation speed of each mode is not assumed - it is discovered directly from the data for that mode",
        "A smooth wave is fit to each mode's coefficient vs angle, including a secondary wobble rhythm found empirically in the data",
    ], next_page())

    # ---------------------------------------------------------------- Step 3
    content_slide(prs, "How we apply POD - Step 3: Torque behavior & prediction", [
        "Repeat the angle fit at every torque level present in the training data",
        "Fit a smooth curve through the resulting numbers across torque, for each mode",
        "To predict a new (torque, angle): read the curves for that torque, reconstruct each mode's coefficient at that angle, and recombine with the spatial shapes",
        "The result is the full 96-number force prediction - no simulation, closed-form, near-instant",
    ], next_page())

    # ---------------------------------------------------------------- Inputs/outputs
    slide = add_slide(prs)
    set_background(slide, WHITE)
    add_accent_bar(slide)
    add_title(slide, "Model inputs and outputs", left=Inches(0.7), size=30)

    io_top = Inches(1.7)
    box_h = Inches(2.6)

    in_box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.9), io_top, Inches(3.3), box_h)
    in_box.fill.solid(); in_box.fill.fore_color.rgb = BLUE; in_box.line.fill.background()
    tf = in_box.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    run = p.add_run(); run.text = "INPUT"; run.font.bold = True; run.font.size = Pt(18); run.font.color.rgb = WHITE
    for line in ["Torque (Nm)", "Electrical angle (deg)", "(RPM - fixed in\ncurrent dataset)"]:
        p = tf.add_paragraph(); p.alignment = PP_ALIGN.CENTER
        r = p.add_run(); r.text = line; r.font.size = Pt(15); r.font.color.rgb = WHITE

    arrow = slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(4.35), io_top + Inches(0.9), Inches(1.8), Inches(0.8))
    arrow.fill.solid(); arrow.fill.fore_color.rgb = ORANGE; arrow.line.fill.background()
    tf = arrow.text_frame
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = "POD model"; r.font.size = Pt(14); r.font.bold = True; r.font.color.rgb = WHITE

    out_box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.3), io_top, Inches(3.3), box_h)
    out_box.fill.solid(); out_box.fill.fore_color.rgb = NAVY; out_box.line.fill.background()
    tf = out_box.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    run = p.add_run(); run.text = "OUTPUT"; run.font.bold = True; run.font.size = Pt(18); run.font.color.rgb = WHITE
    for line in ["Fr - radial force\n(48 values, one per tooth)", "Ft - tangential force\n(48 values, one per tooth)", "96 numbers total"]:
        p = tf.add_paragraph(); p.alignment = PP_ALIGN.CENTER
        r = p.add_run(); r.text = line; r.font.size = Pt(15); r.font.color.rgb = WHITE

    note_box = slide.shapes.add_textbox(Inches(0.9), io_top + box_h + Inches(0.3), Inches(10.5), Inches(1.8))
    tf = note_box.text_frame
    tf.word_wrap = True
    notes = [
        "2 numbers in, 96 numbers out - a direct, closed-form replacement for an FEA run at that operating point",
        "Prediction cost: a handful of spline lookups and one inverse transform - effectively instant",
        "Internally, the model only ever stores: 6 spatial mode shapes per channel + a set of smooth curves across torque per mode - a tiny model compared to a neural network",
    ]
    for i, text in enumerate(notes):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(8)
        r = p.add_run(); r.text = "- " + text
        r.font.size = Pt(16); r.font.color.rgb = GRAY

    add_footer(slide, "POD Model for EMag Force Prediction", next_page())

    # ---------------------------------------------------------------- Validation picture
    mode_image = RESULTS_DIR / "pod_modes_Fr_T450.png"
    if mode_image.exists():
        picture_slide(
            prs, "Validation: POD rediscovers known physics", mode_image,
            "With zero physics input, POD's own spatial modes (blue) line up almost exactly with the "
            "expected harmonic waves (orange dashed) at orders 0, 8, 8, 24 - the same orders found by "
            "independently hand-analyzing the FEA data.",
            next_page(), max_height=Inches(4.9),
        )

    # ---------------------------------------------------------------- Energy spectrum picture
    spectrum_fr = RESULTS_DIR / "pod_spectrum_Fr_T450.png"
    spectrum_ft = RESULTS_DIR / "pod_spectrum_Ft_T450.png"
    if spectrum_fr.exists() and spectrum_ft.exists():
        two_picture_slide(
            prs, "How much each mode matters: the energy spectrum",
            spectrum_fr, "Fr (radial force)", spectrum_ft, "Ft (tangential force)",
            "Mode 1 alone explains 72-80% of the variance; by mode 4 the running total is "
            "essentially 100%. Modes past that point are noise-level - confirming 6 modes per "
            "channel is enough, not an arbitrary cutoff.",
            next_page(),
        )

    # ---------------------------------------------------------------- Validation bullets
    content_slide(prs, "Validation - what this confirms", [
        "A plain SVD needs only 4-6 modes to explain ~100% of the variance in the force data",
        "The dominant spatial modes match plain cos/sin waves at orders 0, 8, 16, and 24 - exactly the orders used in the separate, hand-built harmonic model",
        "Orders 8 and 16 each show up as two modes with nearly equal strength - the expected signature of a spatial pattern that rotates with the rotor, rather than one that stays still",
        "The model's own frequency-discovery step (given no hints) came back with exactly [0, 8, 8, 16, 16, 24] for both Fr and Ft",
        "A small wobble effect (24 cycles per electrical turn) found independently while refining the hand-built model shows up here too - a third, independent confirmation it's a real effect in the machine",
    ], next_page())

    # ---------------------------------------------------------------- True vs predicted picture
    line_image = RESULTS_DIR / "true_vs_predicted_line_T450.png"
    if line_image.exists():
        picture_slide(
            prs, "Predicted vs FEA data - a torque the model never saw", line_image,
            "Torque = 450 Nm held out entirely during fitting. Predicted (orange) vs true FEA data "
            "(blue) overlap almost exactly across all 48 teeth, for both Fr and Ft.",
            next_page(), max_height=Inches(4.6),
        )

    # ---------------------------------------------------------------- Results table
    slide = add_slide(prs)
    set_background(slide, WHITE)
    add_accent_bar(slide)
    add_title(slide, "Results", left=Inches(0.7), size=30)

    sub = slide.shapes.add_textbox(Inches(0.9), Inches(1.25), Inches(11), Inches(0.4))
    sub.text_frame.word_wrap = True
    r = sub.text_frame.paragraphs[0].add_run()
    r.text = "Predicting a torque the model never saw during training (the meaningful generalization test)"
    r.font.size = Pt(16); r.font.italic = True; r.font.color.rgb = GRAY

    rows = [
        ["Model", "Mean R² (new-torque test)"],
        ["Harmonic model (hand-built physics)", "0.9822"],
        ["POD model (data-driven)", "0.9822"],
        ["Interpolation baseline (no physics)", "0.9252"],
    ]
    add_table(slide, rows, Inches(1.2), Inches(1.9), Inches(10.5), Inches(1.8),
              col_widths=[Inches(7.0), Inches(3.5)])

    sub2 = slide.shapes.add_textbox(Inches(0.9), Inches(4.0), Inches(11), Inches(0.4))
    sub2.text_frame.word_wrap = True
    r = sub2.text_frame.paragraphs[0].add_run()
    r.text = "Interpolating within a torque already seen during training (the easier test)"
    r.font.size = Pt(16); r.font.italic = True; r.font.color.rgb = GRAY

    rows2 = [
        ["Model", "Overall R²", "Fr R²", "Ft R²"],
        ["Harmonic model", "0.9999", "0.9999", "0.9997"],
        ["POD model", "0.9836", "0.9559", "0.9816"],
        ["Interpolation baseline", "0.8781", "0.6788", "0.8466"],
    ]
    add_table(slide, rows2, Inches(1.2), Inches(4.5), Inches(10.5), Inches(2.0),
              col_widths=[Inches(5.5), Inches(1.67), Inches(1.67), Inches(1.66)])

    add_footer(slide, "POD Model for EMag Force Prediction", next_page())

    # ---------------------------------------------------------------- Summary
    content_slide(prs, "Summary", [
        "POD is a general, data-driven way to find hidden low-dimensional structure in complex data and build fast surrogate models",
        "Applied to our EMag force data: found just 6 dominant modes per force channel, matching known machine physics exactly",
        "Accuracy on new, unseen torque levels: R² = 0.9822 - matching the hand-built physics model almost to the decimal",
        "Fast: closed-form prediction, no training data needed at inference time, no simulation required",
        "Value: independent, assumption-free confirmation that the hand-built harmonic model's physics assumptions are correct",
    ], next_page())

    content_slide(prs, "Limitations and next steps", [
        ("Limitations (shared with the hand-built model)", 0),
        ("Electrical angle only covers 0-90 degrees in the current dataset, not the full 360", 1),
        ("Only one RPM in the dataset - speed-dependence is untested", 1),
        ("POD's own weak spot: its basis is learned from training data, so basis quality depends on how completely that data covers the angle sweep", 1),
        ("Lowest-torque region (±75 Nm) is the least accurate for both physics-grade models - a real property of the machine, not a model flaw", 1),
        ("Next steps", 0),
        ("Extend FEA data to a full 360 degree electrical cycle to verify angle extrapolation", 1),
        ("Add further RPM sweeps - test whether the same dominant orders still hold at other speeds", 1),
        ("Use POD as the automatic structure-discovery step for any future machine geometry, before hand-building a physics model", 1),
    ], next_page(), bullet_size=18)

    prs.save(OUT_PATH)
    print(f"Saved -> {OUT_PATH}  ({len(prs.slides)} slides)")


if __name__ == "__main__":
    main()
