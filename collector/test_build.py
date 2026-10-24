"""Offline tests: python3 -m unittest discover -s collector -v"""
import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build  # noqa: E402
import classify as C  # noqa: E402


class TestRelevance(unittest.TestCase):
    def test_core(self):
        for t in ("22.7 A 14b 4.6GS/s RF DAC in 0.18μm CMOS for cable head-end systems",
                  "A 113-dB SNR oversampling DAC with segmented noise-shaped scrambling",
                  "A −117.1-dB THD Audio DAC Utilizing Single Vector Quantizer for Simultaneous Mismatch and ISI Shaping",
                  "Delta–Sigma D/A Converter Using Binary-Weighted Digital-to-Analog Differentiator"):
            self.assertEqual(C.relevance(t, ""), "core", t)

    def test_dacs_inside_adcs_are_out(self):
        for t in ("A 0.024mm2 8b 400MS/s SAR ADC with 2b/cycle and resistive DAC in 65nm CMOS",
                  "An 80 MHz CT DSM With SMASH DAC Achieving 106.2 dB SFDR Without Linearity Calibration",
                  "A 28-nm SRAM Compute-In-Memory Macro With In-SRAM DAC/ADC Operations"):
            self.assertIsNone(C.relevance(t, ""), t)

    def test_dac_in_a_transmitter_is_related(self):
        self.assertEqual(C.relevance("10-to-112-Gb/s DSP-DAC-Based Transmitter in 7-nm FinFET", ""), "related")


class TestSpecs(unittest.TestCase):
    def test_title(self):
        s = C.parse_specs("22.7 A 14b 4.6GS/s RF DAC in 0.18μm CMOS for cable head-end systems", "")
        self.assertEqual((s["res"], s["fs"], s["node"]), (14, 4.6e9, 180))

    def test_abstract(self):
        s = C.parse_specs("A current-steering DAC", "The 12-bit DAC achieves an SFDR of 72 dBc and consumes 45 mW in 28-nm CMOS.")
        self.assertEqual((s["res"], s["sfdr"], s["p"], s["node"]), (12, 72.0, 0.045, 28))
        self.assertAlmostEqual(C.derived({"p": 0.045, "fs": 1e9})["e"], 45e-12)

    def test_several_values_are_left_out(self):
        s = C.parse_specs("A DAC", "SFDR is 70 dBc at 100 MHz and 55 dBc at 1 GHz.")
        self.assertNotIn("sfdr", s)
        s = C.parse_specs("A 75-dB-SFDR DAC", "SFDR is 75 dBc at 100 MHz and 55 dBc at 1 GHz.")
        self.assertEqual(s["sfdr"], 75.0)

    def test_type(self):
        self.assertEqual(C.dac_type("A 113-dB SNR oversampling DAC", ""), "Oversampling")
        self.assertEqual(C.dac_type("A 14b 4.6GS/s RF DAC", ""), "Nyquist")


class TestBuild(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.cache = os.path.join(self.tmp, "cache")
        os.makedirs(self.cache)
        self._papers, self._meta = build.PAPERS, build.META
        build.PAPERS = os.path.join(self.tmp, "papers.json")
        build.META = os.path.join(self.tmp, "meta.json")

    def tearDown(self):
        build.PAPERS, build.META = self._papers, self._meta
        shutil.rmtree(self.tmp)

    def put(self, n, title, pub, abstract="", year=2025):
        with open(os.path.join(self.cache, "%d.json" % n), "w", encoding="utf-8") as f:
            json.dump({"article_number": n, "title": title, "publication_title": pub, "abstract": abstract,
                       "publication_year": year, "publication_date": "Feb. %d" % year, "doi": "10.1109/x.%d" % n,
                       "authors": {"authors": [{"full_name": "A. Kim", "author_order": 1,
                                                "affiliation": "KAIST, Daejeon, South Korea"}]}}, f)

    def test_rebuild(self):
        config = build.load_json(build.CONFIG, None)
        self.put(1, "A 14b 4.6GS/s RF DAC", "IEEE Journal of Solid-State Circuits", "It consumes 460 mW in 28-nm CMOS.")
        self.put(2, "A 12-b SAR ADC with a capacitive DAC", "IEEE Journal of Solid-State Circuits")
        self.put(3, "A 10-GS/s Time-Interleaved DAC", "2025 IEEE Custom Integrated Circuits Conference (CICC)")
        self.put(4, "A DAC", "Some Other Conference")
        meta = build.rebuild(config, self.cache, "2026-10-24")
        papers = {p["id"]: p for p in build.load_json(build.PAPERS, [])}
        self.assertEqual(set(papers), {"1", "3"})
        p = papers["1"]
        self.assertEqual((p["v"], p["ty"], p["cn"], p["s"]["p"]), ("JSSC", "Nyquist", ["South Korea"], 0.46))
        self.assertAlmostEqual(p["x"]["e"], 1e-10)
        self.assertNotIn("abstract", json.dumps(list(papers.values())))
        self.assertEqual(meta["core"], 2)


if __name__ == "__main__":
    unittest.main()
