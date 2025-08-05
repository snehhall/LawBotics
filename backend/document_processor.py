
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
from docx import Document
import spacy
import PyPDF2

# Initialize models
nlp = spacy.load("en_core_web_sm")
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
tokenizer = AutoTokenizer.from_pretrained("nlpaueb/legal-bert-small-uncased")
model = AutoModelForSequenceClassification.from_pretrained("nlpaueb/legal-bert-small-uncased")

# Legal term simplification dictionary
LEGAL_TERMS = {
    "force majeure": "unforeseeable circumstances that prevent someone from fulfilling a contract",
    "indemnification": "compensation for harm or loss",
    "indemnify": "to compensate for harm or loss",
    "jurisdiction": "the official authority to make legal decisions",
    "confidentiality": "the obligation to keep certain information private",
    "liability": "legal responsibility for one's actions",
    "breach": "violation or breaking of a contract or agreement",
    "default": "failure to fulfill an obligation or make a required payment",
    "warranty": "a guarantee or promise about the quality or condition of something",
    "arbitration": "resolution of disputes by an impartial third party",
    "intellectual property": "creations of the mind such as patents, copyrights, and trademarks",
    "termination": "the ending or cancellation of an agreement",
    "consideration": "something of value given in exchange for a promise or performance"
}

def extract_text(filepath):
    """Extract text from PDF, DOCX, or TXT files."""
    if filepath.endswith('.pdf'):
        reader = PyPDF2.PdfReader(filepath)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text.strip()

    elif filepath.endswith('.docx'):
        doc = Document(filepath)
        return '\n'.join([para.text for para in doc.paragraphs if para.text])

    else:  # .txt or fallback
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            with open(filepath, 'r', encoding='latin-1') as f:
                return f.read()

def analyze_legal_document(text):
    """Analyze the legal document using the legal BERT model."""
    inputs = tokenizer(text[:512], return_tensors="pt", truncation=True)
    outputs = model(**inputs)
    
    return {
        'key_clauses': identify_key_clauses(text),
        'obligations': identify_obligations(text),
        'risks': identify_risks(text)
    }

def identify_key_clauses(text):
    """Identify key clauses in the document."""
    clauses = []
    text_lower = text.lower()
    
    # Check for various clause types
    if "indemnif" in text_lower:
        clauses.append("Indemnification Clause")
    if "confidential" in text_lower:
        clauses.append("Confidentiality Clause")
    if "force majeure" in text_lower:
        clauses.append("Force Majeure Clause")
    if "terminat" in text_lower:
        clauses.append("Termination Clause")
    if "payment" in text_lower or "fee" in text_lower:
        clauses.append("Payment Terms")
    if "intellectual property" in text_lower or "ip" in text_lower:
        clauses.append("Intellectual Property Clause")
    if "dispute" in text_lower or "arbitration" in text_lower:
        clauses.append("Dispute Resolution Clause")
    if "liability" in text_lower or "damages" in text_lower:
        clauses.append("Liability Clause")
    
    return clauses if clauses else ["General Terms and Conditions"]

def identify_obligations(text):
    """Identify legal obligations in the text."""
    try:
        doc = nlp(text)
        obligations = []
        
        obligation_keywords = ["shall", "must", "required to", "obligated to", "duty to", "agree to"]
        
        for sent in doc.sents:
            sent_text = sent.text.strip()
            if len(sent_text) > 20:  # Skip very short sentences
                if any(keyword in sent_text.lower() for keyword in obligation_keywords):
                    # Clean up the sentence
                    clean_sent = ' '.join(sent_text.split())
                    if len(clean_sent) > 30:  # Only include substantial obligations
                        obligations.append(clean_sent)
        
        return obligations[:5]  # Return top 5 obligations
    except Exception as e:
        print(f"Error in identify_obligations: {e}")
        return ["Error processing obligations"]

def identify_risks(text):
    """Identify potential legal risks in the text."""
    try:
        doc = nlp(text)
        risks = []
        
        risk_keywords = ["liable", "liability", "penalty", "indemnify", "breach", "default", "warranty", 
                        "damages", "terminate", "suspend", "legal action", "claims"]
        
        for sent in doc.sents:
            sent_text = sent.text.strip()
            if len(sent_text) > 20:  # Skip very short sentences
                if any(keyword in sent_text.lower() for keyword in risk_keywords):
                    # Clean up the sentence
                    clean_sent = ' '.join(sent_text.split())
                    if len(clean_sent) > 30:  # Only include substantial risks
                        risks.append(clean_sent)
        
        return risks[:5]  # Return top 5 risks
    except Exception as e:
        print(f"Error in identify_risks: {e}")
        return ["Error processing risks"]

def summarize_text(text):
    """Generate a summary of the document."""
    try:
        # Clean and prepare text
        text = text.strip()
        if len(text) < 100:
            return text
        
        # Split into smaller chunks for better summarization
        max_chunk_size = 1000
        chunks = [text[i:i+max_chunk_size] for i in range(0, len(text), max_chunk_size)]
        summaries = []
        
        for chunk in chunks:
            if len(chunk.strip()) > 50:  # Only summarize substantial chunks
                try:
                    summary = summarizer(chunk, max_length=100, min_length=30, do_sample=False)
                    summaries.append(summary[0]['summary_text'])
                except Exception as chunk_error:
                    print(f"Error summarizing chunk: {chunk_error}")
                    # Fallback: take first few sentences
                    sentences = chunk.split('.')[:3]
                    summaries.append('. '.join(sentences) + '.')
        
        return ' '.join(summaries)
    except Exception as e:
        print(f"Error in summarize_text: {e}")
        # Fallback summary
        sentences = text.split('.')[:5]
        return '. '.join(sentences) + '.'

def simplify_legal_text(text):
    """Simplify legal jargon in the text."""
    try:
        simplified = text
        for term, explanation in LEGAL_TERMS.items():
            # Use case-insensitive replacement
            import re
            pattern = re.compile(re.escape(term), re.IGNORECASE)
            simplified = pattern.sub(f"[{term} ({explanation})]", simplified)
        return simplified
    except Exception as e:
        print(f"Error in simplify_legal_text: {e}")
        return text

def process_document(filepath):
    """Main processing pipeline for the document."""
    try:
        print(f"Processing document: {filepath}")
        text = extract_text(filepath)
        print(f"Extracted text length: {len(text)}")
        
        if not text or len(text.strip()) < 50:
            return {
                'analysis': {
                    'key_clauses': ["No content found"],
                    'obligations': ["No content found"],
                    'risks': ["No content found"]
                },
                'summary': "Document appears to be empty or too short to analyze.",
                'simplified_text': text
            }
        
        # Process the document
        analysis = analyze_legal_document(text)
        summary = summarize_text(text)
        simplified = simplify_legal_text(text)
        
        print(f"Analysis completed - Key clauses: {len(analysis['key_clauses'])}")
        
        return {
            'analysis': analysis,
            'summary': summary,
            'simplified_text': simplified
        }
    except Exception as e:
        print(f"Error in process_document: {e}")
        return {
            'analysis': {
                'key_clauses': ["Error processing document"],
                'obligations': ["Error processing document"],
                'risks': ["Error processing document"]
            },
            'summary': f"Error processing document: {str(e)}",
            'simplified_text': "Error processing document"
        }