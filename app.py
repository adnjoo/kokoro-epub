import gradio as gr
from pipeline import epub_to_audio, extract_chapters, DEFAULT_VOICE

with gr.Blocks(title="kokoro-epub — Free EPUB → Audiobook") as demo:
    gr.Markdown("## Free EPUB → Audiobook (Open Source)")

    epub_in = gr.File(label="EPUB file", file_types=[".epub"])

    # State to store the full list of chapters so the buttons know what to select
    all_chapters = gr.State([])

    # Add quick selection buttons above the checkbox group
    with gr.Row():
        select_all_btn = gr.Button("Select All", size="sm")
        deselect_all_btn = gr.Button("Deselect All", size="sm")

    chapter_selector = gr.CheckboxGroup(label="Select chapters to convert", choices=[])


    def on_epub_upload(f):
        if f:
            choices = [f"{t} ({len(txt.split())} words)" for (t, txt) in extract_chapters(f.name)]
            return gr.update(choices=choices), choices
        return gr.update(choices=[]), []


    # Update both the checkbox choices and the background state when a file is uploaded
    epub_in.change(
        fn=on_epub_upload,
        inputs=epub_in,
        outputs=[chapter_selector, all_chapters],
    )

    # Wire up the selection buttons
    select_all_btn.click(
        fn=lambda choices: gr.update(value=choices),
        inputs=all_chapters,
        outputs=chapter_selector
    )

    deselect_all_btn.click(
        fn=lambda: gr.update(value=[]),
        outputs=chapter_selector
    )

    with gr.Row():
        voice = gr.Dropdown(
            label="Voice",
            value=DEFAULT_VOICE,
            choices=["af_heart","af_alloy","af_bella","af_rose","am_michael","am_adam","am_mandarin"],
        )
        speed = gr.Slider(0.7, 1.3, value=1.0, step=0.05, label="Speed")
        format_choice = gr.Radio(label="Output format", choices=["MP3", "M4B"], value="MP3")

    run_btn = gr.Button("Convert")
    audio_out = gr.File(label="Download MP3 (or ZIP)", visible=False)
    m4b_out = gr.File(label="Download M4B (with chapters)", visible=False)
    logs = gr.Textbox(label="Logs", lines=12)

    run_btn.click(
        fn=epub_to_audio,
        inputs=[epub_in, voice, speed, chapter_selector, format_choice],
        outputs=[audio_out, m4b_out, logs],
    )

if __name__ == "__main__":
    demo.launch()