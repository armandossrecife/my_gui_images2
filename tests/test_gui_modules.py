import unittest

import gui
from ui.download_panel import DownloadPanel
from ui.gallery_panel import GalleryPanel
from ui.image_viewer import ImageViewerPanel
from ui.theme import AppTheme


class PublicApiCompatibilityTest(unittest.TestCase):
    def test_fachada_gui_preserva_componentes_publicos(self):
        self.assertIs(gui.AppTheme, AppTheme)
        self.assertIs(gui.DownloadPanel, DownloadPanel)
        self.assertIs(gui.GalleryPanel, GalleryPanel)
        self.assertIs(gui.ImageViewerPanel, ImageViewerPanel)

    def test_adaptadores_da_api_anterior_continuam_disponiveis(self):
        self.assertTrue(hasattr(gui, "EntradaWindow"))
        self.assertTrue(hasattr(gui, "ViewAllImagesWindow"))
        self.assertTrue(hasattr(gui, "WindowImageViewer"))


if __name__ == "__main__":
    unittest.main()
