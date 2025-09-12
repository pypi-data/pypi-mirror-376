import gradio as gr
from gradio_creditspanel import CreditsPanel
import os

# Create dummy license files
os.makedirs("LICENSES", exist_ok=True)
if not os.path.exists("LICENSES/Apache.txt"):
    with open("LICENSES/Apache.txt", "w") as f:
        f.write("Apache License\nVersion 2.0, January 2004\nhttp://www.apache.org/licenses/...")
if not os.path.exists("LICENSES/MIT.txt"):
    with open("LICENSES/MIT.txt", "w") as f:
        f.write("MIT License\nCopyright (c) 2025 Author\nPermission is hereby granted...")

# Create assets directory for logo
os.makedirs("assets", exist_ok=True)
if not os.path.exists("./assets/logo.webp"):
    print("Warning: ./assets/logo.webp not found. Creating placeholder. Replace with a valid WebP image.")
    with open("./assets/logo.webp", "w") as f:
        f.write("Placeholder WebP logo")
else:
    print("Logo found at ./assets/logo.webp")

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
    {"title": "Cloud Infrastructure Engineer", "name": "Lucas Nguyen"},
    {"title": "Mobile Developer", "name": "Mia Hernandez"},
    {"title": "Performance Engineer", "name": "James Taylor"},
    {"title": "Component Concept", "name": "Your Name"},
    {"title": "Support Engineer", "name": "Charlotte Moore"}
]

license_paths = {
    "Gradio Framework": "./LICENSES/Apache.txt",
    "This Component": "./LICENSES/MIT.txt"
}

DEFAULT_SPEEDS = {
    "scroll": 40.0,
    "starwars": 80.0,
    "matrix": 40.0
}

def update_panel(
    effect: str,
    speed: float,
    sidebar_position: str,
    show_logo: bool,
    show_licenses: bool,
    logo_position: str,
    logo_sizing: str,
    logo_width: int | str | None,
    logo_height: int | str | None,
    scroll_background_color: str | None,
    scroll_title_color: str | None,
    scroll_name_color: str | None
):
    print(f"Updating panel: effect={effect}, speed={speed}, sidebar_position={sidebar_position}, show_logo={show_logo}, show_licenses={show_licenses}, logo_position={logo_position}, logo_sizing={logo_sizing}, logo_width={logo_width}, logo_height={logo_height}")
    return gr.update(
        visible=True,
        effect=effect,
        speed=speed,
        sidebar_position=sidebar_position,
        show_logo=show_logo,
        show_licenses=show_licenses,
        logo_position=logo_position,
        logo_sizing=logo_sizing,
        logo_width=logo_width,
        logo_height=logo_height,
        scroll_background_color=scroll_background_color,
        scroll_title_color=scroll_title_color,
        scroll_name_color=scroll_name_color,
        value=credits_list
        # value={
        #     "credits": credits_list,
        #     "licenses": license_paths,
        #     "effect": effect,
        #     "speed": speed,
        #     "sidebar_position": sidebar_position,
        #     "logo_path": "./assets/logo.webp",  # Handled by Gradio's file serving
        #     "show_logo": show_logo,
        #     "show_licenses": show_licenses,
        #     "logo_position": logo_position,
        #     "logo_sizing": logo_sizing,
        #     "logo_width": logo_width,
        #     "logo_height": logo_height,
        #     "scroll_background_color": scroll_background_color,
        #     "scroll_title_color": scroll_title_color,
        #     "scroll_name_color": scroll_name_color
        # }
    )

def update_speed_on_effect_change(effect: str):
    """Update speed_slider to default speed when effect changes."""
    return DEFAULT_SPEEDS.get(effect, 40.0)

with gr.Blocks(theme=gr.themes.Ocean(), title="CreditsPanel Demo", css="") as demo:
    gr.Markdown(
        """
        # Interactive CreditsPanel Demo
        Use the sidebar controls to customize the credits panel.
        """
    )

    with gr.Sidebar(position="right"):
        effect_radio = gr.Radio(
            ["scroll", "starwars", "matrix"],
            label="Animation Effect",
            value="scroll",
            info="Select the visual style for the credits."
        )
        speed_slider = gr.Slider(
            minimum=5.0,
            maximum=100.0,
            step=1.0,
            value=DEFAULT_SPEEDS["scroll"],
            label="Animation Speed (seconds)",
            info="Duration of the animation cycle."
        )
        sidebar_position_radio = gr.Radio(
            ["right", "bottom"],
            label="Sidebar Position",
            value="right",
            info="Place the licenses sidebar on the right or bottom."
        )
        show_logo_checkbox = gr.Checkbox(
            label="Show Logo",
            value=True,
            info="Toggle the logo panel."
        )
        show_licenses_checkbox = gr.Checkbox(
            label="Show Licenses",
            value=True,
            info="Toggle the licenses sidebar."
        )
        logo_position_radio = gr.Radio(
            ["center", "left", "right"],
            label="Logo Position",
            value="center",
            info="Position of the logo in the panel."
        )
        logo_sizing_radio = gr.Radio(
            ["stretch", "crop", "resize"],
            label="Logo Sizing",
            value="resize",
            info="How the logo fits in the panel."
        )
        logo_width_input = gr.Textbox(
            label="Logo Width (px or CSS)",
            value="200px",
            info="Width of the logo (e.g., '200px' or '50%')."
        )
        logo_height_input = gr.Textbox(
            label="Logo Height (px or CSS)",
            value="100px",
            info="Height of the logo (e.g., '100px' or '10%')."
        )
        scroll_background_color = gr.ColorPicker(
            label="Scroll Background Color",
            value="#000000",
            info="Background color for ScrollEffect."
        )
        scroll_title_color = gr.ColorPicker(
            label="Scroll Title Color",
            value="#FFFFFF",
            info="Color for title text in ScrollEffect."
        )
        scroll_name_color = gr.ColorPicker(
            label="Scroll Name Color",
            value="#FFFFFF",
            info="Color for name text in ScrollEffect."
        )

    panel = CreditsPanel(
        credits=credits_list,
        licenses=license_paths,
        effect="scroll",
        height=500,
        speed=DEFAULT_SPEEDS["scroll"],
        sidebar_position="right",
        logo_path="./assets/logo.webp",  # Handled by Gradio's file serving
        show_logo=True,
        show_licenses=True,
        logo_position="center",
        logo_sizing="resize",
        logo_width="200px",
        logo_height="100px",
        scroll_background_color="#000000",
        scroll_title_color="#FFFFFF",
        scroll_name_color="#FFFFFF",
        visible=True
    )

    inputs = [
        effect_radio,
        speed_slider,
        sidebar_position_radio,
        show_logo_checkbox,
        show_licenses_checkbox,
        logo_position_radio,
        logo_sizing_radio,
        logo_width_input,
        logo_height_input,
        scroll_background_color,
        scroll_title_color,
        scroll_name_color
    ]
    
    # Update speed when effect changes
    effect_radio.change(
        fn=update_speed_on_effect_change,
        inputs=effect_radio,
        outputs=speed_slider
    )
    
    # Update panel for all inputs
    for input_component in inputs:
        input_component.change(
            fn=update_panel,
            inputs=inputs,
            outputs=panel
        )

if __name__ == "__main__":
    demo.launch(debug=True, share=False)