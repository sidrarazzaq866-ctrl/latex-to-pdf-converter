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

filename = st.text_input("File name (without .pdf)", value="derivation")

convert_clicked = st.button("Convert to PDF", type="primary", use_container_width=True)

if convert_clicked:
    if not latex_input.strip():
        st.warning("Please paste some LaTeX content first.")
    else:
        if mode.startswith("Just the content"):
            full_tex = DEFAULT_PREAMBLE + "\n" + latex_input + "\n" + DEFAULT_ENDING
        else:
            full_tex = latex_input

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

st.divider()
st.caption(
    "Tip: if you're not sure your LaTeX is valid, ask the AI assistant that generated it "
    "to double-check the syntax before pasting it here."
)
