import ollama
import gradio as gr
from fpdf import FPDF
from fastapi import FastAPI
from datetime import datetime

app = FastAPI()


def generate_cover_letter(
    job_option, resume_option, job_file, resume_file, job_text, resume_text
):
    # Handle inputs based on the selected option
    if job_option == "Upload":
        job_description = (
            job_file.decode("utf-8") if job_file else "Job description file is missing."
        )
    else:
        job_description = job_text

    if resume_option == "Upload":
        resume = (
            resume_file.decode("utf-8") if resume_file else "Resume file is missing."
        )
    else:
        resume = resume_text

    now = datetime.now().strftime("%b %d, %Y")

    # Create the prompt
    prompt = f"""
    Create a professional 100 words cover letter for the following today's date, job description and resume with today's date, and it should not contain any input that needs to be given by user. Give me a finalized version in one shot. Also, make sure it can easily fit in one A4 size sheet:

    Today's date:
    {now}

    Job Description:
    {job_description}

    Resume:
    {resume}
    """

    # Generate cover letter using Ollama
    try:
        stream = ollama.chat(
            model="llama3.2",
            messages=[{"role": "user", "content": prompt}],
            stream=True,
        )

        # Collect and return the generated output
        cover_letter = ""
        for chunk in stream:
            cover_letter += chunk["message"]["content"]
        return cover_letter
    except Exception as e:
        return f"An error occurred during cover letter generation: {e}"


def save_as_pdf(content):
    """Save the generated cover letter as a PDF with A4 page size."""
    pdf = FPDF(format="A4")  # Set page size to A4
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.set_auto_page_break(
        auto=True, margin=15
    )  # Enable automatic page breaks with a margin

    # Define usable width for the text
    effective_page_width = pdf.w - 2 * pdf.l_margin

    # Split content into lines and add to PDF
    for line in content.split("\n"):
        # MultiCell handles line wrapping within the defined width
        pdf.multi_cell(w=effective_page_width, h=10, txt=line)

    # Save the PDF
    output_path = "cover_letter.pdf"  # Update path as needed
    pdf.output(output_path)
    return output_path


# Gradio app
def create_gradio_interface():
    with gr.Blocks() as app:
        gr.Markdown("## AI Cover Letter Generator")
        gr.Markdown("Choose how to provide your job description and resume.")

        with gr.Row():
            with gr.Column():
                job_option = gr.Radio(
                    ["Upload", "Paste"],
                    label="Job Description Input Method",
                    value="Upload",
                )
                job_file = gr.File(
                    label="Upload Job Description (txt)", type="binary", visible=True
                )
                job_text = gr.Textbox(
                    label="Paste Job Description",
                    visible=False,
                    placeholder="Paste job description here...",
                )
                job_option.change(
                    lambda option: (
                        gr.update(visible=option == "Upload"),
                        gr.update(visible=option == "Paste"),
                    ),
                    inputs=job_option,
                    outputs=[job_file, job_text],
                )

            with gr.Column():
                resume_option = gr.Radio(
                    ["Upload", "Paste"], label="Resume Input Method", value="Upload"
                )
                resume_file = gr.File(
                    label="Upload Resume (txt)", type="binary", visible=True
                )
                resume_text = gr.Textbox(
                    label="Paste Resume",
                    visible=False,
                    placeholder="Paste resume here...",
                )
                resume_option.change(
                    lambda option: (
                        gr.update(visible=option == "Upload"),
                        gr.update(visible=option == "Paste"),
                    ),
                    inputs=resume_option,
                    outputs=[resume_file, resume_text],
                )

        generate_button = gr.Button("Generate Cover Letter")
        output_text = gr.Textbox(label="Generated Cover Letter", lines=20)
        pdf_button = gr.DownloadButton("Download as PDF", visible=False)
        pdf_file = gr.File(label="Download PDF", visible=True)

        def handle_pdf(content):
            if content.strip():
                pdf_path = save_as_pdf(content)
                return gr.update(visible=False), pdf_path
            return gr.update(visible=False), None

        generate_button.click(
            generate_cover_letter,
            inputs=[
                job_option,
                resume_option,
                job_file,
                resume_file,
                job_text,
                resume_text,
            ],
            outputs=output_text,
        )

        output_text.change(
            handle_pdf,
            inputs=output_text,
            outputs=[pdf_button, pdf_file],
            # outputs=[pdf_file, pdf_button],
        )

    return app


gradio_app = create_gradio_interface()
app = gr.mount_gradio_app(app, gradio_app, path="/")
