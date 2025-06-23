from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
from document_processor import process_document
from transformers import AutoModelForCausalLM, AutoTokenizer
from langchain_community.vectorstores import Qdrant
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA
import torch
from langchain_community.document_loaders import TextLoader
from langchain_core.prompts import PromptTemplate

app = Flask(__name__, static_folder=r'C:\Users\hp\Downloads\Lawbotics\frontend')
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Initialize RAG components
def initialize_rag():
    # Load embedding model
    model_name = "BAAI/bge-small-en"
    embeddings = HuggingFaceBgeEmbeddings(
        model_name=model_name,
        model_kwargs={'device': 'cuda' if torch.cuda.is_available() else 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )

    # Initialize with empty documents - these will be added during upload
    texts = ["Initial document"]  # Temporary placeholder
    metadatas = [{}]  # Empty metadata
    
    # Create Qdrant instance
    qdrant = Qdrant.from_texts(
        texts=texts,
        embedding=embeddings,
        location=":memory:",  # Use in-memory for testing, replace with path for production
        collection_name="legal_docs"
    )

    # Set up the LLM (replace with your actual LLM)
    model_name = "gpt2"  # For testing, use a better model for production
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    llm = AutoModelForCausalLM.from_pretrained(model_name)

    # Create prompt template
    prompt_template = """Use the following legal context to answer the question:
    Context: {context}
    Question: {question}
    Answer:"""
    
    PROMPT = PromptTemplate(
        template=prompt_template, input_variables=["context", "question"]
    )

    # Set up the RetrievalQA chain
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=qdrant.as_retriever(),
        chain_type_kwargs={"prompt": PROMPT},
        return_source_documents=True
    )
    return qdrant, qa_chain

# Initialize RAG system
qdrant, qa_chain = initialize_rag()

# Document Processing Endpoint
@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Empty filename'}), 400
    
    # Save file
    upload_dir = r'C:\Users\hp\Downloads\Lawbotics\frontend\uploads'
    os.makedirs(upload_dir, exist_ok=True)
    filepath = os.path.join(upload_dir, file.filename)
    file.save(filepath)
    
    try:
        # Process document
        result = process_document(filepath)
        
        # Add document to vector store
        with open(filepath, 'r', encoding='utf-8') as f:
            text = f.read()
        
        # Split text into chunks
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = text_splitter.split_text(text)
        
        # Add to Qdrant
        qdrant.add_texts(texts=chunks)
        
        return jsonify({
            'success': True,
            'filename': file.filename,
            'analysis': result['analysis'],
            'summary': result['summary'],
            'simplified_text': result['simplified_text']
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Chatbot Endpoint
@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    question = data.get('question')
    
    if not question:
        return jsonify({'error': 'Question is required'}), 400
    
    try:
        # Get response from RAG system
        result = qa_chain.invoke({"query": question})
        
        return jsonify({
            'response': result['result'],
            'sources': [doc.metadata.get('source', 'Document') for doc in result['source_documents']]
        })
    except Exception as e:
        return jsonify({'error': str(e), 'message': 'Failed to generate response'}), 500

# Serve Frontend
@app.route('/')
def serve_index():
    return send_from_directory(r'C:\Users\hp\Downloads\Lawbotics\frontend', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(r'C:\Users\hp\Downloads\Lawbotics\frontend', path)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
