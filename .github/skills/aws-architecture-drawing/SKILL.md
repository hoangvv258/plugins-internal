---
name: aws-architecture-drawing
description: >-
  This skill should be used when the user asks to "draw AWS architecture",
  "create AWS diagram", "AWS architecture diagram", "design AWS infrastructure",
  "visualize AWS setup", "generate AWS cloud diagram", "AWS network diagram",
  "create VPC diagram", "draw serverless architecture", "AWS 3-tier diagram",
  or any request involving creating professional AWS architecture visualizations.
  Generates PowerPoint (.pptx) diagrams using official AWS Architecture Icons
  with proper groups, connectors, and labeling per AWS Architecture Center guidelines.
version: 1.0.0
---

# AWS Architecture Drawing Skill

Generate professional AWS architecture diagrams as PowerPoint (.pptx) files using official AWS Architecture Icons (Release 2026.01.30) following AWS Architecture Center design guidelines.

## Prerequisites

Install python-pptx before generating diagrams:
```bash
pip install python-pptx
```

## Icon Asset Location

All icons are bundled in the `assets/` directory of this skill:
- **Service icons (48px)**: `assets/service-icons/Arch_{Service}_48.png` — 300 icons
- **Resource icons (48px)**: `assets/resource-icons/Res_{Service}_{Resource}_48.png` — 421 icons
- **General icons (48px)**: `assets/general-icons/Res_General_{Name}_48.png` — 49 icons (Users, Internet, Server, Client, Database, etc.)
- **Group icons (32px)**: `assets/group-icons/{Group}_32.png` — 13 icons
- **Category icons (48px)**: `assets/category-icons/Arch-Category_{Category}_48.png` — 26 icons

Use `scripts/icon_lookup.py` to find icons by name, or consult `references/icon-catalog.md` for the full catalog.

## Mandatory 8-Step Construction Workflow

Every architecture diagram MUST follow these steps in exact order. Skipping steps or reordering will produce incorrect diagrams.

### Step 1: Create Presentation & Blank Slide

Initialize a widescreen presentation (13.33 × 7.50 inches) with a blank slide:

```python
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

prs = Presentation()
prs.slide_width = Inches(13.33)
prs.slide_height = Inches(7.50)
slide_layout = prs.slide_layouts[6]  # Blank
slide = prs.slides.add_slide(slide_layout)
```

### Step 2: Add Diagram Title

Add a title text box at the top of the slide:

```python
title_box = slide.shapes.add_textbox(Inches(0.26), Inches(0.40), Inches(12.81), Inches(0.70))
tf = title_box.text_frame
tf.word_wrap = True
p = tf.paragraphs[0]
p.text = "Architecture: Your Title Here"
run = p.runs[0]
run.font.name = "Arial"
run.font.size = Pt(20)
run.font.bold = True
```

### Step 3: Add Groups (Outermost → Innermost)

Groups are container rectangles with a group icon in the top-left corner. **Z-order matters**: add outermost groups first (AWS Cloud), then inner groups (VPC, Subnet, etc.).

Each group = Rectangle (transparent fill, colored border) + Group Icon (0.42×0.42in, top-left).

Use the helper script `scripts/generate_pptx.py` (AWSArchitectureDiagram class) or construct manually:

```python
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.dml import MSO_LINE_DASH_STYLE

# Group border specifications (from references/group-colors.md)
GROUP_SPECS = {
    "AWS Cloud":          {"color": RGBColor(0x23, 0x27, 0x2A), "dash": None,                              "icon": "AWS-Cloud_32.png"},
    "VPC":                {"color": RGBColor(0x8C, 0x4F, 0xFF), "dash": None,                              "icon": "Virtual-private-cloud-VPC_32.png"},
    "Region":             {"color": RGBColor(0x00, 0xA4, 0xA6), "dash": MSO_LINE_DASH_STYLE.SQUARE_DOT,    "icon": "Region_32.png"},
    "Availability Zone":  {"color": RGBColor(0x00, 0xA4, 0xA6), "dash": MSO_LINE_DASH_STYLE.DASH,          "icon": None},
    "Public Subnet":      {"color": RGBColor(0x7A, 0xA1, 0x16), "dash": None,                              "icon": "Public-subnet_32.png"},
    "Private Subnet":     {"color": RGBColor(0x00, 0xA4, 0xA6), "dash": None,                              "icon": "Private-subnet_32.png"},
    "Security Group":     {"color": RGBColor(0xDD, 0x34, 0x4C), "dash": None,                              "icon": None},
    "Auto Scaling":       {"color": RGBColor(0xED, 0x71, 0x00), "dash": MSO_LINE_DASH_STYLE.DASH,          "icon": "Auto-Scaling-group_32.png"},
    "AWS Account":        {"color": RGBColor(0xE7, 0x15, 0x7B), "dash": None,                              "icon": "AWS-Account_32.png"},
}

def add_group(slide, group_type, left, top, width, height, label, icon_base_path):
    spec = GROUP_SPECS[group_type]
    # Rectangle container
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
    shape.fill.background()
    shape.line.width = Pt(1.25)
    shape.line.color.rgb = spec["color"]
    if spec["dash"]:
        shape.line.dash_style = spec["dash"]
    # Label text
    tf = shape.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = label
    run = p.runs[0]
    run.font.name = "Arial"
    run.font.size = Pt(12)
    # Group icon (top-left corner, 0.42in)
    if spec["icon"]:
        import os
        icon_path = os.path.join(icon_base_path, spec["icon"])
        slide.shapes.add_picture(icon_path, left, top, Inches(0.42), Inches(0.42))
    return shape
```

**Nesting rule**: Inner groups must have ≥ 0.05in buffer on all sides from parent group.

**IMPORTANT: Icon placement clearance**: Group icons occupy 0.42×0.42" at the top-left corner. When placing service/resource icons inside a group, offset at least **0.55"** from the group's left edge and **0.55"** from its top edge to avoid overlapping the group corner icon and label. Use `safe_icon_position()` helper or calculate manually:
- `safe_x = group_left + 0.55 + (col * cell_width)`
- `safe_y = group_top + 0.55 + (row * 1.4)` (1.4" = icon + label + spacing)

### Step 4: Add Service Icons (0.83 × 0.83 in)

Service icons represent AWS services. Each = PNG image + centered text label below.

```python
def add_service_icon(slide, icon_path, label_text, center_x, top_y):
    icon_w = Inches(0.83)
    icon_h = Inches(0.83)
    label_w = Inches(1.10)  # slightly wider than icon for readability
    label_h = Inches(0.35)
    # Icon
    pic_left = center_x - icon_w // 2
    slide.shapes.add_picture(icon_path, pic_left, top_y, icon_w, icon_h)
    # Label below icon
    label_left = center_x - label_w // 2
    label_top = top_y + icon_h
    txBox = slide.shapes.add_textbox(label_left, label_top, label_w, label_h)
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = label_text
    p.alignment = PP_ALIGN.CENTER
    run = p.runs[0]
    run.font.name = "Arial"
    run.font.size = Pt(8)  # smaller than icon, readable
```

To find the correct icon file, use `scripts/icon_lookup.py` or consult `references/icon-catalog.md`.

### Step 5: Add Resource Icons (0.50 × 0.50 in)

Resource icons are smaller and represent sub-components of a service:

```python
def add_resource_icon(slide, icon_path, label_text, center_x, top_y):
    icon_w = Inches(0.50)
    icon_h = Inches(0.50)
    label_w = Inches(0.80)  # slightly wider than icon for readability
    label_h = Inches(0.25)
    pic_left = center_x - icon_w // 2
    slide.shapes.add_picture(icon_path, pic_left, top_y, icon_w, icon_h)
    label_left = center_x - label_w // 2
    label_top = top_y + icon_h
    txBox = slide.shapes.add_textbox(label_left, label_top, label_w, label_h)
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = label_text
    p.alignment = PP_ALIGN.CENTER
    run = p.runs[0]
    run.font.name = "Arial"
    run.font.size = Pt(7)  # smaller than icon, readable
```

### Step 6: Add Arrows & Connectors

Add connections **after** all icons are placed. The `connect()` method automatically anchors arrows to icon edges and routes orthogonally.

**ALL arrows are SOLID** — per AWS Architecture Icons PPTX deck (Slide 16), dashed arrows are never used.

**Preferred: Use `connect()` for icon-to-icon arrows** (uses elbow connectors for clean right-angle routing):
```python
# Icons are registered by name when added
diagram.add_service_icon(path, 'Lambda', 5.0, 3.0, name='Lambda')
diagram.add_service_icon(path, 'DynamoDB', 8.0, 3.0, name='DDB')

# connect() uses elbow connectors and routes with right angles
diagram.connect('Lambda', 'DDB')                                           # auto direction
diagram.connect('Lambda', 'DDB', from_dir='right', to_dir='left')         # explicit
diagram.connect('A', 'B', bidirectional=True)                              # bidirectional
```

**For manual positioning** (when icons aren't registered or for non-icon endpoints):
```python
diagram.add_elbow_arrow(start_x, start_y, end_x, end_y)   # elbow connector (preferred)
diagram.add_arrow(start_x, start_y, end_x, end_y)          # straight arrow
diagram.add_line(start_x, start_y, end_x, end_y)           # no arrowhead
```

**Arrow rules (from PPTX deck Slide 16):**
- Use **straight lines and right angles** to connect objects wherever possible
- In the rare instance where right angles are not possible, you may use a diagonal
- 1.25pt width, "Open Arrow" Size 4 (w=lg, len=lg)
- **ALL arrows are SOLID** — no dashed, dotted, or other line styles
- Arrows must start/end at icon edges, not floating in space
- Arrows must NOT cross through other icons or group borders
- Each pair of icons may have only ONE arrow (duplicates are auto-skipped)
- DON'T use anything besides preset or default arrows

**Scale**: When diagram has many icons (>10), use `scale=0.85` or lower to prevent overflow:
```python
diagram = AWSArchitectureDiagram('Title', icon_base_path=ASSETS, scale=0.85)
```

### Step 7: Add Annotations (Optional)

- **Numbered steps**: Oval shapes (0.36×0.36in) with step numbers
- **CIDR codes**: Text boxes near VPC/subnet boundaries
- **Standby replicas**: When AZ 2 mirrors AZ 1, add text "↔ Standby Replica in AZ 2" instead of duplicating all icons
- **Users group**: Always place a "Users / Internet" group OUTSIDE the AWS Cloud group (to the left)
- **Short forms**: Allowed after full name is mentioned once (e.g., EC2, S3, Lambda)

### Step 8: Save Output

```python
prs.save("output_architecture.pptx")
```

## Design Rules Summary (from AWS Architecture Icons PPTX Deck)

- **Font**: Arial throughout, 12pt Regular for all labels (service, resource, group), 20pt Bold for titles. Labels slightly wider than icon for readability but must not overlap adjacent icons
- **Icons**: Never crop, flip, rotate, or change icon shapes. Use icons at their predefined size, color, and format
- **Labels**: Max 2 lines, centered below icon, width = 1.30" for service icons, 1.00" for resource icons. Labels slightly wider than icon for readability. "AWS" or "Amazon" always with service name. Break after second word if needed
- **Arrows (Slide 16)**: 
  - ALL arrows are **SOLID** — no dashed, dotted, or other line styles ever
  - Use **elbow connectors** (right-angle bends) for all non-aligned connections
  - Use straight arrows only when source and target are on the same axis
  - Diagonal lines ONLY when right angles are not possible
  - 1.25pt width, "Open Arrow" Size 4 (w=lg, len=lg)
  - Route arrows AROUND icons and groups — never through them
  - Each icon pair has at most ONE arrow (duplicates auto-skipped)
  - DON'T use anything besides preset or default arrows
- **Arrow Dedup**: Each pair of icons may have only ONE arrow. Duplicate `connect()` calls are silently skipped
- **Groups (Slide 14)**: Transparent fill, colored border 1.25pt, icon top-left 0.42×0.42in. Inner groups need ≥ 0.05" buffer from parent
- **Group Labels**: Black (#000000) **12pt Regular** text as SEPARATE textbox inside border (offset 0.06" from top). NOT on the border line
- **Clearance**: Service icons must be ≥ 0.55" from group top-left corner (to avoid overlapping group icon)
- **Icon Boundaries**: ALL icons must be FULLY INSIDE their containing group — never straddling or crossing group borders
- **Alignment**: 
  - Icons in the same logical row must share the same Y coordinate
  - Icons in the same logical column must share the same X coordinate
  - Use constants for shared coordinates (e.g., `PUB_Y = 3.0`, `PRIV_Y = 5.0`)
  - Space icons evenly within each group
- **Text Overlap Prevention**: 
  - Group labels must not overlap with group icons or border lines
  - Icon labels must not overlap with other icons, labels, or group borders
  - Ensure label textbox width doesn't exceed available space
- **General Icons (Slides 28-29)**: Use for non-service elements (Users, Internet, Server, Client, Database, etc.). Located at `assets/general-icons/`
- **Users**: Always place a "Users / Internet" group OUTSIDE and to the LEFT of the AWS Cloud group. Use general icons (User, Users, Mobile-client) for user representation
- **Duplicate AZs**: If AZ 2 mirrors AZ 1, use text annotation "↔ Standby Replica in AZ 2" instead
- **Scale**: Use `scale=0.85` for diagrams with >10 icons, `scale=0.7` for >15 icons
- **Numbered Callouts (Slide 18)**: Black with bold white type, 0.36" (large) or 0.30" (small). Order linearly (left→right, top→bottom, or clockwise)

For comprehensive rules, consult `references/aws-design-rules.md`.

## Agent-Driven Workflow (Recommended)

This skill is designed to work with **3 specialized agents** that ensure professional-quality output:

### Workflow: Plan → Build → Review → Fix → Approve

```
User request
  ↓
@aws-architecture-planner   ← Phase 1: Plan layout, routes, crossing analysis
  ↓ (produces YAML layout plan)
@aws-architecture-builder   ← Phase 2: Generate Python script → PPTX
  ↓ (produces PPTX file)
@aws-architecture-reviewer  ← Phase 3: Validate ALL design rules
  ↓
  ├─ PASS → ✅ Deliver to user
  └─ FAIL → Send issues back to @aws-architecture-builder → regenerate → re-review
             (loop until all checks pass, max 5 iterations)
```

### Agent Descriptions

| Agent | Role | Input | Output |
|-------|------|-------|--------|
| `@aws-architecture-planner` | Plans optimal layout with coordinates, groups, icon positions, and arrow routing with crossing avoidance | User's architecture description | YAML layout plan with crossing analysis |
| `@aws-architecture-builder` | Generates Python code using `generate_pptx.py` and produces PPTX file | Planner's YAML layout plan | PPTX file + crossing check results |
| `@aws-architecture-reviewer` | Validates PPTX against ALL AWS design rules (arrows, icons, groups, text, layout) | PPTX file path + Builder's code | Pass/Fail report with specific fix instructions |

### How to Invoke

When a user asks to create an AWS architecture diagram:

1. **Always start with the Planner**: `@aws-architecture-planner` analyzes requirements, selects services, plans exact coordinates, and verifies arrow routing won't cross any icons
2. **Pass plan to Builder**: `@aws-architecture-builder` translates the plan into executable Python code and generates the PPTX
3. **Pass PPTX to Reviewer**: `@aws-architecture-reviewer` runs comprehensive validation (6 check categories, 16 sub-checks) and reports issues
4. **Fix loop**: If Reviewer finds issues, send the report back to Builder to fix and regenerate, then re-review
5. **Deliver**: When Reviewer approves (all checks pass), deliver the PPTX to the user

### Critical Review Points (Most Common Errors)

The Reviewer specifically catches these frequently-occurring issues:
- **Arrows crossing through icons** (CHECK 2b) — most common defect
- **Arrows overlapping label text** (CHECK 2c) — labels sit below icons
- **Dashed arrows used** (CHECK 2a) — AWS spec requires ALL solid
- **Icons straddling group borders** (CHECK 3a) — must be fully inside
- **Managed services inside VPC** (CHECK 3b) — S3, DynamoDB, Lambda go outside VPC
- **Inconsistent alignment** (CHECK 3c) — same-row icons must share Y coordinate
- **Arrow start points unclear** (CHECK 2d) — must start/end at icon edges

## Additional Resources

### Reference Files
- **`references/aws-design-rules.md`** — Complete design rules from AWS Architecture Icons PPTX deck
- **`references/icon-catalog.md`** — Full catalog of 300 service + 421 resource + 49 general + 13 group icons with file paths
- **`references/group-colors.md`** — All group types with border colors, dash styles, and nesting rules
- **`references/diagram-patterns.md`** — Common architecture patterns (3-tier, serverless, VPC, microservices)

### Agents
- **`.github/agents/aws-architecture-planner.md`** — Plans architecture layout with crossing analysis
- **`.github/agents/aws-architecture-builder.md`** — Generates PPTX from layout plan
- **`.github/agents/aws-architecture-reviewer.md`** — Validates and approves PPTX output

### Scripts
- **`scripts/generate_pptx.py`** — Complete diagram generator with `connect()` API for edge-anchored arrows, `scale` parameter, and icon registry
- **`scripts/icon_lookup.py`** — Find correct icon file by service name (fuzzy match)
- **`scripts/validate_diagram.py`** — Validate PPTX against AWS design rules (icon sizes, group colors, boundaries)

### Templates
- **`templates/template-basic-vpc.pptx`** — 2-AZ VPC with public/private subnets
- **`templates/template-serverless.pptx`** — Flat serverless layout
- **`templates/template-multi-account.pptx`** — Multi-account organization
- **`templates/template-3az-ha.pptx`** — 3-AZ high availability
- **`templates/template-hybrid-cloud.pptx`** — On-premises + AWS VPC
