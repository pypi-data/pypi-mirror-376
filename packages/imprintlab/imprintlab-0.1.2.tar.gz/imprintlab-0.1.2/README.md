# Imprint

**Imprint** is a Python library for creating and generating visual document templates, such as certificates, badges, invitations, and other graphic templates, in a simple and programmatic way. It allows dynamic fields to be filled from APIs, Excel files, databases, or any data source.

---

## ⚡ Features

* Create **custom templates** with multiple pages.
* Add **dynamic fields**: text, images, and QR codes.
* Define **size and position** for each field on a page.
* Export templates as **PNG images** or other formats.
* Easy integration with **APIs, Excel, and databases**.
* Modular structure for future extensions (new field types and graphical effects).

---

## 🚀 Installation

You can install directly from the repository (when available on PyPI, just replace `git+...` with `pip install imprint`):

```bash
pip install git+https://github.com/your-username/imprint.git
```

---

## 📝 Basic Usage Example

```python
import os
from imprint import Model

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

result = model.build(form_data).make_images()
# to view
result.show()
# to save
result.save("result.png", format="PNG")



# Multiple pages example
results = model.build(form_data).make_images()
for i, page in enumerate(results):
    page.save(f"result-{i}.png", format="PNG")
```

---

## 🔧 Model Structure

* **Model**: represents the complete document, containing multiple pages.
* **Page**: represents each page of the template.
* **Field**: represents dynamic fields that can be filled (text, image, QR code, etc.).
* **Components**: set of available field types.

---

## 🌟 Upcoming Features

* Support for **layers and visual effects**.
* Direct **PDF export**.
* Integration with **Excel and CSV files**.
* Support for **dynamic QR codes** and barcodes.
* Shareable templates via **API**.

---

## 💡 Contributing

1. **Fork** the project.
2. **Create a branch** for your feature:

```bash
git checkout -b feature/new-feature
```

---

## 📄 License

MIT License © Daniel Fernandes
