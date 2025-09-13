
import gradio as gr
from app import demo as app
import os

_docs = {'CreditsPanel': {'description': 'A Gradio component for displaying credits with customizable visual effects, such as scrolling or Star Wars-style animations.\nSupports displaying a logo, licenses, and configurable text styling.\n\n    EVENTS (list): Supported events for the component, currently only `change`.', 'members': {'__init__': {'value': {'type': 'Any', 'default': 'None', 'description': None}, 'credits': {'type': 'typing.Union[\n    typing.List[typing.Dict[str, str]],\n    typing.Callable,\n    NoneType,\n][\n    typing.List[typing.Dict[str, str]][\n        typing.Dict[str, str][str, str]\n    ],\n    Callable,\n    None,\n]', 'default': 'None', 'description': None}, 'height': {'type': 'int | str | None', 'default': 'None', 'description': None}, 'width': {'type': 'int | str | None', 'default': 'None', 'description': None}, 'licenses': {'type': 'typing.Optional[typing.Dict[str, str | pathlib.Path]][\n    typing.Dict[str, str | pathlib.Path][\n        str, str | pathlib.Path\n    ],\n    None,\n]', 'default': 'None', 'description': None}, 'effect': {'type': '"scroll" | "starwars" | "matrix"', 'default': '"scroll"', 'description': None}, 'speed': {'type': 'float', 'default': '40.0', 'description': None}, 'base_font_size': {'type': 'float', 'default': '1.5', 'description': None}, 'intro_title': {'type': 'str | None', 'default': 'None', 'description': None}, 'intro_subtitle': {'type': 'str | None', 'default': 'None', 'description': None}, 'sidebar_position': {'type': '"right" | "bottom"', 'default': '"right"', 'description': None}, 'logo_path': {'type': 'str | pathlib.Path | None', 'default': 'None', 'description': None}, 'show_logo': {'type': 'bool', 'default': 'True', 'description': None}, 'show_licenses': {'type': 'bool', 'default': 'True', 'description': None}, 'show_credits': {'type': 'bool', 'default': 'True', 'description': None}, 'logo_position': {'type': '"center" | "left" | "right"', 'default': '"center"', 'description': None}, 'logo_sizing': {'type': '"stretch" | "crop" | "resize"', 'default': '"resize"', 'description': None}, 'logo_width': {'type': 'int | str | None', 'default': 'None', 'description': None}, 'logo_height': {'type': 'int | str | None', 'default': 'None', 'description': None}, 'scroll_background_color': {'type': 'str | None', 'default': 'None', 'description': None}, 'scroll_title_color': {'type': 'str | None', 'default': 'None', 'description': None}, 'scroll_name_color': {'type': 'str | None', 'default': 'None', 'description': None}, 'label': {'type': 'str | gradio.i18n.I18nData | None', 'default': 'None', 'description': None}, 'every': {'type': 'float | None', 'default': 'None', 'description': None}, 'inputs': {'type': 'typing.Union[\n    gradio.components.base.Component,\n    typing.Sequence[gradio.components.base.Component],\n    set[gradio.components.base.Component],\n    NoneType,\n][\n    gradio.components.base.Component,\n    typing.Sequence[gradio.components.base.Component][\n        gradio.components.base.Component\n    ],\n    set[gradio.components.base.Component],\n    None,\n]', 'default': 'None', 'description': None}, 'show_label': {'type': 'bool', 'default': 'False', 'description': None}, 'container': {'type': 'bool', 'default': 'True', 'description': None}, 'scale': {'type': 'int | None', 'default': 'None', 'description': None}, 'min_width': {'type': 'int', 'default': '160', 'description': None}, 'interactive': {'type': 'bool | None', 'default': 'None', 'description': None}, 'visible': {'type': 'bool', 'default': 'True', 'description': None}, 'elem_id': {'type': 'str | None', 'default': 'None', 'description': None}, 'elem_classes': {'type': 'list[str] | str | None', 'default': 'None', 'description': None}, 'render': {'type': 'bool', 'default': 'True', 'description': None}, 'key': {'type': 'int | str | tuple[int | str, Ellipsis] | None', 'default': 'None', 'description': None}, 'preserved_by_key': {'type': 'list[str] | str | None', 'default': '"value"', 'description': None}}, 'postprocess': {'value': {'type': 'Any', 'description': None}}, 'preprocess': {'return': {'type': 'typing.Optional[typing.Dict[str, typing.Any]][\n    typing.Dict[str, typing.Any][str, Any], None\n]', 'description': 'Dict[str, Any] | None: The input payload, returned unchanged.'}, 'value': None}}, 'events': {'change': {'type': None, 'default': None, 'description': 'Triggered when the value of the CreditsPanel changes either because of user input (e.g. a user types in a textbox) OR because of a function update (e.g. an image receives a value from the output of an event trigger). See `.input()` for a listener that is only triggered by user input.'}}}, '__meta__': {'additional_interfaces': {}, 'user_fn_refs': {'CreditsPanel': []}}}

abs_path = os.path.join(os.path.dirname(__file__), "css.css")

with gr.Blocks(
    css=abs_path,
    theme=gr.themes.Default(
        font_mono=[
            gr.themes.GoogleFont("Inconsolata"),
            "monospace",
        ],
    ),
) as demo:
    gr.Markdown(
"""
# `gradio_creditspanel`

<div style="display: flex; gap: 7px;">
<a href="https://pypi.org/project/gradio_creditspanel/" target="_blank"><img alt="PyPI - Version" src="https://img.shields.io/pypi/v/gradio_creditspanel"></a>  
</div>

Credits Panel for Gradio UI
""", elem_classes=["md-custom"], header_links=True)
    app.render()
    gr.Markdown(
"""
## Installation

```bash
pip install gradio_creditspanel
```

## Usage

```python
\"\"\"
app.py

This script serves as an interactive demonstration for the custom Gradio component `CreditsPanel`.
It showcases all available features of the component, allowing users to dynamically adjust
properties like animation effects, speed, layout, and styling. The app also demonstrates
how to handle file dependencies (logo, licenses) in a portable way.
\"\"\"

import gradio as gr
from gradio_creditspanel import CreditsPanel
import os

# --- 1. SETUP & DATA PREPARATION ---
# This section prepares all necessary assets and data for the demo.
# It ensures the demo runs out-of-the-box without manual setup.

def setup_demo_files():
    \"\"\"
    Creates necessary directories and dummy files (logo, licenses) for the demo.
    This makes the application self-contained and easy to run.
    \"\"\"
    # Create dummy license files
    os.makedirs("LICENSES", exist_ok=True)
    if not os.path.exists("LICENSES/Apache.txt"):
        with open("LICENSES/Apache.txt", "w") as f:
            f.write("Apache License\nVersion 2.0, January 2004\nhttp://www.apache.org/licenses/...")
    if not os.path.exists("LICENSES/MIT.txt"):
        with open("LICENSES/MIT.txt", "w") as f:
            f.write("MIT License\nCopyright (c) 2025 Author\nPermission is hereby granted...")

    # Create a placeholder logo if it doesn't exist
    os.makedirs("assets", exist_ok=True)
    if not os.path.exists("./assets/logo.webp"):
        with open("./assets/logo.webp", "w") as f:
            f.write("Placeholder WebP logo")

# Initial data for the credits roll
credits_list = [
    {"title": "Project Manager", "name": "Emma Thompson"},
    {"title": "Lead Developer", "name": "John Doe"},
    {"title": "Senior Backend Engineer", "name": "Michael Chen"},
    {"title": "Frontend Developer", "name": "Sarah Johnson"},
    {"title": "UI/UX Designer", "name": "Jane Smith"},
    {"title": "Database Architect", "name": "Alex Ray"},
    {"title": "DevOps Engineer", "name": "Liam Patel"},
    {"title": "Quality Assurance Lead", "name": "Sam Wilson"},
    {"title": "Test Automation Engineer", "name": "Olivia Brown"},
    {"title": "Security Analyst", "name": "David Kim"},
    {"title": "Data Scientist", "name": "Sophie Martinez"},
    {"title": "Machine Learning Engineer", "name": "Ethan Lee"},
    {"title": "API Developer", "name": "Isabella Garcia"},
    {"title": "Technical Writer", "name": "Noah Davis"},
    {"title": "Scrum Master", "name": "Ava Rodriguez"},
]

# Paths to license files
license_paths = {
    "Gradio Framework": "./LICENSES/Apache.txt",
    "This Component": "./LICENSES/MIT.txt"
}

# Default animation speeds for each effect to provide a good user experience
DEFAULT_SPEEDS = {
    "scroll": 40.0,
    "starwars": 80.0,
    "matrix": 40.0
}

# --- 2. GRADIO EVENT HANDLER FUNCTIONS ---
# These functions define the application's interactive logic.

def update_panel(
    effect: str, 
    speed: float, 
    base_font_size: float,
    intro_title: str, 
    intro_subtitle: str, 
    sidebar_position: str,
    show_logo: bool, 
    show_licenses: bool, 
    show_credits: bool, 
    logo_position: str,
    logo_sizing: str, 
    logo_width: str | None, 
    logo_height: str | None,
    scroll_background_color: str | None, 
    scroll_title_color: str | None,
    scroll_name_color: str | None
) -> dict:
    \"\"\"
    Callback function that updates all properties of the CreditsPanel component.
    It takes the current state of all UI controls and returns a gr.update() dictionary.
    \"\"\"
    return gr.update(
        visible=True,
        effect=effect,
        speed=speed,
        base_font_size=base_font_size,
        intro_title=intro_title,
        intro_subtitle=intro_subtitle,
        sidebar_position=sidebar_position,
        show_logo=show_logo,
        show_licenses=show_licenses,
        show_credits=show_credits,
        logo_position=logo_position,
        logo_sizing=logo_sizing,
        logo_width=logo_width,
        logo_height=logo_height,
        scroll_background_color=scroll_background_color,
        scroll_title_color=scroll_title_color,
        scroll_name_color=scroll_name_color,
        value=credits_list  # The list of credits to display
    )

def update_ui_on_effect_change(effect: str) -> tuple[float, float]:
    \"\"\"
    Updates the speed and font size sliders to sensible defaults when the
    animation effect is changed.
    \"\"\"
    font_size = 1.5
    if effect == "starwars":
        font_size = 6.0  # Star Wars effect looks better with a larger font
    
    speed = DEFAULT_SPEEDS.get(effect, 40.0)
    return speed, font_size

# --- 3. GRADIO UI DEFINITION ---
# This section constructs the user interface using gr.Blocks.

with gr.Blocks(theme=gr.themes.Ocean(), title="CreditsPanel Demo") as demo:
    gr.Markdown(
        \"\"\"
        # Interactive CreditsPanel Demo
        Use the sidebar controls to customize the `CreditsPanel` component in real-time.
        \"\"\"
    )

    with gr.Sidebar(position="right"):
        gr.Markdown("### Effects Settings")
        effect_radio = gr.Radio(
            ["scroll", "starwars", "matrix"], label="Animation Effect", value="scroll",
            info="Select the visual style for the credits."
        )
        speed_slider = gr.Slider(
            minimum=5.0, maximum=100.0, step=1.0, value=DEFAULT_SPEEDS["scroll"],
            label="Animation Speed (seconds)", info="Duration of one animation cycle."
        )
        font_size_slider = gr.Slider(
            minimum=1.0, maximum=10.0, step=0.1, value=1.5,
            label="Base Font Size (rem)", info="Controls the base font size."
        )

        gr.Markdown("### Intro Text")
        intro_title_input = gr.Textbox(
            label="Intro Title", value="Gradio", info="Main title for the intro sequence."
        )
        intro_subtitle_input = gr.Textbox(
            label="Intro Subtitle", value="The best UI framework", info="Subtitle for the intro sequence."
        )

        gr.Markdown("### Layout & Visibility")
        sidebar_position_radio = gr.Radio(
            ["right", "bottom"], label="Sidebar Position", value="right",
            info="Place the licenses sidebar on the right or bottom."
        )
        show_logo_checkbox = gr.Checkbox(label="Show Logo", value=True)
        show_licenses_checkbox = gr.Checkbox(label="Show Licenses", value=True)
        show_credits_checkbox = gr.Checkbox(label="Show Credits", value=True)
        gr.Markdown("### Logo Customization")
        logo_position_radio = gr.Radio(
            ["left", "center", "right"], label="Logo Position", value="center"
        )
        logo_sizing_radio = gr.Radio(
            ["stretch", "crop", "resize"], label="Logo Sizing", value="resize"
        )
        logo_width_input = gr.Textbox(label="Logo Width", value="200px")
        logo_height_input = gr.Textbox(label="Logo Height", value="100px")

        gr.Markdown("### Color Settings (Scroll Effect)")
        scroll_background_color = gr.ColorPicker(label="Background Color", value="#000000")
        scroll_title_color = gr.ColorPicker(label="Title Color", value="#FFFFFF")
        scroll_name_color = gr.ColorPicker(label="Name Color", value="#FFFFFF")

    # Instantiate the custom CreditsPanel component with default values
    panel = CreditsPanel(
        credits=credits_list,
        licenses=license_paths,
        effect="scroll",
        height=500,
        speed=DEFAULT_SPEEDS["scroll"],
        base_font_size=1.5,
        intro_title="Gradio",
        intro_subtitle="The best UI framework",
        sidebar_position="right",
        logo_path="./assets/logo.webp",
        show_logo=True,
        show_licenses=True,
        show_credits=True,
        logo_position="center",
        logo_sizing="resize",
        logo_width="200px",
        logo_height="100px",
        scroll_background_color="#000000",
        scroll_title_color="#FFFFFF",
        scroll_name_color="#FFFFFF",
    )

    # List of all input components that should trigger a panel update
    inputs = [
        effect_radio, 
        speed_slider, 
        font_size_slider,
        intro_title_input, 
        intro_subtitle_input,
        sidebar_position_radio, 
        show_logo_checkbox, 
        show_licenses_checkbox,
        show_credits_checkbox,
        logo_position_radio, 
        logo_sizing_radio, 
        logo_width_input, 
        logo_height_input,
        scroll_background_color, 
        scroll_title_color, 
        scroll_name_color
    ]

    # --- 4. EVENT BINDING ---
    # Connect the UI controls to the handler functions.

    # Special event: changing the effect also updates speed and font size sliders
    effect_radio.change(
        fn=update_ui_on_effect_change,
        inputs=effect_radio,
        outputs=[speed_slider, font_size_slider]
    )

    # General event: any change in an input control updates the main panel
    for input_component in inputs:
        input_component.change(
            fn=update_panel,
            inputs=inputs,
            outputs=panel
        )

# --- 5. APP LAUNCH ---
if __name__ == "__main__":
    setup_demo_files()
    demo.launch()
```
""", elem_classes=["md-custom"], header_links=True)


    gr.Markdown("""
## `CreditsPanel`

### Initialization
""", elem_classes=["md-custom"], header_links=True)

    gr.ParamViewer(value=_docs["CreditsPanel"]["members"]["__init__"], linkify=[])


    gr.Markdown("### Events")
    gr.ParamViewer(value=_docs["CreditsPanel"]["events"], linkify=['Event'])




    gr.Markdown("""

### User function

The impact on the users predict function varies depending on whether the component is used as an input or output for an event (or both).

- When used as an Input, the component only impacts the input signature of the user function.
- When used as an output, the component only impacts the return signature of the user function.

The code snippet below is accurate in cases where the component is used as both an input and an output.

- **As input:** Is passed, dict[str, Any] | None: The input payload, returned unchanged.


 ```python
def predict(
    value: typing.Optional[typing.Dict[str, typing.Any]][
    typing.Dict[str, typing.Any][str, Any], None
]
) -> Any:
    return value
```
""", elem_classes=["md-custom", "CreditsPanel-user-fn"], header_links=True)




    demo.load(None, js=r"""function() {
    const refs = {};
    const user_fn_refs = {
          CreditsPanel: [], };
    requestAnimationFrame(() => {

        Object.entries(user_fn_refs).forEach(([key, refs]) => {
            if (refs.length > 0) {
                const el = document.querySelector(`.${key}-user-fn`);
                if (!el) return;
                refs.forEach(ref => {
                    el.innerHTML = el.innerHTML.replace(
                        new RegExp("\\b"+ref+"\\b", "g"),
                        `<a href="#h-${ref.toLowerCase()}">${ref}</a>`
                    );
                })
            }
        })

        Object.entries(refs).forEach(([key, refs]) => {
            if (refs.length > 0) {
                const el = document.querySelector(`.${key}`);
                if (!el) return;
                refs.forEach(ref => {
                    el.innerHTML = el.innerHTML.replace(
                        new RegExp("\\b"+ref+"\\b", "g"),
                        `<a href="#h-${ref.toLowerCase()}">${ref}</a>`
                    );
                })
            }
        })
    })
}

""")

demo.launch()
