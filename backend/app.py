

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
from document_processor import process_document
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
from langchain_community.vectorstores import Qdrant
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA
from langchain_core.prompts import PromptTemplate
from langchain.llms import HuggingFacePipeline
import torch


frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../frontend'))
app = Flask(__name__, static_folder=frontend_dir)
CORS(app, resources={r"/api/*": {"origins": "*"}})


def initialize_rag():

    model_name = "BAAI/bge-small-en"
    embeddings = HuggingFaceBgeEmbeddings(
        model_name=model_name,
        model_kwargs={'device': 'cuda' if torch.cuda.is_available() else 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )


    qdrant = Qdrant.from_texts(
        texts=["Initial document"],
        embedding=embeddings,
        location=":memory:",
        collection_name="legal_docs"
    )


    model_name = "gpt2"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(model_name)
    pipe = pipeline("text-generation", model=model, tokenizer=tokenizer, max_length=256)
    llm = HuggingFacePipeline(pipeline=pipe)

    # Create prompt template
    prompt_template = """Use the following legal context to answer the question:
    Context: {context}
    Question: {question}
    Answer:"""
    
    PROMPT = PromptTemplate(
        template=prompt_template, 
        input_variables=["context", "question"]
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

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Empty filename'}), 400
    
    # Save file
    upload_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../frontend/uploads'))
    os.makedirs(upload_dir, exist_ok=True)
    filepath = os.path.join(upload_dir, file.filename)
    file.save(filepath)
    
    try:
        # Process document using the extract_text function from document_processor
        result = process_document(filepath)
        
        # Extract text properly for vector store (use the same extraction method)
        from document_processor import extract_text
        text = extract_text(filepath)
        
        # Split text into chunks
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = text_splitter.split_text(text)
        
        # Add to Qdrant with metadata
        metadatas = [{"source": file.filename, "chunk": i} for i in range(len(chunks))]
        qdrant.add_texts(texts=chunks, metadatas=metadatas)
        
        return jsonify({
            'success': True,
            'filename': file.filename,
            'analysis': result['analysis'],
            'summary': result['summary'],
            'simplified_text': result['simplified_text']
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
        return jsonify({'error': str(e)}), 500

@app.route('/')
def serve_index():
    return send_from_directory(frontend_dir, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(frontend_dir, path)

if __name__ == '__main__':
    app.run(debug=True, port=5000)