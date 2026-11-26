
import re

# Measurement units that require a space between the number and unit.
UNITS_REQUIRING_SPACE = [
    "mm",
    "cm",
    "m",
    "kg",
    "g",
    "V",
    "A",
    "W",
    "kW",
    "Hz",
    "kHz",
    "MHz",
    "°C",
]

def check_measurement_spacing(text):
    """Find measurement values written without a space before the unit."""
    issues = []

    for unit in UNITS_REQUIRING_SPACE:
        pattern = rf"(?<![\w.])(\d+(?:\.\d+)?){re.escape(unit)}\b"

        for match in re.finditer(pattern, text):
            issues.append(
                {
                    "value": match.group(),
                    "preferred": f"{match.group(1)} {unit}",
                    "position": match.start(),
                }
            )

    return issues
