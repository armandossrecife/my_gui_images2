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

O módulo funciona como ponto de composição da aplicação e como fachada de
compatibilidade. Assim, importações anteriores como `gui.MenuWindow` e
`gui.WindowImageViewer` continuam válidas.

### `MenuWindow`

Compõe a janela principal, mantém a lista de imagens e coordena a seleção entre
biblioteca e visualizador.

## Pacote `ui`

### `constants`

Centraliza cores, tipografia, dimensões de miniaturas e limites de renderização.

### `helpers`

Reúne funções puras de formatação, cálculo da grade e escalas de visualização.
Por não dependerem de uma janela Tk, essas funções são testadas isoladamente.

### `theme`

Contém `AppTheme` e `Tooltip`, responsáveis pelo sistema visual compartilhado.

### `download_panel`

#### `DownloadPanel`

Controla o formulário de URL, a thread de download, a fila de eventos, a barra de
progresso e os estados de sucesso, erro e cancelamento.

### `gallery_panel`

#### `GalleryPanel`

Exibe as imagens em uma grade que se reorganiza conforme a largura disponível.
Mantém cache das miniaturas e oferece seleção por mouse ou teclado.

### `image_viewer`

#### `ImageViewerPanel`

Exibe a imagem selecionada com ajuste proporcional, tamanho real, zoom seguro,
barras de rolagem e movimentação por arraste.

### Compatibilidade

`EntradaWindow`, `ViewAllImagesWindow` e `WindowImageViewer` continuam disponíveis
para chamadas da API anterior. As duas primeiras direcionam o usuário para as áreas
equivalentes da janela unificada.
