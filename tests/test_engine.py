import argparse
import tempfile
import unittest
from pathlib import Path
from netbrain_lookup import engine

class LookupTests(unittest.TestCase):
    def test_cli_aliases(self):
        self.assertEqual(engine.parse_args(["--host","192.0.2.1"]).host,"192.0.2.1")
        self.assertEqual(engine.parse_args(["--host-file","hosts.txt"]).hosts_file,"hosts.txt")
        self.assertEqual(engine.parse_args(["-hf","hosts.txt"]).hosts_file,"hosts.txt")
        self.assertEqual(engine.parse_args(["-ho","192.0.2.1"]).host,"192.0.2.1")

    def test_mac_normalization(self):
        variants = ["aa:bb:cc:dd:ee:ff", "AABB.CCDD.EEFF", "aa-bb-cc-dd-ee-ff", "aabbccddeeff"]
        self.assertEqual(len({engine.normalize_mac(v) for v in variants}),1)

    def test_input_deduplication(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"hosts.txt"
            p.write_text("192.0.2.1\naabb.ccdd.eeff\nAA:BB:CC:DD:EE:FF\ninvalid\n")
            targets=engine.load_targets(p)
            self.assertEqual(len(targets),3)
            self.assertEqual(targets[-1]["type"],"INVALID")

    def test_input_output_collision(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"hosts.csv"
            p.write_text("192.0.2.1")
            args=engine.parse_args(["--url","https://netbrain.example.local","-u","LAB","-hf",str(p),"-o",str(p),"--overwrite"])
            self.assertEqual(engine.main(args),2)
            self.assertEqual(p.read_text(),"192.0.2.1")

    def test_api_status(self):
        with self.assertRaises(engine.NetBrainAPIError):
            engine.validate_status({"statusCode":790400},"test")

    def test_distinct_observations(self):
        a = {"target":"192.0.2.1","target_type":"IP","status":"found","endpoint_ip":"192.0.2.1","switch_name":"LAB-A","source_api":"test","notes":""}
        b = dict(a,switch_name="LAB-B")
        rows = engine.consolidate_observations([a,b])
        self.assertEqual(len(rows),2)
        engine.annotate_matches(rows)
        self.assertEqual(rows[1]["match_count"],"2")
        self.assertEqual(engine.target_summary(rows)["found"],1)

    def test_exact_ip(self):
        rows = [{"ip":"192.0.2.10"},{"ip":"192.0.2.1"}]
        self.assertEqual(engine.filter_target_records(rows,engine.make_target("192.0.2.1")),[rows[1]])

    def test_non_interactive_selection(self):
        from unittest.mock import patch
        with patch.object(engine,"NO_PROMPT",True), patch("builtins.input",side_effect=AssertionError("Prompt forbidden")):
            with self.assertRaises(engine.NetBrainError):
                engine.choose([{"name":"a","id":"1"},{"name":"b","id":"2"}],None,"name","id","domain")
