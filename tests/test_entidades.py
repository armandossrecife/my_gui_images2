import io
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import PIL.Image

from entidades import Download, DownloadCancelado, Util


class FakeResponse:
    def __init__(self, content, content_type="image/png", content_length=None):
        self.content = content
        self.headers = {"content-type": content_type}
        if content_length is not None:
            self.headers["content-length"] = str(content_length)

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def raise_for_status(self):
        return None

    def iter_content(self, chunk_size):
        for offset in range(0, len(self.content), chunk_size):
            yield self.content[offset : offset + chunk_size]


def criar_png():
    output = io.BytesIO()
    PIL.Image.new("RGB", (2, 2), color="red").save(output, format="PNG")
    return output.getvalue()


class UtilTest(unittest.TestCase):
    def test_reserva_nomes_distintos_em_chamadas_concorrentes(self):
        with TemporaryDirectory() as directory:
            util = Util()

            def reservar(_):
                return util.criar_nome_unico(directory, "foto", ".png")

            with ThreadPoolExecutor(max_workers=8) as executor:
                filenames = list(executor.map(reservar, range(20)))

            self.assertEqual(20, len(set(filenames)))
            self.assertTrue(
                all((Path(directory) / filename).exists() for filename in filenames)
            )


class DownloadTest(unittest.TestCase):
    def test_publica_imagem_somente_apos_validacao(self):
        content = criar_png()
        with TemporaryDirectory() as directory:
            filename = Util().criar_nome_unico(directory, "foto", ".png")
            destination = Path(directory) / filename
            progress_events = []

            with patch(
                "entidades.requests.get",
                return_value=FakeResponse(content, content_length=len(content)),
            ):
                download = Download("https://example.com/foto.png", destination)
                download.set_callback(
                    lambda total, current: progress_events.append((total, current))
                )
                downloaded = download.executa()

            self.assertEqual(len(content), downloaded)
            self.assertEqual(content, destination.read_bytes())
            self.assertEqual((len(content), len(content)), progress_events[-1])
            self.assertFalse(any(Path(directory).glob("*.part")))

    def test_rejeita_download_acima_do_limite(self):
        with TemporaryDirectory() as directory:
            filename = Util().criar_nome_unico(directory, "foto", ".png")
            destination = Path(directory) / filename

            with patch(
                "entidades.requests.get",
                return_value=FakeResponse(b"", content_length=11),
            ):
                with self.assertRaisesRegex(Exception, "excede o limite"):
                    Download(
                        "https://example.com/foto.png",
                        destination,
                        tamanho_maximo=10,
                    ).executa()

            self.assertFalse(destination.exists())

    def test_cancelamento_remove_arquivos_incompletos(self):
        content = criar_png()
        cancel_event = threading.Event()
        cancel_event.set()

        with TemporaryDirectory() as directory:
            filename = Util().criar_nome_unico(directory, "foto", ".png")
            destination = Path(directory) / filename

            with patch(
                "entidades.requests.get",
                return_value=FakeResponse(content, content_length=len(content)),
            ):
                with self.assertRaises(DownloadCancelado):
                    Download(
                        "https://example.com/foto.png",
                        destination,
                        cancel_event=cancel_event,
                    ).executa()

            self.assertFalse(destination.exists())
            self.assertFalse(
                any(path.name.endswith(".part") for path in Path(directory).iterdir())
            )


if __name__ == "__main__":
    unittest.main()
