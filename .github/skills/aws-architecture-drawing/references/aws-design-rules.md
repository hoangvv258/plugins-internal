# AWS Architecture Design Rules

Extracted from the official AWS Architecture Icons PPTX Deck (Release 2026.01.30).

## Typography

| Context | Font | Size | Weight | Color |
|---|---|---|---|---|
| Diagram title | Arial | 20pt | Bold | Black |
| Group label | Arial | 12pt | Regular | Black |
| Service icon label | Arial | 12pt | Regular | Black |
| Resource icon label | Arial | 12pt | Regular | Black |
| Training/Cert diagrams | Arial | 16pt | Regular | Black |
| Annotations/CIDR | Arial | 12pt | Regular | Black |

## Icon Rules

### Service Icons (48px / 0.83in)
- Represent an AWS service
- Size: 0.83 × 0.83 inches in diagrams
- Format: PNG (from 48/ directory)
- **DO**: Use at predefined size, color, and format
- **DON'T**: Crop, flip, rotate, or change icon shapes

### Resource Icons (48px / 0.50in)
- Represent a service resource (sub-component)
- Size: 0.50 × 0.50 inches in diagrams
- Format: PNG (from Res_* directories)

### Group Icons (32px / 0.42in)
- Placed in top-left corner of group rectangles
- Size: 0.42 × 0.42 inches
- Format: PNG (from Architecture-Group-Icons directory)

### General Resource Icons
- Apply to resources across multiple AWS services
- Size: ~0.51 × 0.51 inches
- Used for generic concepts (User, Server, Database, Internet, etc.)

## Icon Labels

- Font: 12pt Arial, centered below icon
- Max 2 lines for service names
- "AWS" or "Amazon" must always accompany the service name
- Line breaks after the second word if necessary

### Short Forms
- Allowed after full name is mentioned once in the document
- Examples: EC2, S3, Lambda, RDS, DynamoDB, CloudFront
- **DON'T**: Use short forms without first mentioning full name
- **DON'T**: Use duplicate short forms for different services

## Groups (Containers)

### Structure
Each group consists of:
1. **Rectangle** — Transparent fill (`shape.fill.background()`), colored border
2. **Group Icon** — 0.42×0.42in PNG, top-left corner of rectangle
3. **Label Text** — Part of rectangle's text_frame, Arial 12pt

### Border Specification
- Width: 1.25pt (15875 EMU)
- Color and dash style vary by group type (see group-colors.md)

### Resizing
- Use bottom-right corner to resize
- Inner nested groups need ≥ 0.05in buffer on all sides

### Nesting Order (outermost → innermost)
1. AWS Cloud
2. AWS Account (if multi-account)
3. Region
4. VPC
5. Availability Zone
6. Public/Private Subnet
7. Security Group
8. Auto Scaling Group / EC2 Instance Contents

## Arrows and Connectors

### Specifications
- Width: 1.25pt (15875 EMU) — matches group border width
- Arrow head: "Open Arrow" Size 4 (w=lg, len=lg in OOXML)
- Color: Default black/dark gray

### Types
| Type | Head | Tail | Use Case |
|---|---|---|---|
| One-way | none | arrow | Data flow, request direction |
| Bidirectional | arrow | arrow | Two-way communication |
| Plain line | none | none | Simple connection/association |
| Elbow connector | varies | varies | Right-angle routing between shapes |
| Dashed line | none | none | Optional/conditional flow |

### Rules
- **DO**: Use straight lines and right angles
- **DO**: Copy preset arrows to maintain formatting
- **DO**: Hold Shift for perfectly straight lines
- **DO**: Use elbow connectors for right-angle paths
- **DON'T**: Use anything besides preset or default arrows
- **DON'T**: Use curved or diagonal lines when avoidable

## Slide Dimensions

- Width: 13.33 inches (12192000 EMU)
- Height: 7.50 inches (6858000 EMU)
- Format: Widescreen 16:9

## Color Palette

### Group Border Colors
| Color Name | Hex | Used By |
|---|---|---|
| Squid Ink (default) | #23272A | AWS Cloud |
| Purple | #8C4FFF | VPC, custom groups |
| Teal | #00A4A6 | Region, AZ, Private Subnet |
| Green | #7AA116 | Public Subnet, IoT Greengrass |
| Orange | #ED7100 | Auto Scaling, EC2, Spot Fleet, Elastic Beanstalk |
| Pink | #E7157B | AWS Account, Step Functions |
| Red | #DD344C | Security Group |
| Gray | #7D8998 | Corporate Data Center, Server, Generic |
| Mint | #01A88D | Custom groups |
| Magenta | #C925D1 | Custom groups |

### Approved Custom Group Colors (7)
#8C4FFF, #E7157B, #7AA116, #01A88D, #ED7100, #DD344C, #C925D1
