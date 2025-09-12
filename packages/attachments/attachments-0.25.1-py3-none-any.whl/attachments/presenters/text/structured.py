"""Structured text presenters - CSV, XML, etc."""

import subprocess
import tempfile
from pathlib import Path

from ...core import Attachment, presenter
from ...loaders.documents.office import LibreOfficeDocument


@presenter
def csv(att: Attachment, doc: LibreOfficeDocument) -> Attachment:
    """
    Converts an Excel workbook to CSV format using the LibreOffice binary.
    Each sheet is converted to a separate CSV block.
    """
    soffice = att.metadata.get("libreoffice_binary_path")
    if not soffice:
        att.text += (
            "LibreOffice binary path not found. Please use the 'excel_to_libreoffice' loader first."
        )

    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            source_path = doc.path

            # Run LibreOffice conversion. It creates one .csv file per sheet.
            subprocess.run(
                [soffice, "--headless", "--convert-to", "csv", "--outdir", temp_dir, source_path],
                check=True,
                capture_output=True,
                timeout=60,
            )

            temp_path = Path(temp_dir)
            csv_files = sorted(list(temp_path.glob("*.csv")))

            if not csv_files:
                att.text += "CSV conversion failed - no output files found."

            for csv_file in csv_files:
                # Try to derive sheet name from filename, e.g., "source.Sheet1.csv"
                base_stem = Path(source_path).stem
                sheet_name = csv_file.stem
                if sheet_name.startswith(base_stem):
                    sheet_name = sheet_name[len(base_stem) :].lstrip(".")

                att.text += csv_file.read_text(encoding="utf-8")
                att.text += "\n\n"

        except subprocess.TimeoutExpired:
            att.metadata["libreoffice_error"] = "Excel to CSV conversion timed out (>60s)"
        except subprocess.CalledProcessError as e:
            err_msg = e.stderr.decode("utf-8", errors="ignore")
            att.metadata["libreoffice_error"] = f"LibreOffice conversion failed: {err_msg}"
        except Exception as e:
            att.metadata["libreoffice_error"] = f"Error converting Excel to CSV: {e}"

    return att


@presenter
def csv(att: Attachment, df: "pandas.DataFrame") -> Attachment:
    """Convert pandas DataFrame to CSV."""
    try:
        att.text += df.to_csv(index=False)
    except Exception as e:
        att.text += f"*Error converting to CSV: {e}*\n"
    return att


@presenter
def xml(att: Attachment, df: "pandas.DataFrame") -> Attachment:
    """Convert pandas DataFrame to XML."""
    try:
        att.text += df.to_xml(index=False)
    except Exception as e:
        att.text += f"*Error converting to XML: {e}*\n"
    return att


@presenter
def xml(att: Attachment, pres: "pptx.Presentation") -> Attachment:
    """Extract raw PPTX XML content for detailed analysis."""
    att.text += f"# PPTX XML Content: {att.path}\n\n"

    try:
        import xml.dom.minidom
        import zipfile

        # PPTX files are ZIP archives containing XML
        with zipfile.ZipFile(att.path, "r") as pptx_zip:
            # Get slide indices to process
            slide_indices = att.metadata.get("selected_slides", range(min(3, len(pres.slides))))

            att.text += "```xml\n"
            att.text += "<!-- PPTX Structure Overview -->\n"

            # List all XML files in the PPTX
            xml_files = [f for f in pptx_zip.namelist() if f.endswith(".xml")]
            att.text += f"<!-- XML Files: {', '.join(xml_files)} -->\n\n"

            # Extract slide XML content
            for slide_idx in slide_indices:
                slide_xml_path = f"ppt/slides/slide{slide_idx + 1}.xml"

                if slide_xml_path in pptx_zip.namelist():
                    try:
                        xml_content = pptx_zip.read(slide_xml_path).decode("utf-8")

                        # Pretty print the XML
                        dom = xml.dom.minidom.parseString(xml_content)
                        pretty_xml = dom.toprettyxml(indent="  ")

                        # Remove empty lines and XML declaration for cleaner output
                        lines = [line for line in pretty_xml.split("\n") if line.strip()]
                        if lines and lines[0].startswith("<?xml"):
                            lines = lines[1:]  # Remove XML declaration

                        att.text += f"<!-- Slide {slide_idx + 1} XML -->\n"
                        att.text += "\n".join(lines)
                        att.text += "\n\n"

                    except Exception as e:
                        att.text += f"<!-- Error parsing slide {slide_idx + 1} XML: {e} -->\n\n"
                else:
                    att.text += f"<!-- Slide {slide_idx + 1} XML not found -->\n\n"

            # Also include presentation.xml for overall structure
            if "ppt/presentation.xml" in pptx_zip.namelist():
                try:
                    pres_xml = pptx_zip.read("ppt/presentation.xml").decode("utf-8")
                    dom = xml.dom.minidom.parseString(pres_xml)
                    pretty_xml = dom.toprettyxml(indent="  ")
                    lines = [line for line in pretty_xml.split("\n") if line.strip()]
                    if lines and lines[0].startswith("<?xml"):
                        lines = lines[1:]

                    att.text += "<!-- Presentation Structure XML -->\n"
                    att.text += "\n".join(lines)

                except Exception as e:
                    att.text += f"<!-- Error parsing presentation XML: {e} -->\n"

            att.text += "```\n\n"
            att.text += f"*XML content extracted from {len(slide_indices)} slides*\n\n"

    except Exception as e:
        att.text += f"```\n<!-- Error extracting PPTX XML: {e} -->\n```\n\n"

    return att


@presenter
def xml(att: Attachment, doc: "docx.Document") -> Attachment:
    """Extract raw DOCX XML content for detailed analysis."""
    att.text += f"# DOCX XML Content: {att.path}\n\n"

    try:
        import xml.dom.minidom
        import zipfile

        # DOCX files are ZIP archives containing XML
        with zipfile.ZipFile(att.path, "r") as docx_zip:
            att.text += "```xml\n"
            att.text += "<!-- DOCX Structure Overview -->\n"

            # List all XML files in the DOCX
            xml_files = [f for f in docx_zip.namelist() if f.endswith(".xml")]
            att.text += f"<!-- XML Files: {', '.join(xml_files)} -->\n\n"

            # Extract main document XML content
            if "word/document.xml" in docx_zip.namelist():
                try:
                    xml_content = docx_zip.read("word/document.xml").decode("utf-8")

                    # Pretty print the XML
                    dom = xml.dom.minidom.parseString(xml_content)
                    pretty_xml = dom.toprettyxml(indent="  ")

                    # Remove empty lines and XML declaration for cleaner output
                    lines = [line for line in pretty_xml.split("\n") if line.strip()]
                    if lines and lines[0].startswith("<?xml"):
                        lines = lines[1:]  # Remove XML declaration

                    att.text += "<!-- Main Document XML -->\n"
                    att.text += "\n".join(lines)
                    att.text += "\n\n"

                except Exception as e:
                    att.text += f"<!-- Error parsing document XML: {e} -->\n\n"

            # Also include styles.xml for formatting information
            if "word/styles.xml" in docx_zip.namelist():
                try:
                    styles_xml = docx_zip.read("word/styles.xml").decode("utf-8")
                    dom = xml.dom.minidom.parseString(styles_xml)
                    pretty_xml = dom.toprettyxml(indent="  ")
                    lines = [line for line in pretty_xml.split("\n") if line.strip()]
                    if lines and lines[0].startswith("<?xml"):
                        lines = lines[1:]

                    att.text += "<!-- Styles XML -->\n"
                    att.text += "\n".join(lines)

                except Exception as e:
                    att.text += f"<!-- Error parsing styles XML: {e} -->\n"

            # Include document properties if available
            if "docProps/core.xml" in docx_zip.namelist():
                try:
                    props_xml = docx_zip.read("docProps/core.xml").decode("utf-8")
                    dom = xml.dom.minidom.parseString(props_xml)
                    pretty_xml = dom.toprettyxml(indent="  ")
                    lines = [line for line in pretty_xml.split("\n") if line.strip()]
                    if lines and lines[0].startswith("<?xml"):
                        lines = lines[1:]

                    att.text += "\n\n<!-- Document Properties XML -->\n"
                    att.text += "\n".join(lines)

                except Exception as e:
                    att.text += f"\n<!-- Error parsing properties XML: {e} -->\n"

            att.text += "```\n\n"
            att.text += "*XML content extracted from DOCX structure*\n\n"

    except Exception as e:
        att.text += f"```\n<!-- Error extracting DOCX XML: {e} -->\n```\n\n"

    return att
