import numpy as np

def voltage_divider(v_in, r1, r2):
    """Calculate output voltage of a voltage divider."""
    v_out = v_in * (r2 / (r1 + r2))
    return v_out

def current_divider(i_in, r1, r2):
    """Calculate current through parallel resistors."""
    i1 = i_in * (r2 / (r1 + r2))
    i2 = i_in * (r1 / (r1 + r2))
    return i1, i2

def ohm_law(voltage=None, current=None, resistance=None):
    """Calculate missing value using Ohm's Law."""
    if voltage is None:
        return current * resistance
    elif current is None:
        return voltage / resistance
    elif resistance is None:
        return voltage / current
    else:
        raise ValueError("Provide exactly two parameters")

# Example 1: Simple Series Circuit
print("=== Series Circuit ===")
v_source = 12  # Volts
r1, r2, r3 = 100, 200, 300  # Ohms

r_total = r1 + r2 + r3
i_total = v_source / r_total

print(f"Total Resistance: {r_total} Ω")
print(f"Total Current: {i_total:.3f} A")
print(f"Voltage drops:")
print(f"  V1 = {i_total * r1:.1f} V")
print(f"  V2 = {i_total * r2:.1f} V")
print(f"  V3 = {i_total * r3:.1f} V")

# Example 2: Voltage Divider
print("\n=== Voltage Divider ===")
v_in = 10  # Volts
r1, r2 = 1000, 2000  # Ohms
v_out = voltage_divider(v_in, r1, r2)
print(f"Input: {v_in}V, Output: {v_out:.2f}V")

# Example 3: Mesh Analysis for 2-loop circuit
print("\n=== Mesh Analysis ===")
# Circuit: V1--R1--(Node)--R2--V2
#                |
#                R3
#                |
#               GND

# Matrix solution: [R] * [I] = [V]
# Loop 1: (R1+R3)*I1 - R3*I2 = V1
# Loop 2: -R3*I1 + (R2+R3)*I2 = -V2

R1, R2, R3 = 10, 20, 5  # Ohms
V1, V2 = 12, 5  # Volts

# Coefficient matrix
R = np.array([[R1 + R3, -R3],
              [-R3, R2 + R3]])
# Voltage vector
V = np.array([V1, -V2])

currents = np.linalg.solve(R, V)
print(f"Mesh currents:")
print(f"  I1 = {currents[0]:.3f} A")
print(f"  I2 = {currents[1]:.3f} A")
