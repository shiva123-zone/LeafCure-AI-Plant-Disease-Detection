from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from datetime import datetime
import os

# =========================
# 🌿 DISEASE CAUSES
# =========================
DISEASE_CAUSES = {

    "Tomato Early blight":
    """Tomato Early Blight is caused by a fungal pathogen called Alternaria solani.
    This disease generally occurs due to high humidity, warm temperature and poor air circulation.
    It spreads through infected soil, water splashes and contaminated tools.
    Continuous wetness on leaves and improper crop rotation can also increase the chances of infection.""",

    "Potato - Early blight":
    """Potato Early Blight is caused by the fungus Alternaria solani.
    The disease develops in plants under stress conditions such as lack of nutrients or improper irrigation.
    It spreads through wind, rain splash and infected plant debris present in soil.
    Warm and moist environmental conditions accelerate its growth rapidly.""",

    "Tomato Septoria leaf spot":
    """Septoria Leaf Spot is a fungal disease caused by Septoria lycopersici.
    It usually appears when leaves remain wet for long periods due to rainfall or overwatering.
    Poor air circulation and high humidity also promote its spread.
    The disease spreads through infected leaves, water and farm equipment.""",

    "Healthy":
    """The plant appears healthy with no visible disease symptoms.
    Proper irrigation, balanced soil nutrients and good sunlight exposure help maintain plant health.
    Regular monitoring and preventive care reduce the chances of future infections."""
}

def generate_pdf(user, disease, confidence, image_path):

    file_name = f"report_{user}.pdf"
    pdf_path = os.path.join("uploads", file_name)

    doc = SimpleDocTemplate(pdf_path, pagesize=A4)

    styles = getSampleStyleSheet()
    elements = []

    title = Paragraph("<b>LeafCure Analysis Report</b>", styles['Title'])
    elements.append(title)

    elements.append(Spacer(1,20))

    date = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

    elements.append(Paragraph(f"User: {user}", styles['Normal']))
    elements.append(Paragraph(f"Disease: {disease}", styles['Normal']))
    elements.append(Paragraph(f"Confidence: {confidence}%", styles['Normal']))
    elements.append(Paragraph(f"Date: {date}", styles['Normal']))

    elements.append(Spacer(1,20))
    # =========================
    # ADD DISEASE CAUSE PARAGRAPH
    # =========================
    cause = DISEASE_CAUSES.get(disease,
    "Plant disease occurs due to environmental stress, fungal or bacterial infection.")

    elements.append(Paragraph("<b>Cause of Disease:</b>", styles['Heading3']))
    elements.append(Spacer(1,10))
    elements.append(Paragraph(cause, styles['BodyText']))
    elements.append(Spacer(1,20))


    if os.path.exists(image_path):
        img = Image(image_path, width=4*inch, height=4*inch)
        elements.append(img)

    doc.build(elements)

    return pdf_path
