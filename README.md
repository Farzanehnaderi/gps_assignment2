## 🛰️ Project Overview
This project processes GPS RINEX navigation files (version 3.04) to compute and visualize satellite positions and trajectories in ECEF coordinates. Developed for the *Satellite Positioning* course at University of Tehran, it calculates satellite positions at 30-second intervals and provides both CSV outputs and 3D trajectory visualizations.

Key Features:
- RINEX 3.04 navigation file parser
- Keplerian orbit parameter processing
- ECEF position computation
- CSV data export
- 3D trajectory visualization
- Command-line and GUI interfaces

---

## 📦 Requirements & Installation

### Dependencies
```bash
Python 3.8+
numpy
matplotlib
PyQt5 (for GUI)
```

### Installation
```bash
git clone https://github.com/Farzanehnaderi/gps_assignment2.git
cd gps_assignment2
pip install -r requirements.txt
```

---

## 🚀 Usage

### Command-Line Interface (CLI)
```bash
python gps_navigation.py
```
1. Automatically loads sample file `GODS00USA_R_20240010000_01D_GN.rnx`
2. Lists available PRNs in the file
3. Enter comma-separated PRNs to process (e.g., `G01, G07, G22`)
4. Generates CSV files and 3D plots

### Graphical User Interface (GUI)
```bash
python GUI.py
```

Features:
- Load any RINEX navigation file
- Multi-PRN selection
- Adjustable time step (default: 30s)
- CSV export toggle
- Real-time 3D plotting
- Processing log

---

## 📂 File Structure
```
├── gps_navigation.py       # Core processing logic (CLI)
├── GUI.py                  # PyQt5 graphical interface
├── requirements.txt        # Dependencies
├── sample_data/            # Example RINEX files
│   └── GODS00USA_R_20240010000_01D_GN.rnx
└── outputs/                # Generated CSV/plots
```

---

## 🧠 Technical Implementation

### Processing Pipeline
1. **RINEX File Parsing**:
   - Header detection and skipping
   - PRN-block extraction
   - Ephemeris parameter decoding

2. **Time Conversion**:
   ```python
   def convert_to_gps_seconds(y, m, d, h, mi, s):
       # Julian date calculation
       return ((jd - 2444244.5) * 86400) % (7*86400)
   ```

3. **Orbital Mechanics**:
   - Kepler's equation solver (Newton-Raphson)
   ```python
   def solve_kepler(M, e, tol=1e-12, max_iter=10):
       E = M
       for _ in range(max_iter):
           E_next = E - (E - e*sin(E) - M) / (1 - e*cos(E))
           if abs(E_next - E) < tol:
               break
           E = E_next
       return E
   ```
   - ECEF position computation:
     ```math
     \begin{align*}
     x &= r(\cos u \cos \Omega - \sin u \cos i \sin \Omega) \\
     y &= r(\cos u \sin \Omega + \sin u \cos i \cos \Omega) \\
     z &= r(\sin u \sin i)
     \end{align*}
     ```

4. **Output Generation**:
   - CSV format: `t, x, y, z`
   - 3D Matplotlib visualization

---

## 📊 Sample Output
**CSV Format:**
```csv
t,x,y,z
123456.00000000000,14567823.45,-6789234.12,21678945.67
123486.00000000000,14567985.32,-6789156.87,21678892.31
...
```


## 🛠️ Development Notes

### Key Constants
```python
MU = 3.986005e14          # Earth's gravitational constant
OMEGA_EARTH = 7.2921151467e-5  # Earth rotation rate (rad/s)
```

### Customization Options
1. Change time step in GUI or modify `dt` in CLI
2. Adjust Kepler solver tolerance (`tol` parameter)
3. Extend for GLONASS/Galileo support

---

## 📚 References
1. IS-GPS-200M: GPS Interface Specification
2. RINEX 3.04 Format Specification
3. Hofmann-Wellenhof, B. et al. (2008): *GNSS - Global Navigation Satellite Systems*
4. Montenbruck, O. & Gill, E. (2000): *Satellite Orbits*

---

## 📧 Submission
- **Deadline**: Summer 2025
- **Professor** : Dr.Saeed Farzaneh
- **Submit to**: atoofi_alireza@yahoo.com
- **File format**: `assignment_2.py`
- **Requirements**:
  - Complete working solution
  - Sample output CSV
  - 3D trajectory plot for at least one PRN

---

## 👩‍💻 Developer  
**Farzaneh Naderi**  
Geospatial Engineering, University of Tehran  
810301115  
*"Precision in Orbit, Excellence in Computation"*
