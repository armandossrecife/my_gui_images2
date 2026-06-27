import unittest

from ui.helpers import (
    calculate_fit_scale,
    calculate_grid_columns,
    calculate_safe_zoom_limit,
    format_bytes,
)


class FormatBytesTest(unittest.TestCase):
    def test_formata_bytes_e_unidades_binarias(self):
        self.assertEqual("512 B", format_bytes(512))
        self.assertEqual("2.0 KiB", format_bytes(2048))
        self.assertEqual("3.0 MiB", format_bytes(3 * 1024 * 1024))


class ResponsiveLayoutTest(unittest.TestCase):
    def test_grade_sempre_tem_ao_menos_uma_coluna(self):
        self.assertEqual(1, calculate_grid_columns(0))
        self.assertEqual(1, calculate_grid_columns(175))
        self.assertEqual(2, calculate_grid_columns(352))

    def test_ajuste_preserva_proporcao_sem_ampliar(self):
        self.assertEqual(0.5, calculate_fit_scale((1000, 500), (500, 500)))
        self.assertEqual(1.0, calculate_fit_scale((100, 100), (500, 500)))

    def test_ajuste_pode_ampliar_quando_solicitado(self):
        self.assertEqual(
            5.0,
            calculate_fit_scale(
                (100, 100),
                (500, 600),
                allow_upscale=True,
            ),
        )

    def test_limite_de_zoom_protege_contra_renderizacao_excessiva(self):
        limit = calculate_safe_zoom_limit((6000, 4000), max_pixels=36_000_000)
        self.assertAlmostEqual((36_000_000 / 24_000_000) ** 0.5, limit)
        self.assertEqual(4.0, calculate_safe_zoom_limit((100, 100)))


if __name__ == "__main__":
    unittest.main()
