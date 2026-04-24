#!/usr/bin/env python3
"""
E-Commerce Platform Architecture Diagram
Rewritten from scratch referencing official AWS Architecture Icons Deck.
Layout: left-to-right flow, 3 rows, all arrows orthogonal.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from generate_pptx import AWSArchitectureDiagram

ASSETS = os.path.join(os.path.dirname(__file__), '..', 'assets')
ICONS = os.path.join(ASSETS, 'service-icons')
GEN = os.path.join(ASSETS, 'general-icons')

d = AWSArchitectureDiagram("E-Commerce Platform", icon_base_path=ASSETS, scale=0.85)

# ═══════════════════════════════════════════════════════════════════════════════
# LAYOUT GRID — based on official AWS deck spacing rules
# Canvas: 13.33 × 7.50 in, usable area: ~0.3–13.0 x ~1.2–6.9
# Title: 0.40–1.10, Footer: 6.90–7.50
# Icon spacing: ~1.5–1.8" between columns, ~1.8" between rows
# ═══════════════════════════════════════════════════════════════════════════════

# Row Y positions (top_y of icons)
ROW_TOP = 1.70      # Row 1: Route53, S3, DynamoDB (regional, outside VPC)
ROW_MID = 3.65      # Row 2: CloudFront → API GW → WAF → ALB (main flow)
ROW_BOT = 5.40      # Row 3: EC2 → ElastiCache → RDS (private subnet)

# Column X positions (center_x of icons) — even 1.6" spacing
COL1 = 0.80         # Users
COL2 = 2.80         # Route53 / CloudFront
COL3 = 4.50         # S3 / API Gateway
COL4 = 6.80         # WAF
COL5 = 8.30         # ALB / EC2
COL6 = 9.80         # ElastiCache
COL7 = 11.30        # DynamoDB / RDS

# ═══════════════════════════════════════════════════════════════════════════════
# GROUPS — outermost → innermost, ≥0.3" between groups, ≥0.2" icon-to-border
# ═══════════════════════════════════════════════════════════════════════════════

# Users group (outside AWS Cloud)
d.add_group("Generic", 0.15, ROW_MID - 0.35, 1.30, 1.70, label="Users")

# AWS Cloud → Region
d.add_group("AWS Cloud", 1.70, 1.10, 11.55, 6.10)
d.add_group("Region", 2.10, 1.45, 10.75, 5.75, label="us-east-1")

# VPC inside Region (covers WAF/ALB/EC2/ElastiCache/RDS)
d.add_group("VPC", 5.40, 2.65, 7.20, 4.40, label="VPC (10.0.0.0/16)")

# AZ inside VPC
d.add_group("Availability Zone", 5.80, 3.00, 6.50, 3.85, label="AZ 1")

# Public Subnet (Row 2 inside VPC: WAF, ALB)
d.add_group("Public Subnet", 6.10, 3.30, 5.90, 1.60, label="Public Subnet")

# Private Subnet (Row 3 inside VPC: EC2, ElastiCache, RDS)
d.add_group("Private Subnet", 6.10, 5.15, 5.90, 1.55, label="Private Subnet")

# ═══════════════════════════════════════════════════════════════════════════════
# SERVICE ICONS — aligned on grid rows for clean orthogonal arrows
# ═══════════════════════════════════════════════════════════════════════════════

# Users icon (outside AWS Cloud)
d.add_general_icon(f"{GEN}/Res_General_Users_48.png",
                   "Users", COL1, ROW_MID, name="Users")

# Row 1 — Regional services (inside Region, outside VPC)
d.add_service_icon(f"{ICONS}/Arch_Amazon-Route-53_48.png",
                   "Amazon\nRoute 53", COL2, ROW_TOP, name="Route53")
d.add_service_icon(f"{ICONS}/Arch_Amazon-Simple-Storage-Service_48.png",
                   "Amazon S3", COL3, ROW_TOP, name="S3")
d.add_service_icon(f"{ICONS}/Arch_Amazon-DynamoDB_48.png",
                   "Amazon\nDynamoDB", COL7, ROW_TOP, name="DynamoDB")

# Row 2 — Main request flow (same Y for horizontal arrows)
d.add_service_icon(f"{ICONS}/Arch_Amazon-CloudFront_48.png",
                   "Amazon\nCloudFront", COL2, ROW_MID, name="CloudFront")
d.add_service_icon(f"{ICONS}/Arch_Amazon-API-Gateway_48.png",
                   "Amazon\nAPI Gateway", COL3, ROW_MID, name="APIGateway")
d.add_service_icon(f"{ICONS}/Arch_AWS-WAF_48.png",
                   "AWS WAF", COL4, ROW_MID, name="WAF")
d.add_service_icon(f"{ICONS}/Arch_Elastic-Load-Balancing_48.png",
                   "Application\nLoad Balancer", COL5, ROW_MID, name="ALB")

# Row 3 — Private subnet services (same Y for horizontal arrows)
d.add_service_icon(f"{ICONS}/Arch_Amazon-EC2_48.png",
                   "Amazon EC2", COL5, ROW_BOT, name="EC2")
d.add_service_icon(f"{ICONS}/Arch_Amazon-ElastiCache_48.png",
                   "Amazon\nElastiCache", COL6, ROW_BOT, name="ElastiCache")
d.add_service_icon(f"{ICONS}/Arch_Amazon-RDS_48.png",
                   "Amazon RDS", COL7, ROW_BOT, name="RDS")

# ═══════════════════════════════════════════════════════════════════════════════
# CONNECTIONS — all orthogonal (straight or elbow), no diagonals
# ═══════════════════════════════════════════════════════════════════════════════

# Row 2 horizontal flow: Users → CloudFront → API GW → WAF → ALB
d.connect("Users", "CloudFront", from_dir="right", to_dir="left")
d.connect("CloudFront", "APIGateway", from_dir="right", to_dir="left")
d.connect("APIGateway", "WAF", from_dir="right", to_dir="left")
d.connect("WAF", "ALB", from_dir="right", to_dir="left")

# Vertical: Route53 ↔ CloudFront (same column COL2)
d.connect("Route53", "CloudFront", from_dir="bottom", to_dir="top")

# Vertical: CloudFront → S3 (L-shape: up from CF, right to S3)
d.connect("CloudFront", "S3", from_dir="top", to_dir="bottom")

# Vertical: ALB → EC2 (same column COL5)
d.connect("ALB", "EC2", from_dir="bottom", to_dir="top")

# Row 3 horizontal: EC2 → ElastiCache → RDS
d.connect("EC2", "ElastiCache", from_dir="right", to_dir="left")
d.connect("ElastiCache", "RDS", from_dir="right", to_dir="left")

# EC2 → DynamoDB: route right along bottom, then up to DDB
# Path: EC2 bottom → down to 6.70 → right to COL7 → up to DDB bottom
d.connect_routed("EC2", "DynamoDB",
                 [(COL5, 6.70), (12.80, 6.70), (12.80, ROW_TOP + 1.2), (COL7, ROW_TOP + 1.2)],
                 from_dir="bottom", to_dir="bottom")

# ═══════════════════════════════════════════════════════════════════════════════
# SAVE
# ═══════════════════════════════════════════════════════════════════════════════

out = os.path.join(os.getcwd(), "ecommerce-platform.pptx")
d.save(out)
print(f"Saved: {out}")
