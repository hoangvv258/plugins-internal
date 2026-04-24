# AWS Architecture Group Colors

Complete reference for all group container border specifications.

## Group Types

| Group Type | Border Color | Hex | Dash Style | Icon File | python-pptx Dash |
|---|---|---|---|---|---|
| AWS Cloud | Squid Ink | #232F3E | Solid | `AWS-Cloud_32.png` | `None` |
| AWS Account | Pink | #E7157B | Solid | `AWS-Account_32.png` | `None` |
| Region | Teal | #00A4A6 | Square Dot | `Region_32.png` | `MSO_LINE_DASH_STYLE.SQUARE_DOT` |
| Availability Zone | Teal | #00A4A6 | Dashed | _(none)_ | `MSO_LINE_DASH_STYLE.DASH` |
| VPC | Purple | #8C4FFF | Solid | `Virtual-private-cloud-VPC_32.png` | `None` |
| Public Subnet | Green | #7AA116 | Solid | `Public-subnet_32.png` | `None` |
| Private Subnet | Teal | #00A4A6 | Solid | `Private-subnet_32.png` | `None` |
| Security Group | Red | #DD344C | Solid | _(none)_ | `None` |
| Auto Scaling Group | Orange | #ED7100 | Dashed | `Auto-Scaling-group_32.png` | `MSO_LINE_DASH_STYLE.DASH` |
| EC2 Instance Contents | Orange | #ED7100 | Solid | `EC2-instance-contents_32.png` | `None` |
| Spot Fleet | Orange | #ED7100 | Solid | `Spot-Fleet_32.png` | `None` |
| Elastic Beanstalk | Orange | #ED7100 | Solid | _(none)_ | `None` |
| Step Functions Workflow | Pink | #E7157B | Solid | _(none)_ | `None` |
| Corporate Data Center | Gray | #7D8998 | Solid | `Corporate-data-center_32.png` | `None` |
| Server Contents | Gray | #7D8998 | Solid | `Server-contents_32.png` | `None` |
| IoT Greengrass | Green | #7AA116 | Solid | `AWS-IoT-Greengrass-Deployment_32.png` | `None` |
| Generic Group | Gray | #7D8998 | Solid/Dashed | _(none)_ | `None` or `DASH` |

## Border Specifications

- **Width**: 1.25pt (15875 EMU, `Pt(1.25)`)
- **Fill**: Always transparent (`shape.fill.background()`)
- **Icon position**: Top-left corner of rectangle, 0.42×0.42 inches
- **Label**: Inside rectangle text_frame, Arial 12pt

## Group Icon File Paths

All group icons are in:
```
Icon-package_01302026.31b40d126ed27079b708594940ad577a86150582/Architecture-Group-Icons_01302026/
```

Available icons:
| File | Group Type |
|---|---|
| `AWS-Account_32.png` | AWS Account |
| `AWS-Cloud-logo_32.png` | AWS Cloud (logo variant) |
| `AWS-Cloud_32.png` | AWS Cloud |
| `AWS-IoT-Greengrass-Deployment_32.png` | IoT Greengrass |
| `Auto-Scaling-group_32.png` | Auto Scaling Group |
| `Corporate-data-center_32.png` | Corporate Data Center |
| `EC2-instance-contents_32.png` | EC2 Instance Contents |
| `Private-subnet_32.png` | Private Subnet |
| `Public-subnet_32.png` | Public Subnet |
| `Region_32.png` | Region |
| `Server-contents_32.png` | Server Contents |
| `Spot-Fleet_32.png` | Spot Fleet |
| `Virtual-private-cloud-VPC_32.png` | VPC |

## Nesting Hierarchy

Standard nesting order (outermost → innermost):

```
AWS Cloud
└── AWS Account (optional, multi-account)
    └── Region
        └── VPC
            ├── Availability Zone
            │   ├── Public Subnet
            │   │   └── Security Group
            │   │       └── EC2 Instance / Auto Scaling Group
            │   └── Private Subnet
            │       └── Security Group
            │           └── EC2 Instance / Auto Scaling Group
            └── (VPC-level resources: NAT Gateway, Internet Gateway)
```

## Nesting Buffer Rule

Inner groups must maintain ≥ 0.05 inches (45720 EMU) buffer on all sides from parent group boundary.

## Custom Groups

When creating groups not in the predefined list, use one of the 7 approved custom colors:

| Color | Hex |
|---|---|
| Purple | #8C4FFF |
| Pink | #E7157B |
| Green | #7AA116 |
| Mint | #01A88D |
| Orange | #ED7100 |
| Red | #DD344C |
| Magenta | #C925D1 |

Custom groups use:
- Solid or dashed border (choose based on whether boundary is fixed or elastic)
- No predefined group icon
- Same 1.25pt border width
