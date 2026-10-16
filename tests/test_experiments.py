import unittest
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import numpy as np

from image_lab import experiments as ops
from image_lab.experiment_ui import ExperimentMixin


class ExperimentTests(unittest.TestCase):
    def test_diagonal_and_area(self):
        mask = np.zeros((20, 20), np.uint8)
        mask[2:6, 2:6] = 255
        mask[6:10, 6:10] = 255
        self.assertEqual(ops.components(mask, 4)['count'], 2)
        self.assertEqual(ops.components(mask, 8)['count'], 1)
        mask[18, 18] = 255
        result = ops.components(mask, 8, 2)
        self.assertEqual((result['raw_count'], result['count']), (2, 1))

    def test_noise_and_median(self):
        mask = np.zeros((100, 100), np.uint8)
        mask[20:80, 20:80] = 255
        noisy = ops.salt_pepper(mask, .02, 10)
        np.testing.assert_array_equal(noisy, ops.salt_pepper(mask, .02, 10))
        clean = ops.smooth(noisy, 'median', 3)
        self.assertGreater(ops.components(noisy)['count'], 1)
        self.assertEqual(ops.components(clean)['count'], 1)
        np.testing.assert_array_equal(mask, ops.gaussian_noise(mask, 0))
        self.assertTrue(np.isin(ops.segment(ops.gaussian_noise(mask))[1], [0, 255]).all())

    def test_chain_closes(self):
        mask = np.zeros((20, 20), np.uint8)
        mask[4:12, 6:14] = 255
        result = ops.components(mask)
        chain = ops.chain_code(result['labels'], 1)
        offsets = np.array([(1, 0), (1, -1), (0, -1), (-1, -1),
                            (-1, 0), (-1, 1), (0, 1), (1, 1)])
        np.testing.assert_array_equal(offsets[chain['code']].sum(axis=0), [0, 0])
        self.assertEqual(chain['steps'], 28)
        self.assertEqual(ops.components(np.zeros((10, 10), np.uint8))['count'], 0)
        self.assertEqual(ops.components(np.full((10, 10), 255, np.uint8))['count'], 1)

    def test_logic_and_relations(self):
        a = np.array([[0, 0, 255, 255]], np.uint8)
        b = np.array([[0, 255, 0, 255]], np.uint8)
        np.testing.assert_array_equal(ops.logical(a, b, 'AND'), [[0, 0, 0, 255]])
        np.testing.assert_array_equal(ops.logical(a, b, 'OR'), [[0, 255, 255, 255]])
        np.testing.assert_array_equal(ops.logical(a, b, 'XOR'), [[0, 255, 255, 0]])
        np.testing.assert_array_equal(ops.logical(a, operation='NOT'), 255-a)
        np.testing.assert_array_equal(ops.relational(a, '==', 0), 255-a)
        with self.assertRaises(ValueError):
            ops.logical(a, b.T)

    def test_dark_segmentation_and_stages(self):
        photo = np.full((60, 60, 3), 225, np.uint8)
        photo[10:30, 10:30] = 25
        p = dict(method='otsu', threshold=127, dark=True, amount=.02,
                 sigma=20, mean=0, seed=2026, kernel=3, area=1)
        controller = ExperimentMixin()
        stages = controller._noise_stages(photo, p)
        self.assertEqual(len(stages), 5)
        self.assertEqual(ops.components(stages[0][1])['count'], 1)
        self.assertEqual(stages[0][1][0, 0], 0)
        self.assertEqual(stages[0][1][15, 15], 255)
        # Máscaras existentes no deben volver a invertirse al contar.
        np.testing.assert_array_equal(controller._mask(stages[0][1], p), stages[0][1])

    def test_actions_use_history(self):
        controller = ExperimentMixin()
        controller.current_image = np.array([[10, 200]], np.uint8)
        controller.require_image = lambda: True
        controller._experiment_params = lambda: dict(method='fixed', threshold=100, dark=False)
        commits = []
        controller.commit = lambda image, description: commits.append((image, description))
        controller.segment_current()
        np.testing.assert_array_equal(commits[0][0], [[0, 255]])

    def test_export(self):
        controller = ExperimentMixin()
        mask = np.zeros((5, 5), np.uint8)
        rows = [dict(stage='base', connectivity=8, raw_count=0, count=0, min_area=1)]
        with TemporaryDirectory() as target:
            with patch('image_lab.experiment_ui.filedialog.askdirectory', return_value=target), \
                    patch('image_lab.experiment_ui.messagebox.showinfo'):
                controller._export_ecc({'seed': 42}, rows, [('base', mask)], {}, None)
            folder = next(Path(target).iterdir())
            self.assertTrue((folder / 'conteos.csv').is_file())
            self.assertTrue((folder / 'imagen_000.png').is_file())
            self.assertEqual(json.loads((folder / 'parametros.json').read_text())['seed'], 42)
            self.assertEqual(json.loads((folder / 'imagenes.json').read_text())[0]['description'], 'base')


if __name__ == '__main__':
    unittest.main()
