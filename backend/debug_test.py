"""Quick test of the consumption logic - run with: python debug_test.py"""
import sys, os
sys.path.insert(0, '.')
from datetime import date as dt_date
from app.api.v1.consumption import _compute_trajectory, _get_latest_snapshot, _get_cycle_units
from app.services.tariff import get_cycle_start

readings = [
    {'reading_value': 300.0, 'units_since_last': 18.0, 'reading_date': '2026-06-28'},
    {'reading_value': 282.0, 'units_since_last': None, 'reading_date': '2026-06-22'},
]

print("=== _compute_trajectory ===")
sorted_asc = sorted(readings, key=lambda r: r['reading_date'])
first = sorted_asc[0]
print(f"First reading: {first}")
print(f"first.get('units_since_last') is None: {first.get('units_since_last') is None}")

if first.get('units_since_last') is None or float(first.get('units_since_last') or 0) == 0:
    total = float(first['reading_value']) + sum(float(r.get('units_since_last') or 0) for r in sorted_asc[1:])
else:
    total = sum(float(r.get('units_since_last') or 0) for r in readings)
print(f"Total: {total}  (expected: 300)")
print(f"Readings count: {len(readings)}  (expected: 2)")

print()
print("=== _get_latest_snapshot ===")
snap = _get_latest_snapshot(readings, None, None)
print(f"Snapshot: {snap}")

print()
print("=== get_cycle_start ===")
class MockAcc: pass
acc = MockAcc()
print(f"No bill: {get_cycle_start(acc, None)}")
print(f"Bill issue 2026-06-15: {get_cycle_start(acc, {'issue_date': '2026-06-15'})}")
print(f"Bill issue 2025-12-20: {get_cycle_start(acc, {'issue_date': '2025-12-20'})}")

print()
print("=== _get_cycle_units (async would need real DB) ===")
print("(Skipped - needs Supabase connection)")
