import os
import pdfrw

def merge_pdfs():
    """
    Merges all PDF files in the specified directory into a single PDF file.
    """
    # Define the directory containing PDF files
    pdf_dir = r"C:/Users/kunw/OneDrive - KUNW-MSFT/2025 Spring Tax Return/2024PFICs/f8621"
    
    # Define the output file path
    output_path = os.path.join(pdf_dir, "merged_pfics.pdf")
    
    # Get all PDF files in the directory
    pdf_files = [os.path.join(pdf_dir, f) for f in os.listdir(pdf_dir) 
                if f.lower().endswith('.pdf')]
    
    if not pdf_files:
        print(f"No PDF files found in {pdf_dir}")
        return
    
    # Sort the files to ensure consistent ordering
    pdf_files.sort()
    
    # Create a PDF writer object
    writer = pdfrw.PdfWriter()
    
    # Add each PDF file to the writer
    for pdf_file in pdf_files:
        try:
            reader = pdfrw.PdfReader(pdf_file)
            writer.addpages(reader.pages)
            print(f"Added {pdf_file}")
        except Exception as err:
            print(f"Error processing {pdf_file}: {err}")
    
    # Write the merged PDF to the output file
    writer.write(output_path)
    print(f"Merged PDF saved to {output_path}")

if __name__ == "__main__":
    merge_pdfs()
