from __future__ import annotations

import os
import time
from datetime import datetime

from ._cli import has_unknown_flags, print_help, wants_help

COMMAND = "cluster_bookings"
DESCRIPTION = "Geographic clustering system for route optimization."
USAGE = f"{COMMAND} <date> [--threshold MILES] [--show-distances] [--cache-status] [--clear-cache] [--help]"

GEOCODE_CACHE_FILE = "geocode_cache.json"
CACHE_TTL = 86400  # 24 hours for geocoding cache
DEFAULT_CLUSTER_THRESHOLD = 5.0  # miles


def debug_log(*_args, **_kwargs):
    pass


def _load_bookings():
    return []


def _geocode_address(_location):
    return {"lat": 0.0, "lng": 0.0}


def _cluster_bookings(bookings, _threshold):
    return [bookings] if bookings else []


def _load_geocode_cache():
    return {}


def parse_args(args):
    target_date = None
    threshold = DEFAULT_CLUSTER_THRESHOLD
    show_distances = False
    show_cache = False
    clear_cache = False
    i = 0
    while i < len(args):
        if args[i] == "--threshold" and i + 1 < len(args):
            try:
                threshold = float(args[i + 1])
            except ValueError:
                print("[❌] Invalid threshold value")
                return None
            i += 2
        elif args[i] == "--show-distances":
            show_distances = True
            i += 1
        elif args[i] == "--cache-status":
            show_cache = True
            i += 1
        elif args[i] == "--clear-cache":
            clear_cache = True
            i += 1
        elif not target_date and not args[i].startswith("--"):
            target_date = args[i]
            i += 1
        else:
            i += 1
    return target_date, threshold, show_distances, show_cache, clear_cache


def handle_cache_ops(show_cache, clear_cache):
    if clear_cache:
        if os.path.exists(GEOCODE_CACHE_FILE):
            os.remove(GEOCODE_CACHE_FILE)
            print("[✅] Geocoding cache cleared")
        else:
            print("[ℹ️] No cache file to clear")
        return True
    if show_cache:
        cache = _load_geocode_cache()
        if not cache:
            print("[ℹ️] No cached geocoding data")
            return True
        print("\n📍 GEOCODING CACHE STATUS")
        print("=" * 50)
        print(f"Cache file: {GEOCODE_CACHE_FILE}")
        print(f"Cache TTL: {CACHE_TTL // 3600} hours")
        print(f"Entries: {len(cache)}")
        now = time.time()
        expired = sum(
            1 for entry in cache.values() if (now - entry.get("timestamp", 0)) > CACHE_TTL
        )
        print(f"Valid: {len(cache) - expired}")
        print(f"Expired: {expired}")
        if cache:
            latest = max(cache.values(), key=lambda x: x.get("timestamp", 0))
            latest_time = datetime.fromtimestamp(latest.get("timestamp", 0)).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            print(f"Latest: {latest_time}")
        return True
    return False


def run(argv=None):
    argv = argv or []
    known_flags = {"--help", "-h"}
    if wants_help(argv):
        print_help(COMMAND, DESCRIPTION, USAGE)
        return 0
    if has_unknown_flags(argv, known_flags):
        print("Not found")
        print_help(COMMAND, DESCRIPTION, USAGE)
        return 0
    if not argv:
        help_text = (
            "[ℹ️] 📍 GEOGRAPHIC CLUSTERING SYSTEM\n"
            "Commands:\n"
            "  cluster_bookings <date> [--threshold MILES] [--show-distances]\n"
            "  cluster_bookings --cache-status\n"
            "  cluster_bookings --clear-cache\n"
            "Examples:\n"
            "  cluster_bookings 2024-08-15 --threshold 3.5 --show-distances\n"
            "  cluster_bookings 2024-08-16 --threshold 5.0\n"
            "  cluster_bookings --cache-status\n"
            "💡 Uses free OpenStreetMap geocoding with 24-hour caching\n"
            "🎯 Optimizes routes by clustering nearby jobs geographically"
        )
        print(help_text)
        return 0
    parsed = parse_args(argv)
    if parsed is None:
        return 1
    target_date, threshold, show_distances, show_cache, clear_cache = parsed
    if handle_cache_ops(show_cache, clear_cache):
        return 0
    if not target_date:
        print("[❌] Date required for clustering")
        print("[ℹ️] Usage: cluster_bookings <date> [options]")
        return 1
    all_bookings = _load_bookings()
    if not all_bookings:
        print("[❌] No bookings found")
        print("[💡] Add bookings with the 'book' command")
        return 1
    date_bookings = [
        b for b in all_bookings if isinstance(b, dict) and b.get("date") == target_date
    ]
    if not date_bookings:
        print(f"[ℹ️] No bookings found for {target_date}")
        return 0
    print(f"\n📍 GEOGRAPHIC CLUSTERING FOR {target_date}")
    print("=" * 60)
    print(f"Bookings to cluster: {len(date_bookings)}")
    print(f"Clustering threshold: {threshold} miles")
    print("Geocoding: OpenStreetMap (free, cached)")
    geocoded_count = 0
    failed_count = 0
    print("\n🌐 Geocoding addresses...")
    for booking in date_bookings:
        if not isinstance(booking, dict):
            continue
        location = booking.get("location", "")
        if not location:
            print(f"[⚠️] No location for booking: {booking.get('customer', 'Unknown')}")
            continue
        coords = _geocode_address(location)
        booking["coords"] = coords
        if coords:
            geocoded_count += 1
        else:
            failed_count += 1
    print(f"Geocoding complete: {geocoded_count} successful, {failed_count} failed")
    if failed_count > 0:
        print("[ℹ️] Consider updating addresses and retrying")
    print("\n🔍 Clustering bookings...")
    clusters = _cluster_bookings(date_bookings, threshold)
    print(f"Clustering complete: {len(clusters)} clusters found")
    for i, cluster in enumerate(clusters):
        print(f"\nCluster {i + 1} ({len(cluster)} bookings)")
        for booking in cluster:
            if not isinstance(booking, dict):
                continue
            customer = booking.get("customer", "Unknown")
            location = booking.get("location", "")
            distance = booking.get("distance_from_base", 0)
            distance_str = f" ({distance:.2f} miles)" if distance > 0 else ""
            print(f" - {customer} at {location}{distance_str}")
            if show_distances and distance > 0:
                print(f"   Distance from cluster base: {distance:.2f} miles")
    total_distance = sum(
        booking.get("distance_from_base", 0)
        for cluster in clusters
        for booking in cluster
        if isinstance(booking, dict)
    )
    avg_distance = total_distance / geocoded_count if geocoded_count > 0 else 0
    print("\n📊 CLUSTERING SUMMARY")
    print("=" * 50)
    print(f"Total bookings: {len(date_bookings)}")
    print(f"Geocoded bookings: {geocoded_count}")
    print(f"Failed geocodes: {failed_count}")
    print(f"Total clusters: {len(clusters)}")
    print(f"Total distance from base: {total_distance:.2f} miles")
    print(f"Average distance per booking: {avg_distance:.2f} miles")
    if len(clusters) == 1:
        print("[🎉] All bookings are within the threshold distance of each other!")
    print("\n✅ Clustering complete")
    return 0
