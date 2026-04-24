#!/usr/bin/env python3
"""
Serverless Web Application Architecture Diagram
Two-row layout: API flow (top) and async flow (bottom).

Architecture:
  Row 1: CloudFront → API Gateway → Lambda (API) → DynamoDB/S3
  Row 2: Route 53 → CloudFront, Cognito → API GW, Lambda (Worker) → SNS
  Middle: SQS connects the flows
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from generate_pptx import AWSArchitectureDiagram

ASSETS = os.path.join(os.path.dirname(__file__), '..', 'assets')
ICONS = os.path.join(ASSETS, 'service-icons')
GEN = os.path.join(ASSETS, 'general-icons')

d = AWSArchitectureDiagram("Serverless Web Application Architecture",
                           icon_base_path=ASSETS, scale=0.80)

# ─── Groups ───────────────────────────────────────────────────────────────

# Users
d.add_group("Generic", 0.3, 2.0, 1.2, 1.3, label="Users")

# AWS Cloud
d.add_group("AWS Cloud", 2.0, 0.8, 10.8, 6.0)
d.add_group("Region", 2.2, 1.0, 10.4, 5.6, label="us-east-1")

# ─── Service Icons ────────────────────────────────────────────────────────

# Users
d.add_general_icon(f"{GEN}/Res_General_Users_48.png", "Users", 0.9, 2.3, name="Users")

# Row 1 (top flow): y=1.5
d.add_service_icon(f"{ICONS}/Arch_Amazon-CloudFront_48.png",
                   "Amazon\nCloudFront", 3.0, 1.5, name="CloudFront")
d.add_service_icon(f"{ICONS}/Arch_Amazon-API-Gateway_48.png",
                   "Amazon\nAPI Gateway", 4.8, 1.5, name="APIGateway")
d.add_service_icon(f"{ICONS}/Arch_AWS-Lambda_48.png",
                   "AWS Lambda\n(API)", 6.6, 1.5, name="LambdaAPI")
d.add_service_icon(f"{ICONS}/Arch_Amazon-DynamoDB_48.png",
                   "Amazon\nDynamoDB", 10.5, 1.5, name="DynamoDB")
d.add_service_icon(f"{ICONS}/Arch_Amazon-Simple-Storage-Service_48.png",
                   "Amazon S3", 10.5, 3.5, name="S3")

# Middle: SQS
d.add_service_icon(f"{ICONS}/Arch_Amazon-Simple-Queue-Service_48.png",
                   "Amazon SQS", 8.4, 2.8, name="SQS")

# Row 2 (bottom flow): y=4.5
d.add_service_icon(f"{ICONS}/Arch_Amazon-Route-53_48.png",
                   "Amazon\nRoute 53", 3.0, 4.5, name="Route53")
d.add_service_icon(f"{ICONS}/Arch_Amazon-Cognito_48.png",
                   "Amazon\nCognito", 4.8, 4.5, name="Cognito")
d.add_service_icon(f"{ICONS}/Arch_AWS-Lambda_48.png",
                   "AWS Lambda\n(Worker)", 6.6, 4.5, name="LambdaWorker")
d.add_service_icon(f"{ICONS}/Arch_Amazon-Simple-Notification-Service_48.png",
                   "Amazon SNS", 8.4, 5.0, name="SNS")

# ─── Connections ──────────────────────────────────────────────────────────

# Users → CloudFront
d.connect("Users", "CloudFront", from_dir="right", to_dir="left")

# DNS
d.connect("Route53", "CloudFront", from_dir="top", to_dir="bottom")

# API flow
d.connect("CloudFront", "APIGateway", from_dir="right", to_dir="left")
d.connect("APIGateway", "LambdaAPI", from_dir="right", to_dir="left")
d.connect("LambdaAPI", "DynamoDB", from_dir="right", to_dir="left")
d.connect_routed("LambdaAPI", "S3",
                 [(6.6, 4.0), (10.5, 4.0)],
                 from_dir="bottom", to_dir="top")

# Auth
d.connect("Cognito", "APIGateway", from_dir="top", to_dir="bottom")

# Async flow
d.connect("LambdaAPI", "SQS", from_dir="right", to_dir="left")
d.connect("SQS", "LambdaWorker", from_dir="bottom", to_dir="right")
d.connect("LambdaWorker", "SNS", from_dir="right", to_dir="left")

# ─── Save ─────────────────────────────────────────────────────────────────

out = os.path.join(os.getcwd(), "serverless-web-app.pptx")
d.save(out)
print(f"Saved: {out}")
