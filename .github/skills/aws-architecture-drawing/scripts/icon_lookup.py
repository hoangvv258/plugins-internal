#!/usr/bin/env python3
"""
AWS Architecture Icon Lookup Script
Finds the correct icon file path by service name using fuzzy matching.

Usage:
    python icon_lookup.py "Lambda"
    python icon_lookup.py "EC2" --type resource
    python icon_lookup.py "VPC" --type group
"""

import os
import sys
import argparse
from difflib import SequenceMatcher

# Base path for icon assets (relative to skill root: .github/skills/aws-architecture-drawing/)
SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(SKILL_ROOT, "assets")
SERVICE_DIR = os.path.join(ASSETS_DIR, "service-icons")
RESOURCE_DIR = os.path.join(ASSETS_DIR, "resource-icons")
GROUP_DIR = os.path.join(ASSETS_DIR, "group-icons")
CATEGORY_DIR = os.path.join(ASSETS_DIR, "category-icons")


def normalize(name):
    """Normalize name for fuzzy matching."""
    return name.lower().replace("-", " ").replace("_", " ").replace("aws ", "").replace("amazon ", "")


def similarity(a, b):
    """Calculate similarity ratio between two strings."""
    return SequenceMatcher(None, normalize(a), normalize(b)).ratio()


def find_service_icons(query, base_path=None):
    """Find service icons matching the query."""
    base = base_path or SERVICE_DIR
    results = []
    if not os.path.exists(base):
        return results
    for f in os.listdir(base):
        if not f.endswith(".png"):
            continue
        name = f.replace("Arch_", "").replace("_48.png", "").replace("-", " ")
        score = similarity(query, name)
        if score > 0.4 or normalize(query) in normalize(name):
            results.append({
                "name": name,
                "file": f,
                "path": os.path.join(base, f),
                "type": "service",
                "score": score,
            })
    return sorted(results, key=lambda x: x["score"], reverse=True)


def find_resource_icons(query, base_path=None):
    """Find resource icons matching the query."""
    base = base_path or RESOURCE_DIR
    results = []
    if not os.path.exists(base):
        return results
    for f in os.listdir(base):
        if not f.endswith(".png") or "_48" not in f:
            continue
        name = f.replace("Res_", "").replace("_48.png", "").replace("-", " ").replace("_", " ")
        score = similarity(query, name)
        if score > 0.3 or normalize(query) in normalize(name):
            results.append({
                "name": name,
                "file": f,
                "path": os.path.join(base, f),
                "type": "resource",
                "score": score,
            })
    return sorted(results, key=lambda x: x["score"], reverse=True)


def find_group_icons(query, base_path=None):
    """Find group icons matching the query."""
    base = base_path or GROUP_DIR
    results = []
    if not os.path.exists(base):
        return results
    for f in os.listdir(base):
        if not f.endswith(".png") or "_Dark" in f:
            continue
        name = f.replace("_32.png", "").replace("-", " ")
        score = similarity(query, name)
        if score > 0.3 or normalize(query) in normalize(name):
            results.append({
                "name": name,
                "file": f,
                "path": os.path.join(base, f),
                "type": "group",
                "score": score,
            })
    return sorted(results, key=lambda x: x["score"], reverse=True)


def find_category_icons(query, base_path=None):
    """Find category icons matching the query."""
    base = base_path or CATEGORY_DIR
    results = []
    if not os.path.exists(base):
        return results
    for f in os.listdir(base):
        if not f.endswith(".png"):
            continue
        name = f.replace("Arch-Category_", "").replace("_48.png", "").replace("-", " ")
        score = similarity(query, name)
        if score > 0.3 or normalize(query) in normalize(name):
            results.append({
                "name": name,
                "file": f,
                "path": os.path.join(base, f),
                "type": "category",
                "score": score,
            })
    return sorted(results, key=lambda x: x["score"], reverse=True)


def lookup(query, icon_type="all", base_path=None):
    """
    Look up icons by name.

    Args:
        query: Service/resource name to search for
        icon_type: "service", "resource", "group", or "all"
        base_path: Override base path for assets directory

    Returns:
        List of matching icons sorted by relevance
    """
    results = []
    if icon_type in ("all", "service"):
        svc_base = os.path.join(base_path, "service-icons") if base_path else None
        results.extend(find_service_icons(query, svc_base))
    if icon_type in ("all", "resource"):
        res_base = os.path.join(base_path, "resource-icons") if base_path else None
        results.extend(find_resource_icons(query, res_base))
    if icon_type in ("all", "group"):
        grp_base = os.path.join(base_path, "group-icons") if base_path else None
        results.extend(find_group_icons(query, grp_base))
    if icon_type in ("all", "category"):
        cat_base = os.path.join(base_path, "category-icons") if base_path else None
        results.extend(find_category_icons(query, cat_base))
    return sorted(results, key=lambda x: x["score"], reverse=True)


def main():
    parser = argparse.ArgumentParser(description="Find AWS Architecture Icons by name")
    parser.add_argument("query", help="Service or resource name to search for")
    parser.add_argument("--type", choices=["service", "resource", "group", "category", "all"],
                        default="all", help="Icon type to search")
    parser.add_argument("--limit", type=int, default=5, help="Max results to show")
    parser.add_argument("--base-path", help="Override base icon directory path")
    args = parser.parse_args()

    results = lookup(args.query, args.type, args.base_path)

    if not results:
        print(f"No icons found for '{args.query}'")
        sys.exit(1)

    for r in results[:args.limit]:
        print(f"[{r['type']:8s}] {r['name']}")
        print(f"           File: {r['file']}")
        print(f"           Path: {r['path']}")
        if "category" in r:
            print(f"           Category: {r['category']}")
        print(f"           Score: {r['score']:.2f}")
        print()


if __name__ == "__main__":
    main()
