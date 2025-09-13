"""
app.py

This script serves as an interactive demonstration for the custom Gradio component `CreditsPanel`.
It showcases all available features of the component, allowing users to dynamically adjust
properties like animation effects, speed, layout, and styling. The app also demonstrates
how to handle file dependencies (logo, licenses) in a portable way.
"""

import gradio as gr
from gradio_creditspanel import CreditsPanel
import os

# --- 1. SETUP & DATA PREPARATION ---
# This section prepares all necessary assets and data for the demo.
# It ensures the demo runs out-of-the-box without manual setup.

def setup_demo_files():
    """
    Creates necessary directories and dummy files (logo, licenses) for the demo.
    This makes the application self-contained and easy to run.
    """
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
    """
    Callback function that updates all properties of the CreditsPanel component.
    It takes the current state of all UI controls and returns a gr.update() dictionary.
    """
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
    """
    Updates the speed and font size sliders to sensible defaults when the
    animation effect is changed.
    """
    font_size = 1.5
    if effect == "starwars":
        font_size = 6.0  # Star Wars effect looks better with a larger font
    
    speed = DEFAULT_SPEEDS.get(effect, 40.0)
    return speed, font_size

# --- 3. GRADIO UI DEFINITION ---
# This section constructs the user interface using gr.Blocks.

with gr.Blocks(theme=gr.themes.Ocean(), title="CreditsPanel Demo") as demo:
    gr.Markdown(
        """
        # Interactive CreditsPanel Demo
        Use the sidebar controls to customize the `CreditsPanel` component in real-time.
        """
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