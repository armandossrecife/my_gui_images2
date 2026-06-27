import mimetypes
import os
import tempfile
import threading
from datetime import datetime
from urllib.parse import urlparse

import PIL.Image
import requests
from tqdm import tqdm


class DownloadCancelado(Exception):
    pass


class Util:
    EXTENSOES_IMAGEM = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}

    def extrair_nome_extensao_url(self, url):
        try:
            parsed_url = urlparse(url)
            if parsed_url.scheme not in ("http", "https"):
                raise ValueError(f"Protocolo não suportado: {parsed_url.scheme}")

            caminho_arquivo = parsed_url.path
            if not caminho_arquivo:
                raise ValueError("Caminho do arquivo ausente na URL")

            nome_arquivo, extensao = os.path.splitext(os.path.basename(caminho_arquivo))
            extensao = extensao.lower()
            if not nome_arquivo:
                raise ValueError("Nome do arquivo ausente na URL")
            if extensao not in self.EXTENSOES_IMAGEM:
                raise ValueError(
                    "A URL precisa apontar para um arquivo de imagem suportado"
                )

            return nome_arquivo, extensao
        except Exception as ex:
            raise ValueError(str(ex)) from ex

    def criar_nome_unico(self, directory_path, nome_arquivo, extensao):
        os.makedirs(directory_path, exist_ok=True)
        candidatos = [f"{nome_arquivo}{extensao}"]
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
        candidatos.extend(
            f"{nome_arquivo}_{timestamp}_{indice}{extensao}" for indice in range(1, 1001)
        )

        for filename in candidatos:
            filename_path = os.path.join(directory_path, filename)
            try:
                file_descriptor = os.open(
                    filename_path,
                    os.O_CREAT | os.O_EXCL | os.O_WRONLY,
                    0o600,
                )
            except FileExistsError:
                continue

            os.close(file_descriptor)
            return filename

        raise OSError("Não foi possível reservar um nome único para a imagem")

    def list_files_by_date(self, directory_path):
        try:
            if not os.path.isdir(directory_path):
                return []

            file_paths = [
                os.path.join(directory_path, file)
                for file in os.listdir(directory_path)
                if self._is_supported_image_path(os.path.join(directory_path, file))
            ]

            file_info = []
            for file_path in file_paths:
                try:
                    creation_time = os.path.getctime(file_path)
                    creation_datetime = datetime.fromtimestamp(creation_time)
                    file_info.append((file_path, creation_datetime))
                except OSError as e:
                    print(f"Erro ao obter a data de criação de {file_path}: {e}")

            file_info.sort(key=lambda x: x[1])
            return [file_path for file_path, _ in file_info]
        except OSError as e:
            print(f"Erro ao listar arquivos: {e}")
            return []

    def _is_supported_image_path(self, file_path):
        _, extensao = os.path.splitext(file_path)
        return (
            os.path.isfile(file_path)
            and os.path.getsize(file_path) > 0
            and extensao.lower() in self.EXTENSOES_IMAGEM
        )


class Download:
    TAMANHO_MAXIMO = 25 * 1024 * 1024

    def __init__(self, url, path_arquivo, cancel_event=None, tamanho_maximo=None):
        self.url = url
        self.path_arquivo = os.fspath(path_arquivo)
        self.callback = None
        self.cancel_event = cancel_event or threading.Event()
        self.tamanho_maximo = tamanho_maximo or self.TAMANHO_MAXIMO
        self._arquivo_temporario = None

    def set_callback(self, callback):
        self.callback = callback

    def executa(self):
        try:
            print("Aguarde...")
            self._arquivo_temporario = self._criar_arquivo_temporario()
            tamanho_baixado = 0

            with requests.get(self.url, stream=True, timeout=(5, 30)) as response:
                response.raise_for_status()
                self._validar_content_type(response)
                total_size = self._obter_tamanho_informado(response)

                with open(self._arquivo_temporario, "wb") as file:
                    with tqdm(
                        total=total_size,
                        unit="B",
                        unit_scale=True,
                        desc=self.path_arquivo,
                    ) as pbar:
                        for chunk in response.iter_content(chunk_size=64 * 1024):
                            self._verificar_cancelamento()
                            if not chunk:
                                continue

                            tamanho_baixado += len(chunk)
                            if tamanho_baixado > self.tamanho_maximo:
                                raise ValueError(
                                    f"A imagem excede o limite de {self.tamanho_maximo} bytes"
                                )

                            file.write(chunk)
                            pbar.update(len(chunk))
                            if self.callback:
                                self.callback(total_size, pbar.n)

            self._verificar_cancelamento()
            self._validar_arquivo_imagem(self._arquivo_temporario)
            self._verificar_cancelamento()
            os.replace(self._arquivo_temporario, self.path_arquivo)
            self._arquivo_temporario = None
            print(
                f"Download completo. Tamanho: {tamanho_baixado}, "
                f"Arquivo salvo em: {self.path_arquivo}"
            )
            return tamanho_baixado
        except DownloadCancelado:
            raise
        except requests.exceptions.MissingSchema as ex:
            raise Exception(
                "URL inválida. Certifique-se de fornecer uma URL válida."
            ) from ex
        except requests.exceptions.RequestException as e:
            raise Exception(f"Erro na conexão: {e}") from e
        except (OSError, PIL.UnidentifiedImageError, ValueError) as e:
            raise Exception(f"O arquivo baixado não é uma imagem válida: {e}") from e
        finally:
            self._remover_arquivos_incompletos()

    def _criar_arquivo_temporario(self):
        directory_path = os.path.dirname(os.path.abspath(self.path_arquivo))
        filename = os.path.basename(self.path_arquivo)
        file_descriptor, temp_path = tempfile.mkstemp(
            dir=directory_path,
            prefix=f".{filename}.",
            suffix=".part",
        )
        os.close(file_descriptor)
        return temp_path

    def _obter_tamanho_informado(self, response):
        content_length = response.headers.get("content-length")
        if not content_length:
            return 0

        total_size = int(content_length)
        if total_size > self.tamanho_maximo:
            raise ValueError(f"A imagem excede o limite de {self.tamanho_maximo} bytes")
        return total_size

    def _verificar_cancelamento(self):
        if self.cancel_event.is_set():
            raise DownloadCancelado("Download cancelado")

    def _validar_content_type(self, response):
        content_type = response.headers.get("content-type", "").split(";")[0].strip().lower()
        guessed_type, _ = mimetypes.guess_type(self.path_arquivo)
        if content_type and not content_type.startswith("image/"):
            raise ValueError(f"Content-Type inesperado: {content_type}")
        if guessed_type and not guessed_type.startswith("image/"):
            raise ValueError(f"Extensão de arquivo inesperada: {self.path_arquivo}")

    def _validar_arquivo_imagem(self, file_path):
        with PIL.Image.open(file_path) as image:
            image.verify()

    def _remover_arquivos_incompletos(self):
        arquivos = [self._arquivo_temporario]
        try:
            if os.path.exists(self.path_arquivo) and os.path.getsize(self.path_arquivo) == 0:
                arquivos.append(self.path_arquivo)
        except OSError as e:
            print(f"Erro ao verificar arquivo incompleto {self.path_arquivo}: {e}")

        for file_path in arquivos:
            try:
                if file_path and os.path.exists(file_path):
                    os.remove(file_path)
            except OSError as e:
                print(f"Erro ao remover arquivo incompleto {file_path}: {e}")
