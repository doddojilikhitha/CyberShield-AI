import logging
from typing import Dict, Any
from fpdf import FPDF

logger = logging.getLogger(__name__)


class CyberShieldPDF(FPDF):
    def header(self):
        # Top banner styling
        self.set_fill_color(30, 41, 59)  # Slate Dark (#1e293b)
        self.rect(0, 0, 210, 20, "F")

        self.set_text_color(255, 255, 255)
        self.set_font("helvetica", "B", 12)
        self.set_y(5)
        self.cell(
            0,
            10,
            "CYBERSHIELD AI - INCIDENT TELEMETRY & PLAYBOOK",
            align="C",
            new_x="LMARGIN",
            new_y="NEXT",
        )
        self.set_y(22)  # Spacer below header banner

    def footer(self):
        self.set_y(-15)
        self.set_fill_color(241, 245, 249)  # Light grey (#f1f5f9)
        self.rect(0, 280, 210, 20, "F")
        self.set_text_color(100, 116, 139)
        self.set_font("helvetica", "I", 8)
        self.cell(
            0,
            10,
            f"Page {self.page_no()} of {{nb}} | CONFIDENTIAL - INTERNAL SOC USE ONLY",
            align="C",
        )


def export_report_to_pdf(report: Dict[str, Any], output_path: str) -> str:
    """
    Renders compiled incident report data to a PDF file at output_path.
    """
    try:
        pdf = CyberShieldPDF(orientation="P", unit="mm", format="A4")
        pdf.alias_nb_pages()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=25)

        # --- TITLE ---
        pdf.set_text_color(30, 41, 59)
        pdf.set_font("helvetica", "B", 20)
        pdf.cell(0, 15, "Incident Report", new_x="LMARGIN", new_y="NEXT", align="L")

        # Draw a separator line
        pdf.set_draw_color(148, 163, 184)  # Light Slate
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)

        # --- SECTION: INCIDENT METADATA ---
        pdf.set_font("helvetica", "B", 14)
        pdf.set_text_color(51, 65, 85)
        pdf.cell(
            0, 10, "1. Incident Classification & Details", new_x="LMARGIN", new_y="NEXT"
        )
        pdf.ln(2)

        pdf.set_font("helvetica", "", 10)
        pdf.set_text_color(71, 85, 105)

        metadata = [
            ("Incident ID:", report.get("incident_id", "N/A")),
            ("Analyst Name:", report.get("analyst_name", "N/A")),
            ("Incident Type:", report.get("classification", "N/A")),
            ("Severity Tier:", str(report.get("severity", "N/A")).upper()),
            ("Created Timestamp:", report.get("created_at", "N/A")),
            ("Approved Timestamp:", report.get("approved_at", "N/A") or "N/A"),
        ]

        for key, val in metadata:
            pdf.set_font("helvetica", "B", 10)
            pdf.cell(50, 6, key, align="L")
            pdf.set_font("helvetica", "", 10)
            pdf.cell(0, 6, val, new_x="LMARGIN", new_y="NEXT", align="L")

        pdf.ln(5)

        # --- SECTION: INCIDENT DESCRIPTION ---
        pdf.set_font("helvetica", "B", 12)
        pdf.set_text_color(51, 65, 85)
        pdf.cell(0, 8, "Initial Incident Scope:", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("helvetica", "", 10)
        pdf.set_text_color(15, 23, 42)
        pdf.multi_cell(0, 5, report.get("incident_summary", ""))
        pdf.ln(5)

        # --- SECTION: FRAMEWORK ALIGNMENTS ---
        pdf.set_font("helvetica", "B", 14)
        pdf.set_text_color(51, 65, 85)
        pdf.cell(
            0, 10, "2. Regulatory & Framework Alignment", new_x="LMARGIN", new_y="NEXT"
        )
        pdf.ln(2)

        frameworks = [
            (
                "NIST Incident Phases:",
                ", ".join(report.get("nist_mapping", [])) or "None Mapped",
            ),
            (
                "MITRE ATT&CK Techniques:",
                ", ".join(report.get("mitre_mapping", [])) or "None Mapped",
            ),
            (
                "OWASP Security Categories:",
                ", ".join(report.get("owasp_guidance", [])) or "None Applicable",
            ),
        ]

        for key, val in frameworks:
            pdf.set_font("helvetica", "B", 10)
            pdf.cell(60, 6, key, align="L")
            pdf.set_font("helvetica", "", 10)
            pdf.multi_cell(0, 6, val, new_x="LMARGIN", new_y="NEXT")

        pdf.ln(5)

        # --- SECTION: INCIDENT RESPONSE PLAYBOOK ---
        pdf.set_font("helvetica", "B", 14)
        pdf.set_text_color(51, 65, 85)
        pdf.cell(0, 10, "3. Generated Response Playbook", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

        playbook_text = report.get("final_playbook")
        if playbook_text:
            pdf.set_font("helvetica", "", 9)
            pdf.set_text_color(15, 23, 42)
            # Renders playbook cleanly, splits lines to avoid overlapping
            for line in playbook_text.split("\n"):
                line_stripped = line.strip()
                if line_stripped.startswith("#"):
                    # Render headers with larger font
                    level = len(line_stripped) - len(line_stripped.lstrip("#"))
                    content = line_stripped.lstrip("#").strip()
                    pdf.ln(2)
                    pdf.set_font("helvetica", "B", 12 if level == 1 else 10)
                    pdf.cell(0, 6, content, new_x="LMARGIN", new_y="NEXT")
                    pdf.set_font("helvetica", "", 9)
                elif line_stripped.startswith("-") or line_stripped.startswith("*"):
                    content = line_stripped.lstrip("-* ").strip()
                    pdf.cell(8, 5, chr(149), align="R")  # Bullet point
                    pdf.multi_cell(0, 5, content, new_x="LMARGIN", new_y="NEXT")
                elif "|" in line_stripped:
                    # Renders tables as plain text lines
                    pdf.set_font("courier", "", 8)
                    pdf.cell(0, 4, line_stripped, new_x="LMARGIN", new_y="NEXT")
                    pdf.set_font("helvetica", "", 9)
                elif line_stripped:
                    pdf.multi_cell(0, 5, line_stripped)
                    pdf.ln(1)
        else:
            pdf.set_font("helvetica", "I", 10)
            pdf.cell(
                0,
                6,
                "No response playbook has been generated/approved yet.",
                new_x="LMARGIN",
                new_y="NEXT",
            )

        pdf.ln(5)

        # --- SECTION: AUDIT LOGS TIMELINE ---
        pdf.set_font("helvetica", "B", 14)
        pdf.set_text_color(51, 65, 85)
        pdf.cell(
            0,
            10,
            "4. Agent Execution & Human Audit Timeline",
            new_x="LMARGIN",
            new_y="NEXT",
        )
        pdf.ln(2)

        # Add table headers
        pdf.set_font("helvetica", "B", 8)
        pdf.set_fill_color(241, 245, 249)
        pdf.cell(45, 6, "Timestamp", border=1, fill=True)
        pdf.cell(40, 6, "Agent/Action", border=1, fill=True)
        pdf.cell(75, 6, "Details Summary", border=1, fill=True)
        pdf.cell(
            30, 6, "Processing Time", border=1, fill=True, new_x="LMARGIN", new_y="NEXT"
        )

        pdf.set_font("helvetica", "", 8)
        pdf.set_text_color(71, 85, 105)
        for log in report.get("audit_summary", []):
            ts = (
                log.get("timestamp", "N/A").split("T")[1][:8]
                if "T" in log.get("timestamp", "")
                else log.get("timestamp", "N/A")
            )
            agent = log.get("agent_name", "N/A")
            summary = log.get("output_summary", "N/A")[:50]
            duration = (
                f"{log.get('processing_time_ms', 0)}ms"
                if log.get("processing_time_ms")
                else "0ms"
            )

            pdf.cell(45, 6, ts, border=1)
            pdf.cell(40, 6, agent, border=1)
            pdf.cell(75, 6, summary, border=1)
            pdf.cell(30, 6, duration, border=1, new_x="LMARGIN", new_y="NEXT")

        pdf.output(output_path)
        logger.info(f"Successfully generated PDF report at: {output_path}")
        return output_path

    except Exception as e:
        logger.error(f"Error exporting report to PDF: {e}", exc_info=True)
        raise
