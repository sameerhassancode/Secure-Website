from fpdf import FPDF
import os

def generate_pdf(report_data, cnic):
    filename = f"report_{cnic}.pdf"
    filepath = os.path.join('static/reports', filename)
    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, report_data)
    pdf.output(filepath)
    
    return filepath

