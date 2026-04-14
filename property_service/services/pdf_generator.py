import os
from jinja2 import Environment, FileSystemLoader
import logging

try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except Exception as e:
    logging.warning(f"WeasyPrint not available. Will mock PDF bytes. Error: {e}")
    WEASYPRINT_AVAILABLE = False

TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')

class PDFGenerator:
    def __init__(self):
        self.env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    
    def generate_agreement_pdf(self, context: dict) -> bytes:
        template = self.env.get_template('agreement.html')
        html_out = template.render(**context)
        
        if WEASYPRINT_AVAILABLE:
            try:
                pdf_bytes = HTML(string=html_out).write_pdf()
                return pdf_bytes
            except Exception as e:
                logging.error(f"Error compiling PDF natively: {e}")
                # Fallback on failure
                pass
        
        # Mock fallback if libraries missing
        fallback_text = f"%PDF-1.4\n%rentora-mock-pdf\n\nTitle: Rental Agreement\nProperty: {context.get('property_title')}\nTenant: {context.get('tenant_id')}\nOwner: {context.get('owner_id')}\n\n[End of File]"
        return fallback_text.encode('utf-8')
