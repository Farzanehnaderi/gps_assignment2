# =======================
# =======================
#  Farzaneh Naderi 
#  810301115
#  GPS - ASSIGNMENT2
'''The goal of this project is to parse GPS RINEX navigation files
    to compute satellite ECEF positions over time
  and export and visualize their 3D trajectories.'''
# ======================
#  Constants & Imports
# =======================
import re
import numpy as np
import csv
import matplotlib.pyplot as plt
from math import sin, cos, sqrt, atan2
from mpl_toolkits.mplot3d import Axes3D

MU = 3.986005e14  
OMEGA_EARTH = 7.2921151467e-5

# =======================
#  Step 1: File Reading
# =======================
def read_file_lines(filepath):
    with open(filepath, 'r') as file:
        return file.readlines()

# ================================
#  Step 2: Parse RINEX Nav Data
# ================================
def parse_rinex_nav(filepath):
    lines = read_file_lines(filepath)
    while 'END OF HEADER' not in lines[0]:
        lines.pop(0)
    lines.pop(0)  

    fields = [
        'a0','a1','a2','IODC','Crs','deltan','M0',
        'Cuc','e','Cus','sqrt_a','toe','Cic','Omega0','Cis',
        'i0','Crc','omega','Omegadot','idot','L2','week',
        'L2_P','acc','health','TGD','IODC2','trans_time','spare'
    ]

    nav_data = {}
    while len(lines) >= 8:
        block = lines[:8]
        lines = lines[8:]

        prn = block[0][:3].strip()
        if not prn:
            continue

        nav_data.setdefault(prn, [])

        yr = int(block[0][3:8].strip())
        mo = int(block[0][8:11].strip())
        dy = int(block[0][11:14].strip())
        hr = int(block[0][14:17].strip())
        mn = int(block[0][17:20].strip())
        sc = float(block[0][20:23].strip())

        values = []
        for ln in block:
            numbers = re.findall(r'[\-\+]?[0-9\.]+D[\-\+]?[0-9]+', ln)
            values.extend([float(val.replace('D', 'E')) for val in numbers])

        if len(values) < len(fields):
            continue

        entry = dict(zip(fields, values))
        entry.update({'year': yr, 'month': mo, 'day': dy, 'hour': hr, 'minute': mn, 'second': sc})
        nav_data[prn].append(entry)

    return nav_data

# ============================================
#  Step 3: Time Conversion & Time Range Calc
# ============================================
def convert_to_gps_seconds(y, m, d, h, mi, s):
    a = (14 - m) // 12
    y_new = y + 4800 - a
    m_new = m + 12*a - 3
    jd = d + ((153*m_new + 2)//5) + 365*y_new + y_new//4 - y_new//100 + y_new//400 - 32045
    jd += (h - 12)/24 + mi/1440 + s/86400
    return ((jd - 2444244.5) * 86400) % (7*86400)

def get_time_bounds(prn_data):
    toes = [rec['toe'] for rec in prn_data]
    return min(toes), max(toes)

def generate_time_sequence(start, end, dt=30):
    return np.arange(start, end + 1e-9, dt)

# ==================================
#  Step 4: Orbital Calculations
# ==================================
def solve_kepler(M, e, tol=1e-12, max_iter=10):
    E = M
    for _ in range(max_iter):
        E_next = E - (E - e*sin(E) - M) / (1 - e*cos(E))
        if abs(E_next - E) < tol:
            break
        E = E_next
    return E

def compute_positions(records, times):
    results = []
    for t in times:
        eph = min(records, key=lambda r: abs(t - r['toe']))

        a = eph['sqrt_a']**2
        e = eph['e']
        M0 = eph['M0']
        toe = eph['toe']
        delta_n = eph['deltan']

        tk = t - toe
        if tk > 302400: tk -= 604800
        if tk < -302400: tk += 604800

        n0 = sqrt(MU / a**3)
        n = n0 + delta_n
        M = M0 + n * tk
        E = solve_kepler(M, e)
        v = atan2(sqrt(1 - e**2) * sin(E), cos(E) - e)

        phi = v + eph['omega']
        u = phi + eph['Cus'] * sin(2*phi) + eph['Cuc'] * cos(2*phi)
        r = a * (1 - e * cos(E)) + eph['Crs'] * sin(2*phi) + eph['Crc'] * cos(2*phi)
        i = eph['i0'] + eph['idot'] * tk + eph['Cis'] * sin(2*phi) + eph['Cic'] * cos(2*phi)
        Omega = eph['Omega0'] + (eph['Omegadot'] - OMEGA_EARTH) * tk - OMEGA_EARTH * toe

        x_prime = r * cos(u)
        y_prime = r * sin(u)

        x = x_prime * cos(Omega) - y_prime * cos(i) * sin(Omega)
        y = x_prime * sin(Omega) + y_prime * cos(i) * cos(Omega)
        z = y_prime * sin(i)

        results.append((t, x, y, z))

    return results

# =====================================
#  Step 5: CSV Output & Visualization
# =====================================
def write_csv(data, filename):
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['t', 'x', 'y', 'z'])
        for row in data:
            writer.writerow([f"{row[0]:.11f}", row[1], row[2], row[3]])

def plot_3d_trajectory(data, label='Satellite'):
    xs, ys, zs = zip(*[(x, y, z) for _, x, y, z in data])
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.plot(xs, ys, zs, label=label)
    ax.set_xlabel('X (m)')
    ax.set_ylabel('Y (m)')
    ax.set_zlabel('Z (m)')
    ax.set_title(f' {label}')
    ax.legend()
    plt.tight_layout()
    plt.show()

# ===============================
#  Step 6: PRN Processing Logic
# ===============================
def process_single_prn(filepath, prn, store_csv=True, display_plot=True):
    nav = parse_rinex_nav(filepath)
    if prn not in nav:
        print(f" PRN {prn} not found.")
        return

    start, end = get_time_bounds(nav[prn])
    t_list = generate_time_sequence(start, end)
    coords = compute_positions(nav[prn], t_list)

    if store_csv:
        csv_name = f"output_{prn}.csv"
        write_csv(coords, csv_name)
        print(f" Saved: {csv_name}")

    if display_plot:
        plot_3d_trajectory(coords, prn)

    return coords

# ====================================
#  Step 7: CLI Interface for User
# ====================================
def prompt_user_selection(filepath):
    nav_data = parse_rinex_nav(filepath)
    prns = sorted(nav_data.keys())
    print("\n📡 Available PRNs:")
    for i, prn in enumerate(prns, 1):
        print(f" {i:2d}. {prn}")

    selected = input("\nEnter PRN(s) to process (comma-separated): ")
    chosen = [p.strip().upper() for p in selected.split(',') if p.strip().upper() in prns]

    if not chosen:
        print(" No valid PRNs selected.")
    return chosen

# =========================================
#  Step 8: Full Pipeline Runner Function
# =========================================
def run_gps_pipeline(filepath):
    chosen_prns = prompt_user_selection(filepath)
    for prn in chosen_prns:
        print(f"\n Processing {prn}...")
        process_single_prn(filepath, prn)

# MAIN
if __name__ == "__main__":
    rinex_file = "GODS00USA_R_20240010000_01D_GN.rnx"
    run_gps_pipeline(rinex_file)
