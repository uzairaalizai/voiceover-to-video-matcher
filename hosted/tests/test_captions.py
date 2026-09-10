import importlib.util
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from engine import make_captions,align_script


class CaptionTests(unittest.TestCase):
    def test_exact_script_fixes_names_and_preserves_interval(self):
        words=[dict(word=w,start=i,end=i+1) for i,w in enumerate('Andy Sippewitch stayed on the show'.split())]
        result=align_script([dict(words=words)],'Andy Sipowicz stayed on the show')[0]['words']
        self.assertEqual(result[1],dict(word='Sipowicz',start=1,end=2))

    def test_adjacent_caption_groups_never_overlap(self):
        with tempfile.TemporaryDirectory() as path:
            directory=pathlib.Path(path)
            words=[dict(word=f'word{i}',start=i*.4,end=(i+1)*.4) for i in range(11)]
            make_captions(directory,[dict(start=0,end=4.4,words=words)],{'captions':True,'graphics':False},360,640)
            events=[line.split(',') for line in (directory/'captions.ass').read_text().splitlines() if line.startswith('Dialogue')]
            def sec(value):
                h,m,s=value.split(':');return int(h)*3600+int(m)*60+float(s)
            for first,second in zip(events,events[1:]):
                self.assertLessEqual(sec(first[2]),sec(second[1]))
