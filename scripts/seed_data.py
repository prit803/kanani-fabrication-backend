"""Seed script to POST vendors and bill items to local API endpoints.

Usage:
    python scripts/seed_data.py --base http://localhost:8000

The script:
- Posts each vendor to POST /vendors as form-data and uploads the same image for all vendors.
- Groups bill items by `bill_id` and posts each group to POST /bill-items to create bills/items.

Adjust `BASE_URL` when running if your server runs on a different host/port.
"""

import argparse
import json
import os
import tempfile
from collections import defaultdict
from urllib.parse import urlparse

import requests

# --- Data copied from the user's input ---
VENDORS = [
    {
        "vendor_name": "Rameshbhai Patel",
        "mobile_number": "9876543210",
        "shop_name": "Shree Ram Fabrication Works",
        "address": "GIDC Phase 1, Vatva, Ahmedabad, Gujarat",
        "status": "active",
    },
    {
        "vendor_name": "Maheshbhai Solanki",
        "mobile_number": "9825012345",
        "shop_name": "Om Steel Fabrication",
        "address": "Naroda GIDC, Ahmedabad, Gujarat",
        "status": "active",
    },
    {
        "vendor_name": "Jigneshbhai Chauhan",
        "mobile_number": "9909123456",
        "shop_name": "Jay Ambe Engineering & Fabrication",
        "address": "Makarpura GIDC, Vadodara, Gujarat",
        "status": "active",
    },
    {
        "vendor_name": "Kiritbhai Parmar",
        "mobile_number": "9723456789",
        "shop_name": "Krishna Welding & Fabrication",
        "address": "Sachin GIDC, Surat, Gujarat",
        "status": "active",
    },
    {
        "vendor_name": "Bhaveshbhai Makwana",
        "mobile_number": "9898765432",
        "shop_name": "Umiya Steel Works",
        "address": "Shapar-Veraval GIDC, Rajkot, Gujarat",
        "status": "active",
    },
    {
        "vendor_name": "Hasmukhbhai Rabari",
        "mobile_number": "9925234567",
        "shop_name": "Ganesh Fabrication",
        "address": "Kathwada GIDC, Ahmedabad, Gujarat",
        "status": "active",
    },
    {
        "vendor_name": "Dineshbhai Vaghela",
        "mobile_number": "9898123456",
        "shop_name": "Mahalaxmi Steel Fabricators",
        "address": "Odhav, Ahmedabad, Gujarat",
        "status": "inactive",
    },
    {
        "vendor_name": "Pravinbhai Gohil",
        "mobile_number": "9978901234",
        "shop_name": "Shiv Shakti Engineering Works",
        "address": "Halol GIDC, Panchmahal, Gujarat",
        "status": "active",
    },
    {
        "vendor_name": "Mukeshbhai Prajapati",
        "mobile_number": "9824321098",
        "shop_name": "Patel Metal Works",
        "address": "Ankleshwar GIDC, Bharuch, Gujarat",
        "status": "active",
    },
    {
        "vendor_name": "Alpeshbhai Thakor",
        "mobile_number": "9712345678",
        "shop_name": "Ambica Fabrication",
        "address": "Changodar GIDC, Ahmedabad, Gujarat",
        "status": "active",
    },
]

# Use this same image path for all vendors (relative to project root)
DEFAULT_VENDOR_IMAGE = os.path.join(
    "storage", "vendors", "vendor_new_20260812182825536252.jpg"
)

BILLS = [
    {"vendor_id": 7, "bill_date": "2026-08-07", "status": "pending"},
    {"vendor_id": 4, "bill_date": "2026-08-07", "status": "pending"},
    {"vendor_id": 6, "bill_date": "2026-08-07", "status": "pending"},
    {"vendor_id": 5, "bill_date": "2026-08-07", "status": "pending"},
    {"vendor_id": 3, "bill_date": "2026-08-07", "status": "pending"},
    {"vendor_id": 2, "bill_date": "2026-08-07", "status": "pending"},
]

BILL_ITEMS = [
    {
        "bill_id": 1,
        "item_description": "એમએસ એંગલ 50x50 - 120 કિલો",
        "quantity": 120,
        "rate": 78.5,
        "audio_file_url": "",
    },
    {
        "bill_id": 1,
        "item_description": "વેલ્ડિંગ કામ",
        "quantity": 1,
        "rate": 2500,
        "audio_file_url": "",
    },
    {
        "bill_id": 1,
        "item_description": "ગ્રાઇન્ડિંગ અને ફિનિશિંગ",
        "quantity": 1,
        "rate": 1200,
        "audio_file_url": "",
    },
    {
        "bill_id": 2,
        "item_description": "એમએસ પાઇપ 2 ઇંચ",
        "quantity": 35,
        "rate": 520,
        "audio_file_url": "",
    },
    {
        "bill_id": 2,
        "item_description": "ગેસ કટિંગ ચાર્જ",
        "quantity": 1,
        "rate": 1800,
        "audio_file_url": "",
    },
    {
        "bill_id": 3,
        "item_description": "એમએસ ચેનલ 100x50",
        "quantity": 18,
        "rate": 980,
        "audio_file_url": "",
    },
    {
        "bill_id": 3,
        "item_description": "વેલ્ડિંગ રોડ",
        "quantity": 8,
        "rate": 450,
        "audio_file_url": "",
    },
    {
        "bill_id": 3,
        "item_description": "મજૂરી ચાર્જ",
        "quantity": 1,
        "rate": 3500,
        "audio_file_url": "",
    },
    {
        "bill_id": 4,
        "item_description": "સ્ટેનલેસ સ્ટીલ શીટ 2 મીમી",
        "quantity": 10,
        "rate": 3200,
        "audio_file_url": "",
    },
    {
        "bill_id": 4,
        "item_description": "ટીઆઈજી વેલ્ડિંગ",
        "quantity": 1,
        "rate": 4200,
        "audio_file_url": "",
    },
    {
        "bill_id": 5,
        "item_description": "એમએસ ફ્લેટ 40x6",
        "quantity": 250,
        "rate": 72,
        "audio_file_url": "",
    },
    {
        "bill_id": 5,
        "item_description": "ગેટ બનાવવાનું કામ",
        "quantity": 1,
        "rate": 6500,
        "audio_file_url": "",
    },
    {
        "bill_id": 5,
        "item_description": "ઇન્સ્ટોલેશન ચાર્જ",
        "quantity": 1,
        "rate": 2500,
        "audio_file_url": "",
    },
    {
        "bill_id": 6,
        "item_description": "જીઆઈ પાઇપ 1.5 ઇંચ",
        "quantity": 40,
        "rate": 610,
        "audio_file_url": "",
    },
    {
        "bill_id": 6,
        "item_description": "આર્ક વેલ્ડિંગ",
        "quantity": 1,
        "rate": 3200,
        "audio_file_url": "",
    },
]


def normalize_base(base: str) -> str:
    """Normalize various base inputs; strip /docs or other UI paths."""
    if not base:
        return base
    # If user passed docs or redoc URL, strip path after host
    if "/docs" in base:
        base = base.split("/docs")[0]
    if "/redoc" in base:
        base = base.split("/redoc")[0]
    # Remove trailing slash
    return base.rstrip("/")


def _download_temp_image(url: str) -> str | None:
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        suffix = os.path.splitext(urlparse(url).path)[1] or ".jpg"
        fd, path = tempfile.mkstemp(suffix=suffix)
        with os.fdopen(fd, "wb") as f:
            f.write(resp.content)
        return path
    except Exception as e:
        print(f"Failed to download image from {url}: {e}")
        return None


def post_vendors(
    base_url: str,
    project_root: str,
    image_override: str | None = None,
    image_remote_url: str | None = None,
):
    url = base_url + "/vendors"
    image_path = None
    if image_override:
        image_path = image_override
    else:
        image_path = os.path.join(project_root, DEFAULT_VENDOR_IMAGE)

    temp_downloaded = None

    # If remote URL provided, download it to temp file and use for uploads
    if image_remote_url:
        temp_downloaded = _download_temp_image(image_remote_url)
        if temp_downloaded:
            image_path = temp_downloaded

    print(f"Posting {len(VENDORS)} vendors to {url}")

    for idx, v in enumerate(VENDORS, start=1):
        data = {
            "vendor_name": v["vendor_name"],
            "mobile_number": v["mobile_number"],
            "shop_name": v.get("shop_name"),
            "address": v.get("address"),
            "status": v.get("status", "active"),
        }

        files = None
        if image_path and os.path.isfile(image_path):
            files = {
                "photo_file": (
                    os.path.basename(image_path),
                    open(image_path, "rb"),
                    "image/jpeg",
                )
            }
        else:
            print(
                f"Warning: image not found at {image_path}. Posting without file for vendor {v['vendor_name']}"
            )

        try:
            resp = requests.post(url, data=data, files=files, timeout=30)
            if files:
                files["photo_file"][1].close()
        except Exception as e:
            print(f"Error posting vendor {v['vendor_name']}: {e}")
            continue

        if 200 <= resp.status_code < 300:
            print(f"[{idx}] Created vendor: {v['vendor_name']} -> {resp.status_code}")
        else:
            print(
                f"[{idx}] Failed to create vendor: {v['vendor_name']} -> {resp.status_code} {resp.text}"
            )

    if temp_downloaded and os.path.isfile(temp_downloaded):
        try:
            os.remove(temp_downloaded)
        except Exception:
            pass


def post_bills_and_items(base_url: str):
    url = base_url.rstrip("/") + "/bill-items"
    print(f"Posting grouped bill-items to {url}")

    # Group items by bill_id
    groups = defaultdict(list)
    for item in BILL_ITEMS:
        groups[item["bill_id"]].append(
            {
                "item_description": item["item_description"],
                "quantity": item["quantity"],
                "rate": item["rate"],
                "audio_file_url": item.get("audio_file_url") or None,
            }
        )

    # For each bill_id group, use BILLS[bill_id-1] as the bill metadata (vendor_id, bill_date, status)
    for bill_id, items in sorted(groups.items()):
        index = bill_id - 1
        if index < 0 or index >= len(BILLS):
            print(f"No bill metadata for bill_id={bill_id}, skipping")
            continue

        bill_meta = BILLS[index]
        payload = {
            "vendor_id": bill_meta.get("vendor_id"),
            "bill_date": bill_meta.get("bill_date"),
            "status": bill_meta.get("status"),
            "items": items,
        }

        try:
            resp = requests.post(url, json=payload)
        except Exception as e:
            print(f"Error posting bill {bill_id}: {e}")
            continue

        if resp.status_code >= 200 and resp.status_code < 300:
            print(
                f"Created bill (from bill_id {bill_id}): {resp.status_code} -> {resp.text}"
            )
        else:
            print(f"Failed to create bill {bill_id}: {resp.status_code} {resp.text}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--base",
        default="http://localhost:8000",
        help="Base URL for the API (default: http://localhost:8000). Can be docs URL like http://host/docs",
    )
    parser.add_argument(
        "--root",
        default=os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
        help="Project root (where storage/ lives)",
    )
    parser.add_argument(
        "--skip-vendors", action="store_true", help="Skip posting vendors"
    )
    parser.add_argument(
        "--skip-bills", action="store_true", help="Skip posting bills and items"
    )
    parser.add_argument(
        "--image-override",
        default=None,
        help="Path to local image to use for all vendors (overrides default)",
    )
    parser.add_argument(
        "--image-remote-url",
        default=None,
        help="URL of an image to download and upload for all vendors",
    )
    args = parser.parse_args()

    base = normalize_base(args.base)

    if not args.skip_vendors:
        post_vendors(
            base,
            args.root,
            image_override=args.image_override,
            image_remote_url=args.image_remote_url,
        )

    if not args.skip_bills:
        post_bills_and_items(base)


if __name__ == "__main__":
    main()


# python scripts/seed_data.py --base http://15.206.212.35/docs --image-remote-url https://example.com/photos/vendor1.jpg

# python scripts/seed_data.py --base http://localhost:8000


# pip install requests
# python scripts/seed_data.py --base http://15.206.212.35/docs --image-override storage/vendors/vendor_new_20260812182825536252.jpg
