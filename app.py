
import io
import hashlib

import streamlit as st
import pymupdf
from PIL import Image, ImageDraw
from streamlit_cropper import st_cropper


# --------------------------------------------------
# 1. Configure the application
# --------------------------------------------------
st.set_page_config(
    page_title="ResearchPilot AI",
    page_icon="🔬",
    layout="wide",
)


# Style the PDF page-number input.
st.markdown(
    """
    <style>
    div[data-testid="stNumberInput"] input {
        border: 2px solid #2563eb !important;
        border-radius: 6px !important;
        font-weight: 600;
    }

    div[data-testid="stNumberInput"] input:focus {
        border-color: #dc2626 !important;
        box-shadow: 0 0 0 2px rgba(220, 38, 38, 0.15);
    }
    </style>
    """,
    unsafe_allow_html=True,
)


st.title("🔬 ResearchPilot AI")
st.write("Understand the science. Verify the evidence.")


# --------------------------------------------------
# 2. Upload the scientific PDF
# --------------------------------------------------
uploaded_file = st.file_uploader(
    "Upload a scientific research paper",
    type=["pdf"],
    max_upload_size=20,
)

if uploaded_file is not None:

    pdf_bytes = uploaded_file.getvalue()

    # Identify the uploaded document.
    file_id = hashlib.sha256(pdf_bytes).hexdigest()[:12]

    try:
        document = pymupdf.open(
            stream=pdf_bytes,
            filetype="pdf",
        )
    except Exception as error:
        st.error(f"Unable to open PDF: {error}")
        st.stop()

    with document:

        if document.needs_pass:
            st.error("Password-protected PDFs are not supported yet.")
            st.stop()

        if len(document) == 0:
            st.error("This PDF has no pages.")
            st.stop()

        st.success("PDF uploaded successfully!")
        st.write(f"Filename: {uploaded_file.name}")
        st.write(f"Total pages: {len(document)}")

        # ------------------------------------------
        # 3. Select PDF page
        # ------------------------------------------
        page_col, info_col = st.columns([1, 5])

        with page_col:
            page_number = st.number_input(
                "Select PDF page",
                min_value=1,
                max_value=len(document),
                value=1,
                step=1,
                key=f"page_{file_id}",
            )

        with info_col:
            st.write("")
            st.write(f"Total: {len(document)} pages")

        page = document[page_number - 1]

        # ------------------------------------------
        # 4. Render PDF page as an image
        # ------------------------------------------
        pixmap = page.get_pixmap(
            matrix=pymupdf.Matrix(2, 2),
            alpha=False,
        )

        page_image = Image.open(
            io.BytesIO(pixmap.tobytes("png"))
        ).convert("RGB")

        # Make a smaller image for mouse selection.
        display_image = page_image.copy()
        display_image.thumbnail((700, 1200))

        # ------------------------------------------
        # 5. Figure selection state
        # ------------------------------------------
        selection_id = f"{file_id}_{page_number}"

        if st.session_state.get("selection_id") != selection_id:
            st.session_state.selection_id = selection_id
            st.session_state.corner1 = None
            st.session_state.corner2 = None
            st.session_state.click_version = 0

        st.subheader("Select an Experimental Figure")

        st.info(
            "Click two opposite corners of the figure. "
            "First click one corner, then click the opposite corner."
        )

        # Draw markers showing selected corners.
        marked_image = display_image.copy()
        draw = ImageDraw.Draw(marked_image)

        for corner in [
            st.session_state.corner1,
            st.session_state.corner2,
        ]:
            if corner is not None:
                x, y = corner
                draw.ellipse(
                    (x - 5, y - 5, x + 5, y + 5),
                    fill="red",
                    outline="white",
                    width=2,
                )

        if (
            st.session_state.corner1 is not None
            and st.session_state.corner2 is not None
        ):
            x1, y1 = st.session_state.corner1
            x2, y2 = st.session_state.corner2

            draw.rectangle(
                (
                    min(x1, x2),
                    min(y1, y2),
                    max(x1, x2),
                    max(y1, y2),
                ),
                outline="red",
                width=3,
            )

       
        # ------------------------------------------
        # 6. Select figure by dragging
        # ------------------------------------------
        st.subheader("Select a Figure")

        st.info(
            "Drag the blue rectangle to select a scientific "
            "figure. Resize or move it as needed."
        )

        cropped_figure = st_cropper(
            page_image,
            realtime_update=True,
            box_color="#2563eb",
            aspect_ratio=None,
            return_type="image",
            key=f"cropper_{selection_id}",
        )

        # ------------------------------------------
        # 7. Preview and download selected figure
        # ------------------------------------------
        if cropped_figure is not None:

            st.subheader("Selected Figure Preview")

            st.image(
                cropped_figure,
                caption=f"Selected figure from PDF Page {page_number}",
            )

            output = io.BytesIO()
            cropped_figure.save(output, format="PNG")

            st.download_button(
                label="Download Selected Figure (PNG)",
                data=output.getvalue(),
                file_name=f"ResearchPilot_page_{page_number}_figure.png",
                mime="image/png",
            )



        # ------------------------------------------
        # 8. Display extracted PDF text
        # ------------------------------------------
        st.subheader("Extracted Text")

        extracted_text = page.get_text("text")

        st.text_area(
            f"PDF Page {page_number} text",
            value=extracted_text,
            height=300,
        )
