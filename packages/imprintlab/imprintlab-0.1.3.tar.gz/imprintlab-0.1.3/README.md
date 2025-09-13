# Imprint — Documentação (Português / English)

> Esta documentação contém versões em **Português (PT-BR)** e **English (EN)** do README e guias rápidos para a biblioteca **Imprint**.

---

# Português (PT-BR)

## Imprint

**Imprint** é uma biblioteca Python para criação e geração programática de templates visuais (certificados, crachás, convites e outros), com campos dinâmicos que podem ser preenchidos a partir de APIs, planilhas, bancos de dados ou qualquer fonte de dados.

### ⚡ Principais recursos

* Criação de **templates personalizados** com múltiplas páginas.
* Campos dinâmicos: **texto**, **imagem** e **QR code** (e mais tipos no futuro).
* Definição de **posição, tamanho e dimensões** para cada campo em uma página.
* Exportação para **imagens PNG** e suporte planejado para PDF e outros formatos.
* Integração fácil com **APIs, Excel/CSV e bancos de dados**.
* Arquitetura modular para facilitar adição de novos tipos de campos e motores de render (engines).

### 🚀 Instalação

Quando publicado no PyPI:

```bash
pip install imprintlab
```

Para instalar diretamente do repositório durante desenvolvimento:

```bash
pip install git+https://github.com/danieldevpy/imprint.git
```

### 📝 Exemplo rápido (usage)

```python
import os
from imprint import Model

# Cria um modelo simples com uma página e campos dinâmicos
def criar_cracha_basico():
    caminho_fundo = os.path.join(os.getcwd(), "examples/assets/badge.png")

    modelo = Model.new(name="Cracha-Basico")

    pagina_frente = modelo.new_page(name="frente")
    pagina_frente.set_background(caminho_fundo)

    campo_nome = pagina_frente.add_component(
        name="Nome Completo", component="text", form_key="nome"
    )
    campo_nome.set_position((520, 320))
    campo_nome.set_size(24)

    campo_cargo = pagina_frente.add_component(
        name="Cargo", component="text", form_key="cargo"
    )
    campo_cargo.set_position((510, 400))
    campo_cargo.set_size(24)

    campo_funcao = pagina_frente.add_component(
        name="Função", component="text", form_key="funcao"
    )
    campo_funcao.set_position((610, 480))
    campo_funcao.set_size(24)

    campo_foto = pagina_frente.add_component(
        name="Foto", component="img", form_key="foto"
    )
    campo_foto.set_position((35, 245))
    campo_foto.set_dimension((360, 360))

    return modelo


modelo = criar_cracha_basico()

dados_formulario = {
    "nome": "Daniel Fernandes Pereira",
    "cargo": "Desenvolvedor de Software",
    "funcao": "Administrador",
    "foto": os.path.join(os.getcwd(), "examples/assets/photo.png"),
}

# Construir e renderizar (com o engine Pillow por padrão)
resultado = modelo.build(dados_formulario).render()

# Visualizar no visualizador padrão do sistema
resultado.show()

# Salvar saída (um arquivo, múltiplas páginas ou diretório)
# - Para uma única página:
resultado.save("out/cracha.png")
# - Para múltiplas páginas: cria diretório com páginas PNG ou salva PDF se especificado
resultado.save("out/")

```

### Exemplo obtendo campos do formulário
```python
from examples.cracha_basico import criar_cracha_basico

modelo = criar_cracha_basico()
print(modelo.get_form())
print(modelo.get_schema())

```
> {'name': '', 'job': '', 'role': '', 'photo': ''}

> {'front': {'name': '', 'job': '', 'role': '', 'photo': ''}}


> Observações:
>
> * `Model.new(...)` cria um novo template.
> * `Page` aceita background por caminho de arquivo; caso não use imagem, especifique `width` e `height`.
> * `form_key` associa o componente a uma chave no dicionário `form_data` passado ao `build()`.

### 🔧 Estrutura da API (resumo)

* `Model.new(name: str)` → cria um novo `Model`.
* `Model.new_page(name: str)` → cria e retorna um `Page` ligado ao `Model`.
* `Page.set_background(path_or_none)` → define background (imagem) ou limpa para fundo colorido.
* `Page.add_component(name, component: str, form_key: Optional[str])` → adiciona componente ("text", "img", "qrcode", ...).
* `Model.build(form: dict)` → retorna um `Builder` pronto para render.
* `Builder.render()` → retorna um `BuildResult` (ex.: `ImageBuildResult`).
* `BuildResult.show()` → abre o resultado no visualizador do sistema.
* `BuildResult.save(path)` → salva como PNG(s) ou PDF (dependendo do engine e do caminho).

### 📦 Formatos e engines

* Atualmente a engine padrão é **Pillow** e produz `ImageBuildResult` (PIL.Image objects).
* Planos futuros: engines adicionais (PDF nativo, SVG, HTML/CSS).

### 📌 Boas práticas e dicas

* Use `Field`/`Component` com `form_key` para ligar os campos ao seu dicionário de dados.
* Para imagens, sempre passe caminhos de arquivo válidos ou URIs locais; cuide do tamanho e proporção.
* Ao usar fundo sem imagem, defina `width` e `height` na página para evitar erro.

### 🌟 Contribuições

1. Fork no GitHub.
2. Crie um branch: `git checkout -b feature/nome-da-feature`.
3. Abra um PR com descrição clara do que foi feito.

### 📄 Licença

MIT License © Daniel Fernandes

---

# English (EN)

## Imprint

**Imprint** is a Python library to programmatically create and generate visual templates (certificates, badges, invitations, etc.) with dynamic fields that can be filled from APIs, spreadsheets, databases or any data source.

### ⚡ Features

* Create **custom templates** with multiple pages.
* Dynamic fields: **text**, **image** and **QR code** (more field types planned).
* Define **position, size and dimension** for each field on a page.
* Export to **PNG images**; PDF and other export formats are planned.
* Easy integration with **APIs, Excel/CSV and databases**.
* Modular engine/architecture to allow new render engines and field types.

### 🚀 Installation

When published on PyPI:

```bash
pip install imprintlab
```

To install from the Git repository (development):

```bash
pip install git+https://github.com/danieldevpy/imprint.git
```

### 📝 Quickstart example

```python
import os
from imprint import Model

# Build a simple badge template with dynamic fields
def create_basic_badge():
    background_path = os.path.join(os.getcwd(), "examples/assets/badge.png")

    model = Model.new(name="Basic-Badge")

    front_page = model.new_page(name="front")
    front_page.set_background(background_path)

    full_name_field = front_page.add_component(name="Full Name", component="text", form_key="name")
    full_name_field.set_position((520, 320))
    full_name_field.set_size(24)

    job_field = front_page.add_component(name="Job", component="text", form_key="job")
    job_field.set_position((510, 400))
    job_field.set_size(24)

    role_field = front_page.add_component(name="Role", component="text", form_key="role")
    role_field.set_position((610, 480))
    role_field.set_size(24)

    photo_field = front_page.add_component(name="Photo", component="img", form_key="photo")
    photo_field.set_position((35, 245))
    photo_field.set_dimension((360, 360))

    return model

model = create_basic_badge()

form_data = {
    "name": "Daniel Fernandes Pereira",
    "job": "Software Developer",
    "role": "Administrator",
    "photo": os.path.join(os.getcwd(), "examples/assets/photo.png")
}

# Build and render (Pillow engine by default)
result = model.build(form_data).render()

# Show result using OS default viewer
result.show()

# Save output (single file, multiple pages or directory)
result.save("out/badge.png")
result.save("out/")
```

### Example getting form fields
```python
from examples.basic_cracha import create_basic_badge

model = create_basic_badge()
print(model.get_form())
print(model.get_schema())

```
> {'name': '', 'job': '', 'role': '', 'photo': ''}

> {'front': {'name': '', 'job': '', 'role': '', 'photo': ''}}

### 🔧 API Summary

* `Model.new(name: str)` — create a new `Model`.
* `Model.new_page(name: str)` — create and attach a `Page` to the model.
* `Page.set_background(path_or_none)` — set background image or use plain color background.
* `Page.add_component(name, component, form_key=...)` — add a component ("text", "img", "qrcode").
* `Model.build(form: dict)` — returns a `Builder` instance.
* `Builder.render()` — returns a `BuildResult` (e.g., `ImageBuildResult`).
* `BuildResult.show()` — open with the system viewer.
* `BuildResult.save(path)` — save as PNG(s) or PDF depending on engine and path.

### 📦 Engines & Output

* Default engine: **Pillow**, produces `ImageBuildResult` (PIL.Image objects).
* Future engines planned: PDF native, SVG, HTML/CSS render.

### 📌 Best Practices

* Use `form_key` to map components to data keys in the form dictionary.
* For images, pass valid file paths or local URIs; mind aspect ratios and sizes.
* When not using an image background, specify `width` and `height` for the page.

### 🌟 Contributing

1. Fork the repository.
2. Create a branch: `git checkout -b feature/your-feature`.
3. Open a PR with a clear description and tests/examples.

### 📄 License

MIT License © Daniel Fernandes

---
