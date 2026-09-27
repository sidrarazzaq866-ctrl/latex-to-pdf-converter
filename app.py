import streamlit as st
import subprocess
import tempfile
import os

st.set_page_config(page_title="LaTeX to PDF Converter", page_icon="📄", layout="centered")

st.title("📄 LaTeX to PDF Converter")
st.write(
    "Paste your LaTeX code below (for example, a derivation or a question-answer "
    "you got from an AI assistant). Click **Convert**, and you'll get a clean, "
    "downloadable PDF — no more broken equations when pasting into Word."
)

# A ready-made template so the physics symbols, fractions, and derivations render correctly.
DEFAULT_PREAMBLE = r"""
\documentclass[12pt]{article}
\usepackage[margin=1in]{geometry}
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage{physics}
\usepackage{siunitx}
\setlength{\parindent}{0pt}
\begin{document}
"""
DEFAULT_ENDING = r"""
\end{document}
"""

mode = st.radio(
    "What are you pasting?",
    ["Just the content (recommended)", "A full LaTeX document (starts with \\documentclass)"],
    index=0,
)

placeholder_text = r"""Example:
Question: Derive the expression for the electric field of a uniformly charged sphere.

\textbf{Solution:}
By Gauss's Law:
\[
\oint \vec{E} \cdot d\vec{A} = \frac{Q_{enc}}{\varepsilon_0}
\]
For $r > R$:
\[
E(4\pi r^2) = \frac{Q}{\varepsilon_0} \quad \Rightarrow \quad E = \frac{Q}{4\pi\varepsilon_0 r^2}
\]
"""

latex_input = st.text_area(
    "LaTeX content",
    height=280,
    placeholder=placeholder_text,
)

filename = st.text_input("File name (without extension)", value="derivation")

col1, col2 = st.columns(2)
with col1:
    convert_pdf_clicked = st.button("Convert to PDF", type="primary", use_container_width=True)
with col2:
    convert_word_clicked = st.button("Convert to Word (.docx)", use_container_width=True)

def build_full_tex():
    if mode.startswith("Just the content"):
        return DEFAULT_PREAMBLE + "\n" + latex_input + "\n" + DEFAULT_ENDING
    return latex_input

if convert_pdf_clicked:
    if not latex_input.strip():
        st.warning("Please paste some LaTeX content first.")
    else:
        full_tex = build_full_tex()
        with st.spinner("Compiling your PDF..."):
            with tempfile.TemporaryDirectory() as tmpdir:
                tex_path = os.path.join(tmpdir, "document.tex")
                with open(tex_path, "w", encoding="utf-8") as f:
                    f.write(full_tex)

                # Run pdflatex twice — the second pass correctly resolves numbering/references.
                log_output = ""
                success = True
                for _ in range(2):
                    result = subprocess.run(
                        ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "document.tex"],
                        cwd=tmpdir,
                        capture_output=True,
                        text=True,
                        timeout=60,
                    )
                    log_output = result.stdout + result.stderr
                    if result.returncode != 0:
                        success = False
                        break

                pdf_path = os.path.join(tmpdir, "document.pdf")

                if success and os.path.exists(pdf_path):
                    with open(pdf_path, "rb") as f:
                        pdf_bytes = f.read()
                    st.success("Your PDF is ready.")
                    st.download_button(
                        "⬇️ Download PDF",
                        data=pdf_bytes,
                        file_name=f"{filename or 'document'}.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                    )
                else:
                    st.error(
                        "The LaTeX code didn't compile. This usually means there's a small "
                        "syntax mistake (a missing $, a missing \\, or an unclosed bracket). "
                        "Check the log below for the exact line."
                    )
                    with st.expander("Show compilation log"):
                        st.code(log_output, language="text")

if convert_word_clicked:
    if not latex_input.strip():
        st.warning("Please paste some LaTeX content first.")
    else:
        full_tex = build_full_tex()
        with st.spinner("Converting to Word..."):
            with tempfile.TemporaryDirectory() as tmpdir:
                tex_path = os.path.join(tmpdir, "document.tex")
                docx_path = os.path.join(tmpdir, "document.docx")
                with open(tex_path, "w", encoding="utf-8") as f:
                    f.write(full_tex)

                result = subprocess.run(
                    ["pandoc", "document.tex", "-o", "document.docx", "--from=latex", "--to=docx"],
                    cwd=tmpdir,
                    capture_output=True,
                    text=True,
                    timeout=60,
                )

                if result.returncode == 0 and os.path.exists(docx_path):
                    with open(docx_path, "rb") as f:
                        docx_bytes = f.read()
                    st.success("Your Word document is ready.")
                    st.caption(
                        "Math equations convert into real, editable Word equations — not images. "
                        "Note: equation numbers (like \\tag{22}) don't carry over to Word and would "
                        "need to be added manually if you need them."
                    )
                    st.download_button(
                        "⬇️ Download Word (.docx)",
                        data=docx_bytes,
                        file_name=f"{filename or 'document'}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True,
                    )
                else:
                    st.error(
                        "The conversion to Word failed. Check the log below for details."
                    )
                    with st.expander("Show conversion log"):
                        st.code(result.stdout + result.stderr, language="text")

st.divider()
st.caption(
    "Tip: if you're not sure your LaTeX is valid, ask the AI assistant that generated it "
    "to double-check the syntax before pasting it here."
)

