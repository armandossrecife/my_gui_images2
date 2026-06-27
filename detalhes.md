# Estrutura da aplicação

## Módulo `entidades`

### `Util`

- Extrai nome e extensão de URLs válidas.
- Reserva nomes de arquivos sem colisões.
- Lista imagens suportadas por data.

### `Download`

- Baixa a imagem em uma thread coordenada pela interface.
- Publica o arquivo somente depois da validação.
- Informa progresso por callback.
- Impõe o limite de 25 MiB e remove arquivos incompletos.
- Responde a solicitações de cancelamento.

## Módulo `gui`

### `AppTheme`

Configura cores, tipografia, espaçamento e estados dos componentes `ttk`.

### `MenuWindow`

Compõe a janela principal, mantém a lista de imagens e coordena a seleção entre
biblioteca e visualizador.

### `DownloadPanel`

Controla o formulário de URL, a thread de download, a fila de eventos, a barra de
progresso e os estados de sucesso, erro e cancelamento.

### `GalleryPanel`

Exibe as imagens em uma grade que se reorganiza conforme a largura disponível.
Mantém cache das miniaturas e oferece seleção por mouse ou teclado.

### `ImageViewerPanel`

Exibe a imagem selecionada com ajuste proporcional, tamanho real, zoom seguro,
barras de rolagem e movimentação por arraste.

### Compatibilidade

`EntradaWindow`, `ViewAllImagesWindow` e `WindowImageViewer` continuam disponíveis
para chamadas da API anterior. As duas primeiras direcionam o usuário para as áreas
equivalentes da janela unificada.
