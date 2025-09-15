# tests/test_zener_diode.py

import unittest

import numpy as np

from semiconductor_sim import ZenerDiode


class TestZenerDiode(unittest.TestCase):
    def test_saturation_current(self):
        diode = ZenerDiode(doping_p=1e17, doping_n=1e17, zener_voltage=5.0, temperature=300)
        self.assertGreater(diode.I_s, 0, "Saturation current should be positive")

    def test_iv_characteristic_length(self):
        diode = ZenerDiode(doping_p=1e17, doping_n=1e17, zener_voltage=5.0, temperature=300)
        voltage = np.array([0.0, 5.0, 6.0])
        current, recombination = diode.iv_characteristic(voltage, n_conc=1e16, p_conc=1e16)
        self.assertEqual(len(current), len(voltage), "Current array length mismatch")
        self.assertEqual(len(recombination), len(voltage), "Recombination array length mismatch")

    def test_zener_breakdown(self):
        diode = ZenerDiode(doping_p=1e17, doping_n=1e17, zener_voltage=5.0, temperature=300)
        voltage = np.array([4.5, 5.0, 5.5])
        current, recombination = diode.iv_characteristic(voltage, n_conc=1e16, p_conc=1e16)
        self.assertGreater(current[2], current[1], "Current should increase after Zener breakdown")

    def test_negative_voltage(self):
        diode = ZenerDiode(doping_p=1e17, doping_n=1e17, zener_voltage=5.0, temperature=300)
        voltage = np.array([-0.5, -1.0, -1.5])
        current, recombination = diode.iv_characteristic(voltage, n_conc=1e16, p_conc=1e16)
        self.assertTrue(np.all(current < 0), "Current should be negative for reverse bias")


if __name__ == '__main__':
    unittest.main()
