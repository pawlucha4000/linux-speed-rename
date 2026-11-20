import datetime as dt
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from mehrfach_umbenennen import engine as E  # noqa: E402

T = dt.datetime(2026, 10, 3, 14, 5, 9)


class ExpandTest(unittest.TestCase):
    def x(self, mask, base="Strombezug_2026", ext="pdf", counter="7"):
        return E.expand(mask, base, ext, counter, T, "Ordner")

    def test_tokens(self):
        self.assertEqual(self.x("[N]"), "Strombezug_2026")
        self.assertEqual(self.x("[N1-5]"), "Strom")
        self.assertEqual(self.x("[N3]"), "r")
        self.assertEqual(self.x("[N12-]"), "2026")
        self.assertEqual(self.x("[N-4]"), "2026")
        self.assertEqual(self.x("[E]"), "pdf")
        self.assertEqual(self.x("[YMD] [hms]"), "2026-10-03 14-05-09")
        self.assertEqual(self.x("[Y]-[M] Foto [C]"), "2026-10 Foto 7")
        self.assertEqual(self.x("[P]"), "Ordner")
        self.assertEqual(self.x("[X] [n]"), "[X] [n]")  # Unbekanntes bleibt stehen


class ComputeTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = self.tmp.name
        self.files = []
        for n in ["IMG_0001.JPG", "IMG_0002.JPG", "IMG_0003.JPG"]:
            p = os.path.join(self.d, n)
            open(p, "w").close()
            self.files.append(p)

    def tearDown(self):
        self.tmp.cleanup()

    def names(self, entries):
        return [e.new_name for e in entries]

    def test_photo_example(self):
        s = E.Settings(name_mask="2026-10 Foto [C]", ext_mask="[E]", counter_digits=3, case=0)
        self.assertEqual(self.names(E.compute(self.files, s)),
                         ["2026-10 Foto 001.JPG", "2026-10 Foto 002.JPG", "2026-10 Foto 003.JPG"])

    def test_counter_start_step(self):
        s = E.Settings(name_mask="[C]", counter_start=10, counter_step=5, counter_digits=2)
        self.assertEqual(self.names(E.compute(self.files, s)), ["10.JPG", "15.JPG", "20.JPG"])

    def test_lower_ext_and_replace(self):
        s = E.Settings(name_mask="[N]", ext_mask="[E]", search="IMG_", replace="Bild ", case=1)
        self.assertEqual(self.names(E.compute(self.files, s)),
                         ["bild 0001.jpg", "bild 0002.jpg", "bild 0003.jpg"])

    def test_regex(self):
        s = E.Settings(search=r"IMG_0*(\d+)", replace=r"Nr \1", regex=True)
        self.assertEqual(self.names(E.compute(self.files, s)), ["Nr 1.JPG", "Nr 2.JPG", "Nr 3.JPG"])

    def test_bad_regex_is_error_not_crash(self):
        s = E.Settings(search="(", regex=True)
        self.assertTrue(E.has_errors(E.compute(self.files, s)))

    def test_duplicates_flagged(self):
        s = E.Settings(name_mask="gleich")
        self.assertTrue(all(e.error for e in E.compute(self.files, s)))

    def test_existing_foreign_file_flagged(self):
        open(os.path.join(self.d, "fremd.JPG"), "w").close()
        s = E.Settings(name_mask="fremd")
        entries = E.compute(self.files[:1], s)
        self.assertEqual(entries[0].error, "Datei existiert bereits")

    def test_execute_swap_and_undo(self):
        # Tausch: 0001 <-> 0002 geht nur über temporäre Namen
        a, b = self.files[0], self.files[1]
        with open(a, "w") as f:
            f.write("A")
        entries = [E.Entry(a, "IMG_0002.JPG"), E.Entry(b, "IMG_0001.JPG")]
        E._check_conflicts(entries)
        self.assertFalse(E.has_errors(entries))
        os.environ["XDG_DATA_HOME"] = self.d + "/data"
        done = E.execute(entries)
        E.save_journal(done)
        with open(b) as f:
            self.assertEqual(f.read(), "A")
        E.undo_last()
        with open(a) as f:
            self.assertEqual(f.read(), "A")
        self.assertEqual(sorted(os.listdir(self.d)), ["IMG_0001.JPG", "IMG_0002.JPG", "IMG_0003.JPG", "data"])

    def test_unchanged_is_fine(self):
        s = E.Settings()
        entries = E.compute(self.files, s)
        self.assertFalse(E.has_errors(entries))
        self.assertEqual(E.execute(entries), [])


if __name__ == "__main__":
    unittest.main()
