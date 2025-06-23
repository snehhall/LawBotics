from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
from sentence_transformers import SentenceTransformer
import pdfplumber
from docx import Document
import spacy
import os

# Initialize models
nlp = spacy.load("en_core_web_sm")
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
tokenizer = AutoTokenizer.from_pretrained("nlpaueb/legal-bert-small-uncased")
model = AutoModelForSequenceClassification.from_pretrained("nlpaueb/legal-bert-small-uncased")
sentence_model = SentenceTransformer('all-MiniLM-L6-v2')

# Legal term simplification dictionary
LEGAL_TERMS = {
    "force majeure": "unforeseeable circumstances that prevent someone from fulfilling a contract",
    "indemnification": "compensation for harm or loss",
    "jurisdiction": "the official authority to make legal decisions",
    "confidentiality": "the obligation to keep certain information private",
    "liability": "legal responsibility for one's actions",
    # Add more terms as needed
}

def extract_text(filepath):
    """Extract text from PDF, DOCX, or TXT files."""
    if filepath.endswith('.pdf'):
        with pdfplumber.open(filepath) as pdf:
            return '\n'.join([page.extract_text() for page in pdf.pages if page.extract_text()])
    elif filepath.endswith('.docx'):
        doc = Document(filepath)
        return '\n'.join([para.text for para in doc.paragraphs if para.text])
    else:  # Assume plain text
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()

def analyze_legal_document(text):
    """Analyze the legal document using the legal BERT model."""
    inputs = tokenizer(text[:512], return_tensors="pt", truncation=True)
    outputs = model(**inputs)
    # You can add more sophisticated analysis based on model outputs if needed
    return {
        'key_clauses': identify_key_clauses(text),
        'obligations': identify_obligations(text),
        'risks': identify_risks(text)
    }

def identify_key_clauses(text):
    """Identify key clauses in the document."""
    clauses = []
    if "indemnification" in text.lower():
        clauses.append("Indemnification Clause")
    if "confidentiality" in text.lower():
        clauses.append("Confidentiality Clause")
    if "force majeure" in text.lower():
        clauses.append("Force Majeure Clause")
    if "termination" in text.lower():
        clauses.append("Termination Clause")
    return clauses or ["General Terms and Conditions"]

def summarize_text(text):
    """Generate a summary of the document."""
    chunks = [text[i:i+1024] for i in range(0, len(text), 1024)]
    summaries = []
    for chunk in chunks:
        summary = summarizer(chunk, max_length=150, min_length=30, do_sample=False)
        summaries.append(summary[0]['summary_text'])
    return ' '.join(summaries)

def simplify_legal_text(text):
    """Simplify legal jargon in the text."""
    simplified = text
    for term, explanation in LEGAL_TERMS.items():
        if term in text.lower():
            simplified = simplified.replace(term, f"[{term} ({explanation})]")
    return simplified

def process_document(filepath):
    """Main processing pipeline for the document."""
    text = extract_text(filepath)
    
    return {
        'analysis': analyze_legal_document(text),
        'summary': summarize_text(text),
        'simplified_text': simplify_legal_text(text)
    }

def identify_obligations(text):
    """Identify legal obligations in the text."""
    doc = nlp(text)
    obligations = []
    
    obligation_keywords = ["shall", "must", "required to", "obligated to", "duty to"]
    
    for sent in doc.sents:
        if any(keyword in sent.text.lower() for keyword in obligation_keywords):
            obligations.append(sent.text.strip())
    
    return obligations[:5]  # Return top 5 obligations

def identify_risks(text):
    """Identify potential legal risks in the text."""
    doc = nlp(text)
    risks = []
    
    risk_keywords = ["liable", "penalty", "indemnify", "breach", "default", "warranty"]
    
    for sent in doc.sents:
        if any(keyword in sent.text.lower() for keyword in risk_keywords):
            risks.append(sent.text.strip())
    
    return risks[:5]  # Return top 5 risks
