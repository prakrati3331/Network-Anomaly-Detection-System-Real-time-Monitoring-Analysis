import os
import pandas as pd
import PyPDF2
import docx
from io import StringIO

def extract_text_from_file(file_path, file_extension):
    """Extract text from different file types."""
    try:
        if file_extension.lower() == '.pdf':
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = '\n'.join([page.extract_text() for page in reader.pages])
        elif file_extension.lower() in ['.docx', '.doc']:
            doc = docx.Document(file_path)
            text = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
        elif file_extension.lower() == '.txt':
            with open(file_path, 'r', encoding='utf-8') as file:
                text = file.read()
        else:
            # For CSV, read and return as is
            if file_extension.lower() == '.csv':
                return pd.read_csv(file_path)
            else:
                # Try reading as text file
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                    text = file.read()
        return text
    except Exception as e:
        raise Exception(f"Error processing file: {str(e)}")

def text_to_dataframe(text):
    """Convert extracted text to a DataFrame for processing."""
    # If text is already a DataFrame, return it
    if isinstance(text, pd.DataFrame):
        return text
        
    # Split text into lines and clean up
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    # Create a DataFrame with the text data
    df = pd.DataFrame({
        'text': lines,
        'length': [len(line) for line in lines],
        'word_count': [len(line.split()) for line in lines]
    })
    return df

def process_uploaded_file(file):
    """Process an uploaded file and return a DataFrame."""
    # Save the file temporarily
    import tempfile
    temp_dir = tempfile.mkdtemp()
    file_path = os.path.join(temp_dir, file.filename)
    file.save(file_path)
    
    # Get file extension
    _, file_extension = os.path.splitext(file.filename)
    
    try:
        # Extract text based on file type
        text = extract_text_from_file(file_path, file_extension)
        
        # If the file is CSV, text is already a DataFrame
        if isinstance(text, pd.DataFrame):
            return text
        
        # Convert text to DataFrame
        df = text_to_dataframe(text)
        
        return df
        
    except Exception as e:
        raise Exception(f"Error processing file: {str(e)}")
    finally:
        # Clean up temporary files
        try:
            os.remove(file_path)
            os.rmdir(temp_dir)
        except:
            pass