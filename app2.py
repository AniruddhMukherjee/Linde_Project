import streamlit as st
import google.generativeai as genai
import fitz  # PyMuPDF
import tempfile
import os
import base64
import uuid
import json
from pathlib import Path

# Page configuration without sidebar orientation
st.set_page_config(page_title="Document Q&A System", layout="wide", initial_sidebar_state="collapsed")

# Hide the standard left sidebar completely with CSS
hide_sidebar_style = """
    <style>
        [data-testid="collapsedControl"] {display: none;}
        section[data-testid="stSidebar"] {display: none;}
        
        /* Custom right panel styling */
        .right-panel {
            border-left: 1px solid #eee;
            padding-left: 20px;
        }
        
        /* PDF container styling */
        .pdf-container {
            display: flex;
            justify-content: center;
            margin-top: 20px;
        }
        iframe {
            width: 100%;
            height: 600px;  /* Reduced height from 900px to 600px */
            border: none;
        }
        
        /* Reference text styling */
        .reference-text {
            margin-top: 10px;
            padding: 10px;
            background-color: #f5f5f5;
            border-left: 4px solid #4CAF50;
            font-style: italic;
        }
    </style>
"""
st.markdown(hide_sidebar_style, unsafe_allow_html=True)

def init_gemini():
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        return genai.GenerativeModel('gemini-1.5-flash')
    except Exception as e:
        st.error(f"Failed to initialize Gemini: {e}")
        return None

def process_document(file, model):
    content = {'text': {}, 'type': 'pdf'}
    
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(file.getvalue())
            tmp_file.flush()
            
            doc = fitz.open(tmp_file.name)
            
            # Process each page
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                if text.strip():
                    content['text'][page_num + 1] = text
                    
                # Convert page to image for display
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                content[f'page_{page_num + 1}'] = base64.b64encode(pix.tobytes("png")).decode('utf-8')
            
            # Save file content for download
            content['file_content'] = base64.b64encode(file.getvalue()).decode('utf-8')
            content['file_name'] = file.name
            
            doc.close()
            os.unlink(tmp_file.name)
            return content
            
    except Exception as e:
        st.error(f"Error processing document: {e}")
        return None

def find_reference_text(model, documents, question, answer_text, doc_name, page_num):
    """Use the LLM to find the specific text from the document that supports the answer"""
    try:
        if doc_name in documents and page_num in documents[doc_name]['text']:
            page_text = documents[doc_name]['text'][page_num]
            
            prompt = f"""
            Question: {question}
            Answer: {answer_text}
            Document Text: {page_text}
            
            Task: Find and extract the exact text from the document that best supports the answer.
            The text should be a direct quote from the document (100 words maximum).
            Only return the exact text from the document without any additional commentary.
            """
            
            response = model.generate_content(prompt)
            return response.text.strip() if response else None
        
        return None
    except Exception as e:
        st.error(f"Error finding reference text: {e}")
        return None

def answer_question(model, documents, question):
    try:
        context = []
        for doc_name, doc_content in documents.items():
            for page_num, text in doc_content['text'].items():
                context.append({
                    'text': text,
                    'page': page_num,
                    'document': doc_name
                })
        
        prompt_context = ' '.join([f"[Doc: {c['document']}, Page {c['page']}]: {c['text']}" for c in context])
        prompt = f"""Question: {question}
        Context: {prompt_context}
        Provide a concise answer in 50 words or less. Include the document name and page number.
        Format your response exactly like this:
        Answer text
        Referenced document: "document_name",  Page No.: X"""
        
        response = model.generate_content(prompt)
        return response.text.strip() if response else "No answer found."
    
    except Exception as e:
        st.error(f"Error generating answer: {e}")
        return None

def save_document_content():
    """Save documents in session state to a persistent location"""
    docs_dir = Path("docs_cache")
    docs_dir.mkdir(exist_ok=True)
    
    doc_paths = {}
    
    for doc_name, doc_content in st.session_state.documents.items():
        # Save encoded page images
        for page_key, page_data in doc_content.items():
            if page_key.startswith('page_'):
                page_num = int(page_key.split('_')[1])
                
                # Save the image data
                img_path = docs_dir / f"{doc_name.replace('/', '_')}_{page_num}.png"
                if not img_path.exists():  # Only save if doesn't exist
                    with open(img_path, 'wb') as f:
                        f.write(base64.b64decode(page_data))
                
                # Keep track of paths
                if doc_name not in doc_paths:
                    doc_paths[doc_name] = {}
                doc_paths[doc_name][str(page_num)] = str(img_path)
        
        # Save the file content for download if it exists
        if 'file_content' in doc_content and 'file_name' in doc_content:
            file_path = docs_dir / f"{doc_name.replace('/', '_')}_original.pdf"
            if not file_path.exists():  # Only save if doesn't exist
                with open(file_path, 'wb') as f:
                    f.write(base64.b64decode(doc_content['file_content']))
            
            # Add file path to doc_paths for download
            if doc_name not in doc_paths:
                doc_paths[doc_name] = {}
            doc_paths[doc_name]['original_file'] = str(file_path)
    
    # Save a mapping file
    with open(docs_dir / "doc_paths.json", 'w') as f:
        json.dump(doc_paths, f)

def display_pdf(file_path, start_page):
    """Display a PDF file with a specific starting page."""
    # Create a base64 encoded string for the PDF file
    with open(file_path, 'rb') as f:
        file_content = f.read()
    base64_pdf = base64.b64encode(file_content).decode('utf-8')
    
    # Use a URL fragment to specify the starting page
    pdf_display = f'<div class="pdf-container"><iframe src="data:application/pdf;base64,{base64_pdf}#page={start_page}" type="application/pdf"></iframe></div>'
    st.markdown(pdf_display, unsafe_allow_html=True)


def main():
    # Initialize session state
    if 'documents' not in st.session_state:
        st.session_state.documents = {}
    if 'qa_history' not in st.session_state:
        st.session_state.qa_history = []
    if 'viewing_document' not in st.session_state:
        st.session_state.viewing_document = False
    
    st.title("📚 Document Q&A System")
    
    model = init_gemini()
    if not model:
        st.stop()
    
    # File upload
    files = st.file_uploader("Upload PDF documents", type=['pdf'], accept_multiple_files=True)
    
    # Check if files were removed
    if not files and st.session_state.documents:
        # Reset document state when files are removed
        st.session_state.documents = {}
        st.session_state.viewing_document = False
        st.info("👆 Upload PDF documents to get started!")
        st.stop()
    
    # If no documents are uploaded yet, show info message and stop
    if not files and not st.session_state.documents:
        st.info("👆 Upload PDF documents to get started!")
        st.stop()
    
    # Process uploaded files
    if files:
        for file in files:
            if file.name not in st.session_state.documents:
                with st.spinner(f"Processing {file.name}..."):
                    content = process_document(file, model)
                    if content:
                        st.session_state.documents[file.name] = content
        
        # Save documents for later access
        save_document_content()
    
    # Create a layout only if we have documents
    if st.session_state.documents:
        # Create layout based on viewing state
        if st.session_state.viewing_document:
            # When viewing a document, use a 2-column layout (60% main, 40% document viewer)
            main_col, right_panel = st.columns([6, 4])
        else:
            # When not viewing a document, use full width for main content
            main_col = st.container()
        
        # Main app content
        with main_col:
            # Q&A Interface
            st.markdown("### ❓ Ask Questions")
            question = st.text_input("Enter your question:")
            
            if st.button("🔍 Ask", type="primary") and question:
                with st.spinner("Generating answer..."):
                    answer = answer_question(model, st.session_state.documents, question)
                    if answer:
                        # Split answer into text and reference
                        answer_parts = answer.split('\nReferenced document:', 1)
                        if len(answer_parts) == 2:
                            answer_text = answer_parts[0].strip()
                            ref_info = answer_parts[1].strip()
                            
                            reference_text = None
                            # Extract page number and document name
                            try:
                                doc_name = ref_info.split('"')[1]
                                page_num = int(ref_info.split('Page No.:', 1)[1].strip())
                                
                                # Find the reference text
                                reference_text = find_reference_text(
                                    model, 
                                    st.session_state.documents, 
                                    question, 
                                    answer_text, 
                                    doc_name, 
                                    page_num
                                )
                                
                                # Store reference information
                                doc_ref = {
                                    'name': doc_name, 
                                    'page': page_num,
                                    'reference_text': reference_text
                                }
                            except:
                                doc_ref = None
                                st.warning("Couldn't parse page reference information")
                            
                            # Display answer and reference info
                            st.markdown("#### Answer")
                            st.write(answer_text)
                            st.write(f"Referenced document: {ref_info}")
                            
                            # Display the reference text if available
                            if reference_text:
                                st.markdown("#### Supporting Text")
                                st.markdown(f'<div class="reference-text">{reference_text}</div>', unsafe_allow_html=True)
                        
                        st.session_state.qa_history.append({
                            'id': str(uuid.uuid4()),
                            'question': question,
                            'answer': answer,
                            'doc_ref': doc_ref if 'doc_ref' in locals() else None
                        })
            
            # Show history with document reference buttons
            if st.session_state.qa_history:
                st.markdown("### 📜 Previous Q&A")
                for qa in reversed(st.session_state.qa_history):
                    col1, col2 = st.columns([8, 2])
                    
                    with col1:
                        with st.expander(f"Q: {qa['question']}"):
                            st.markdown(qa['answer'])
                            
                            # Display reference text in history if available
                            if qa.get('doc_ref') and qa['doc_ref'].get('reference_text'):
                                st.markdown("#### Supporting Text")
                                st.markdown(f'<div class="reference-text">{qa["doc_ref"]["reference_text"]}</div>', unsafe_allow_html=True)
                    
                    with col2:
                        if qa.get('doc_ref'):
                            doc_name = qa['doc_ref']['name']
                            page_num = qa['doc_ref']['page']
                            
                            # Check if this document still exists
                            if doc_name in st.session_state.documents:
                                # Button to view document in right panel
                                if st.button(f"View Document", key=f"btn_{qa['id']}"):
                                    st.session_state.viewing_document = True
                                    st.session_state.viewing_doc_name = doc_name
                                    st.session_state.viewing_page_num = page_num
                                    st.rerun()
                            else:
                                st.info("Document removed")
        
        # Right panel for document viewer (only rendered when viewing_document is True)
        if st.session_state.viewing_document:
            # Verify the document still exists before showing the panel
            doc_name = st.session_state.viewing_doc_name
            if doc_name not in st.session_state.documents:
                st.session_state.viewing_document = False
                st.rerun()
                
            with right_panel:
                st.markdown('<div class="right-panel">', unsafe_allow_html=True)
                
                page_num = st.session_state.viewing_page_num
                
                # Load the document paths mapping
                try:
                    docs_dir = Path("docs_cache")
                    with open(docs_dir / "doc_paths.json", 'r') as f:
                        doc_paths = json.load(f)
                    
                    if doc_name in doc_paths and 'original_file' in doc_paths[doc_name]:
                        file_path = Path(doc_paths[doc_name]['original_file'])
                        if file_path.exists():
                            # Display the document name as a header
                            st.subheader(f"{doc_name}")
                            
                            # Display PDF
                            display_pdf(file_path, page_num)
                            
                            st.markdown("<hr>", unsafe_allow_html=True)
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                # Download button
                                with open(file_path, 'rb') as f:
                                    file_data = f.read()
                                st.download_button(
                                    label="Download PDF",
                                    data=file_data,
                                    file_name=doc_name,
                                    mime='application/pdf'
                                )
                            
                            with col2:
                                # Close button
                                if st.button("Close Document"):
                                    st.session_state.viewing_document = False
                                    st.rerun()
                        
                        else:
                            st.error(f"Original file not found: {file_path}")
                    else:
                        st.error(f"Document not found in cache: {doc_name}")
                except Exception as e:
                    st.error(f"Error loading document: {e}")
                
                st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
    