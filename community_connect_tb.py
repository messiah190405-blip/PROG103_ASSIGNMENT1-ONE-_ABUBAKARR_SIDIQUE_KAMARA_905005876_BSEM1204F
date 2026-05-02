"""
Community Connect
=======================================
A terminal-based household data system for community needs assessment.
Professional UI, dynamic tables, SDG 6/7 integration.
Now uses pathlib – no dependency on the os module.
"""

import json
from datetime import datetime
from pathlib import Path

# ---------- Safe import for screen clearing only ----------
try:
    import os
    HAS_OS = True
except ImportError:
    HAS_OS = False


# ---------- TO BE TREATED AS CONSTANTS ----------
MAX_HOUSEHOLDS = 200
ID_PREFIX = "HH"
DATA_FILE = "households.json"
VALID_MAIN_OPTIONS = ['1', '2', '3', '4', '5', '6', '7', '8']
VALID_SORT_KEYS = ['income', 'name', 'village']


# ---------- UTILITY: SCREEN & INPUT ----------
def clear_screen():
    """Clear the terminal. Uses os.system if possible, otherwise prints blank lines."""
    if HAS_OS:
        try:
            if os.name == 'nt':
                os.system('cls')
            else:
                os.system('clear')
            return
        except Exception:
            pass
    # Fallback – works everywhere
    print("\n" * 100)


def wait_for_enter():
    """Pause until the user presses Enter."""
    input("\nPress Enter to continue...")


def print_table(headers, rows, title=None):
    """Dynamic table printer – adapts to content width."""
    if not headers or not rows:
        print("[No data to display]\n")
        return

    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            cell_len = len(str(cell))
            if cell_len > col_widths[i]:
                col_widths[i] = cell_len

    total_width = sum(col_widths) + (3 * (len(headers) - 1)) + 4
    sep = "=" * total_width

    if title:
        print(sep)
        print(title.center(total_width))
        print(sep)
    else:
        print(sep)

    header_line = " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
    print(f"  {header_line}")
    print("-" * total_width)

    for row in rows:
        row_line = " | ".join(str(cell).ljust(col_widths[i]) for i, cell in enumerate(row))
        print(f"  {row_line}")
    print(sep + "\n")


# ---------- PERSISTENCE (uses pathlib, never os) ----------
def load_data():
    if not Path(DATA_FILE).exists():
        return {}
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        for rec in data.values():
            if 'date_added' in rec:
                rec['date_added'] = datetime.fromisoformat(rec['date_added'])
        return data
    except (json.JSONDecodeError, KeyError):
        print("[WARNING] Data file corrupted. Starting with an empty database.")
        return {}


def save_data(households):
    serializable = {}
    for hh_id, rec in households.items():
        copy = rec.copy()
        if 'date_added' in copy:
            copy['date_added'] = copy['date_added'].isoformat()
        serializable[hh_id] = copy
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(serializable, f, indent=2)
    print("[SUCCESS] Data saved to disk.\n")


def generate_id(households):
    if not households:
        return f"{ID_PREFIX}0001"
    max_num = 0
    for hh_id in households:
        if hh_id.startswith(ID_PREFIX):
            try:
                max_num = max(max_num, int(hh_id[len(ID_PREFIX):]))
            except ValueError:
                continue
    return f"{ID_PREFIX}{max_num + 1:04d}"


# ---------- DATA ENTRY ----------
def input_household_data():
    first = input("   Head's First Name: ").strip()
    if not first:
        print("   [ERROR] First name cannot be empty.\n")
        return None

    last = input("   Head's Last Name: ").strip()
    if not last:
        print("   [ERROR] Last name cannot be empty.\n")
        return None

    village = input("   Village / Ward: ").strip()
    if not village:
        print("   [ERROR] Village cannot be empty.\n")
        return None

    try:
        residents = int(input("   Number of residents: "))
        if residents < 1:
            raise ValueError
    except ValueError:
        print("   [ERROR] Must be a positive whole number.\n")
        return None

    while True:
        w = input("   Has clean water? (1=Yes, 0=No): ").strip()
        if w == '1':
            water = True
            break
        if w == '0':
            water = False
            break
        print("   Please enter exactly 1 or 0.")

    while True:
        e = input("   Has electricity? (1=Yes, 0=No): ").strip()
        if e == '1':
            electricity = True
            break
        if e == '0':
            electricity = False
            break
        print("   Please enter exactly 1 or 0.")

    try:
        income = float(input("   Monthly household income (Le): "))
        if income < 0:
            raise ValueError
    except ValueError:
        print("   [ERROR] Enter a valid non‑negative amount.\n")
        return None

    return {
        "first": first,
        "last": last,
        "village": village,
        "residents": residents,
        "water": water,
        "electricity": electricity,
        "income": income,
        "date_added": datetime.now()
    }


# ---------- CORE OPERATIONS ----------
def add_household(households):
    if len(households) >= MAX_HOUSEHOLDS:
        print("\n[ERROR] Database full.\n")
        return

    new_id = generate_id(households)
    print(f"\n--- Adding household {new_id} ---")
    record = input_household_data()
    if record is None:
        print("[CANCELLED] Record not added.\n")
        return
    households[new_id] = record
    print(f"[SUCCESS] {new_id} – {record['first']} {record['last']} added.\n")


def view_all(households):
    if not households:
        print("\n[INFO] No records.\n")
        return

    headers = ["ID", "Head Name", "Village", "Res", "Water", "Elec", "Income (Le)", "Added on"]
    rows = []
    for hh_id, data in households.items():
        water = "Yes" if data['water'] else "No"
        elec = "Yes" if data['electricity'] else "No"
        date_str = data['date_added'].strftime("%Y-%m-%d") if 'date_added' in data else "N/A"
        rows.append([
            hh_id,
            f"{data['first']} {data['last']}",
            data['village'],
            str(data['residents']),
            water,
            elec,
            f"{data['income']:,.0f} Le",
            date_str
        ])
    print_table(headers, rows, title="ALL HOUSEHOLD RECORDS")


def search(households):
    if not households:
        print("\n[INFO] No data.\n")
        return

    term = input("Enter ID or part of name: ").strip().lower()
    headers = ["ID", "Name", "Village", "Res", "Water", "Elec", "Income"]
    rows = []
    for hh_id, data in households.items():
        full = f"{data['first']} {data['last']}".lower()
        if term in hh_id.lower() or term in full:
            rows.append([
                hh_id,
                f"{data['first']} {data['last']}",
                data['village'],
                str(data['residents']),
                "Yes" if data['water'] else "No",
                "Yes" if data['electricity'] else "No",
                f"{data['income']:,.0f} Le"
            ])
    if not rows:
        print("\nNo matching records found.\n")
        return
    print_table(headers, rows, title="SEARCH RESULTS")


def edit_record(households):
    if not households:
        print("\n[INFO] No data.\n")
        return

    hh_id = input("Enter household ID to edit: ").strip()
    if hh_id not in households:
        print("\n[ERROR] ID not found.\n")
        return

    rec = households[hh_id]
    print(f"\nEditing {hh_id} – {rec['first']} {rec['last']}".center(50))
    print("(Leave a field blank to keep the current value)\n")

    first = input(f"   First name [{rec['first']}]: ").strip()
    if first: rec['first'] = first
    last = input(f"   Last name [{rec['last']}]: ").strip()
    if last: rec['last'] = last
    village = input(f"   Village [{rec['village']}]: ").strip()
    if village: rec['village'] = village

    res = input(f"   Residents [{rec['residents']}]: ").strip()
    if res:
        try:
            res_i = int(res)
            if res_i > 0:
                rec['residents'] = res_i
            else:
                print("   Must be positive; kept previous value.")
        except ValueError:
            print("   Invalid number; kept previous value.")

    for field, label in [('water', 'Clean water'), ('electricity', 'Electricity')]:
        cur = 1 if rec[field] else 0
        val = input(f"   {label}? (1=Yes, 0=No) [{cur}]: ").strip()
        if val in ('1', '0'):
            rec[field] = (val == '1')

    inc = input(f"   Monthly income (Le) [{rec['income']:,.0f}]: ").strip()
    if inc:
        try:
            inc_f = float(inc)
            if inc_f >= 0:
                rec['income'] = inc_f
            else:
                print("   Negative not allowed; kept previous value.")
        except ValueError:
            print("   Invalid; kept previous value.")

    print("\n[SUCCESS] Record updated.\n")


def delete_record(households):
    if not households:
        print("\n[INFO] No data.\n")
        return
    hh_id = input("Enter household ID to delete: ").strip()
    if hh_id not in households:
        print("\n[ERROR] ID not found.\n")
        return
    rec = households[hh_id]
    confirm = input(f"Delete {hh_id} ({rec['first']} {rec['last']})? (y/n): ").strip().lower()
    if confirm == 'y':
        del households[hh_id]
        print("\n[SUCCESS] Record deleted.\n")
    else:
        print("\nDeletion cancelled.\n")


# ---------- REPORTING ----------
def generate_summary(households):
    if not households:
        print("\n[INFO] No data.\n")
        return
    total = len(households)
    pop = sum(d['residents'] for d in households.values())
    water_count = sum(1 for d in households.values() if d['water'])
    elec_count = sum(1 for d in households.values() if d['electricity'])
    total_income = sum(d['income'] for d in households.values())

    water_pct = (water_count / total) * 100
    elec_pct = (elec_count / total) * 100
    avg_income = total_income / total

    print("\n" + "=" * 55)
    print("COMMUNITY DATA SUMMARY".center(55))
    print("=" * 55)
    print(f"  Total Households:         {total}")
    print(f"  Total Population:         {pop}")
    print(f"  Clean Water Access:       {water_count} ({water_pct:.1f}%)")
    print(f"  Electricity Access:       {elec_count} ({elec_pct:.1f}%)")
    print(f"  Average Monthly Income:   Le {avg_income:,.0f}")
    print("=" * 55)
    if water_pct < 90:
        print("⚠  SDG 6 ALERT: Clean water coverage below 90% target.")
    if elec_pct < 75:
        print("⚠  SDG 7 ALERT: Electricity access below 75% benchmark.")
    print()


def village_summary(households):
    if not households:
        print("\n[INFO] No data.\n")
        return
    villages = {}
    for data in households.values():
        v = data['village']
        if v not in villages:
            villages[v] = {'count':0, 'pop':0, 'water_yes':0, 'elec_yes':0, 'total_income':0.0}
        villages[v]['count'] += 1
        villages[v]['pop'] += data['residents']
        if data['water']: villages[v]['water_yes'] += 1
        if data['electricity']: villages[v]['elec_yes'] += 1
        villages[v]['total_income'] += data['income']

    headers = ["Village", "HHs", "Pop", "Water %", "Elec %", "Avg Income"]
    rows = []
    for v, s in sorted(villages.items()):
        rows.append([
            v,
            str(s['count']),
            str(s['pop']),
            f"{(s['water_yes']/s['count'])*100:.1f}%",
            f"{(s['elec_yes']/s['count'])*100:.1f}%",
            f"Le {s['total_income']/s['count']:,.0f}"
        ])
    print_table(headers, rows, title="VILLAGE‑WISE BREAKDOWN")


def filter_needy(households):
    if not households:
        print("\n[INFO] No data.\n")
        return
    print("\n--- NEEDS ASSESSMENT FILTER ---")
    print("1. Without clean water")
    print("2. Without electricity")
    print("3. Without either service")
    opt = input("Select filter (1/2/3): ").strip()
    if opt not in ('1','2','3'):
        print("\n[ERROR] Invalid option.\n")
        return

    headers = ["ID", "Name", "Village", "Res", "Water", "Elec", "Income"]
    rows = []
    for hh_id, data in households.items():
        no_water = not data['water']
        no_elec = not data['electricity']
        if opt == '1' and not no_water: continue
        if opt == '2' and not no_elec: continue
        if opt == '3' and not (no_water or no_elec): continue

        rows.append([
            hh_id,
            f"{data['first']} {data['last']}",
            data['village'],
            str(data['residents']),
            "NO" if no_water else "YES",
            "NO" if no_elec else "YES",
            f"Le {data['income']:,.0f}"
        ])

    if not rows:
        print("All households meet the selected criteria.\n")
        return
    print_table(headers, rows, title="FILTERED HOUSEHOLDS")


def sort_households(households):
    if not households:
        print("\n[INFO] No data.\n")
        return
    print("\nSort by: income (high→low), name (A→Z), or village (A→Z)")
    key = input("Enter sort key: ").strip().lower()
    if key not in VALID_SORT_KEYS:
        print("[ERROR] Invalid key. Allowed: income, name, village.\n")
        return

    if key == 'income':
        items = sorted(households.items(), key=lambda x: x[1]['income'], reverse=True)
    elif key == 'name':
        items = sorted(households.items(), key=lambda x: (x[1]['last'].lower(), x[1]['first'].lower()))
    else:
        items = sorted(households.items(), key=lambda x: x[1]['village'].lower())

    headers = ["ID", "Name", "Village", "Income"]
    rows = []
    for hh_id, data in items:
        rows.append([
            hh_id,
            f"{data['first']} {data['last']}",
            data['village'],
            f"Le {data['income']:,.0f}"
        ])
    print_table(headers, rows, title="SORTED LIST")


# ---------- SUB‑MENU ----------
def reporting_menu(households):
    while True:
        clear_screen()
        print("-" * 45)
        print("REPORTING MENU".center(45))
        print("-" * 45)
        print(" 1. Overall Summary")
        print(" 2. Village Breakdown")
        print(" 3. Needs Assessment Filter")
        print(" 4. Sort Households")
        print(" 5. Return to Main Menu")
        print("-" * 45)

        choice = input("Enter your choice: ").strip()
        if choice == '1':
            generate_summary(households)
            wait_for_enter()
        elif choice == '2':
            village_summary(households)
            wait_for_enter()
        elif choice == '3':
            filter_needy(households)
            wait_for_enter()
        elif choice == '4':
            sort_households(households)
            wait_for_enter()
        elif choice == '5':
            break
        else:
            print("Invalid option.")
            wait_for_enter()


# ---------- MAIN PROGRAM ----------
def main():
    households = load_data()
    print(f"\n   Community Connect loaded. Total households: {len(households)}")
    input("\nPress Enter to start...")

    while True:
        clear_screen()
        print("=" * 45)
        print("       COMMUNITY CONNECT".center(45))
        print("=" * 45)
        print(" 1. Add Household")
        print(" 2. View All Households")
        print(" 3. Search Household")
        print(" 4. Edit Household")
        print(" 5. Delete Household")
        print(" 6. Reports & Analysis")
        print(" 7. Save Data to File")
        print(" 8. Exit (auto‑saves)")
        print("=" * 45)

        choice = input("Enter your choice (1-8): ").strip()

        if choice == '1':
            add_household(households)
            wait_for_enter()
        elif choice == '2':
            view_all(households)
            wait_for_enter()
        elif choice == '3':
            search(households)
            wait_for_enter()
        elif choice == '4':
            edit_record(households)
            wait_for_enter()
        elif choice == '5':
            delete_record(households)
            wait_for_enter()
        elif choice == '6':
            reporting_menu(households)
        elif choice == '7':
            save_data(households)
            wait_for_enter()
        elif choice == '8':
            save_data(households)
            print("\nExiting Community Connect. Goodbye!\n")
            break
        else:
            print("Invalid choice. Enter a number between 1 and 8.")
            wait_for_enter()


if __name__ == "__main__":
    main()