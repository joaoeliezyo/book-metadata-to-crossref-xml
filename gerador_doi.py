import csv
import uuid
import os
import webbrowser
from datetime import datetime
import xml.etree.ElementTree as ET
from xml.dom import minidom
import html

def format_xml(elem):
    """Retorna uma string XML formatada com indentação."""
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return '\n'.join([line for line in reparsed.toprettyxml(indent="  ").split('\n') if line.strip()])

def read_csv_robust(filepath):
    """Tenta ler o arquivo com diferentes codificações para evitar UnicodeDecodeError."""
    # Adicionado o utf-16 aqui
    encodings = ['utf-8', 'utf-8-sig', 'utf-16', 'latin-1', 'cp1252']
    for enc in encodings:
        try:
            with open(filepath, mode='r', encoding=enc) as f:
                return list(csv.DictReader(f))
        except UnicodeDecodeError:
            continue
    raise ValueError(f"Não foi possível ler o arquivo {filepath} com nenhuma das codificações testadas.")

def process_csvs(book_csv, chapters_csv):
    """Lê os CSVs e estrutura os dados em dicionários."""
    book_info = {}
    book_contributors = []
    
    # Processar Livro
    book_rows = read_csv_robust(book_csv)
    for row in book_rows:
        if not book_info:
            book_info = row
        book_contributors.append(row)

    # Processar Capítulos
    chapters_grouped = {}
    chapter_rows = read_csv_robust(chapters_csv)
    for row in chapter_rows:
        title = row['TITLE']
        if title not in chapters_grouped:
            chapters_grouped[title] = {
                'title': title,
                'abstract': row.get('ABSTRACT', ''),
                'doi': row['DOI'],
                'url': row['URL'],
                'first_page': row.get('FIRST_PAGE', ''),
                'last_page': row.get('LAST_PAGE', ''),
                'contributors': []
            }
        chapters_grouped[title]['contributors'].append({
            'role': row.get('ROLE_PERSON', 'Author').lower(),
            'first_name': row['FIRST_NAME_PERSON'],
            'last_name': row['LAST_NAME_PERSON'],
            'orcid': row.get('ORCID_PERSON', '')
        })

    return book_info, book_contributors, list(chapters_grouped.values())

def build_xml(book_info, book_contributors, chapters):
    """Constrói a árvore XML da Crossref."""
    batch_id = str(uuid.uuid4())
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")[:-3]

    # Constantes de Namespaces
    NS_DEFAULT = "http://www.crossref.org/schema/5.4.0"
    NS_JATS = "http://www.ncbi.nlm.nih.gov/JATS1"
    NS_XSI = "http://www.w3.org/2001/XMLSchema-instance"
    NS_XML = "http://www.w3.org/XML/1998/namespace"

    # Registra os prefixos globais para ficarem bonitos no XML final
    ET.register_namespace('', NS_DEFAULT)
    ET.register_namespace('jats', NS_JATS)
    ET.register_namespace('xsi', NS_XSI)

    # CORREÇÃO: Usando a URL completa no dicionário de atributos para evitar o erro do unbound prefix
    root = ET.Element(f"{{{NS_DEFAULT}}}doi_batch", {
        "version": "5.4.0",
        f"{{{NS_XSI}}}schemaLocation": f"{NS_DEFAULT} http://www.crossref.org/schema/deposit/crossref5.4.0.xsd"
    })

    # Head
    head = ET.SubElement(root, "head")
    ET.SubElement(head, "doi_batch_id").text = batch_id
    ET.SubElement(head, "timestamp").text = timestamp
    depositor = ET.SubElement(head, "depositor")
    ET.SubElement(depositor, "depositor_name").text = "lestue:lestue"
    ET.SubElement(depositor, "email_address").text = "editora@lestu.org"
    ET.SubElement(head, "registrant").text = "WEB-FORM"

    # Body > Book
    body = ET.SubElement(root, "body")
    book = ET.SubElement(body, "book", {"book_type": "edited_book"})
    book_metadata = ET.SubElement(book, "book_metadata")

    # Book Contributors
    contributors = ET.SubElement(book_metadata, "contributors")
    for idx, c in enumerate(book_contributors):
        person = ET.SubElement(contributors, "person_name", {
            "sequence": "first" if idx == 0 else "additional",
            "contributor_role": c.get('BOOK_ROLE_PERSON', 'author').lower()
        })
        ET.SubElement(person, "given_name").text = c['BOOK_FIRST_NAME_PERSON']
        ET.SubElement(person, "surname").text = c['BOOK_LAST_NAME_PERSON']
        if c.get('BOOK_ORCID_PERSON'):
            ET.SubElement(person, "ORCID").text = c['BOOK_ORCID_PERSON']

    # Book Title & Abstract
    titles = ET.SubElement(book_metadata, "titles")
    ET.SubElement(titles, "title").text = book_info['BOOK_TITLE']
    
    if book_info.get('BOOK_ABSTRACT'):
        # CORREÇÃO: Declarando xml:lang de forma robusta
        abstract = ET.SubElement(book_metadata, f"{{{NS_JATS}}}abstract", {f"{{{NS_XML}}}lang": "pt"})
        ET.SubElement(abstract, f"{{{NS_JATS}}}p").text = book_info['BOOK_ABSTRACT']

    # Book Publication Date
    pub_date = ET.SubElement(book_metadata, "publication_date", {"media_type": "online"})
    ET.SubElement(pub_date, "month").text = str(book_info['BOOK_MONTH_ONLINE']).zfill(2)
    ET.SubElement(pub_date, "day").text = str(book_info['BOOK_DAY_ONLINE']).zfill(2)
    ET.SubElement(pub_date, "year").text = str(book_info['BOOK_YEAR_ONLINE'])

    ET.SubElement(book_metadata, "isbn").text = book_info['BOOK_ISBN'].replace('-', '')
    
    publisher = ET.SubElement(book_metadata, "publisher")
    ET.SubElement(publisher, "publisher_name").text = book_info['BOOK_PUBLISHER']

    doi_data = ET.SubElement(book_metadata, "doi_data")
    ET.SubElement(doi_data, "doi").text = book_info['BOOK_DOI']
    ET.SubElement(doi_data, "resource").text = book_info['BOOK_URL']

    # Chapters
    for cap in chapters:
        content_item = ET.SubElement(book, "content_item", {"component_type": "chapter"})
        
        cap_contribs = ET.SubElement(content_item, "contributors")
        for idx, c in enumerate(cap['contributors']):
            person = ET.SubElement(cap_contribs, "person_name", {
                "sequence": "first" if idx == 0 else "additional",
                "contributor_role": c['role']
            })
            ET.SubElement(person, "given_name").text = c['first_name']
            ET.SubElement(person, "surname").text = c['last_name']
            if c['orcid']:
                ET.SubElement(person, "ORCID").text = c['orcid']

        cap_titles = ET.SubElement(content_item, "titles")
        ET.SubElement(cap_titles, "title").text = cap['title']

        cap_pub_date = ET.SubElement(content_item, "publication_date", {"media_type": "online"})
        ET.SubElement(cap_pub_date, "month").text = str(book_info['BOOK_MONTH_ONLINE']).zfill(2)
        ET.SubElement(cap_pub_date, "day").text = str(book_info['BOOK_DAY_ONLINE']).zfill(2)
        ET.SubElement(cap_pub_date, "year").text = str(book_info['BOOK_YEAR_ONLINE'])

        pages = ET.SubElement(content_item, "pages")
        ET.SubElement(pages, "first_page").text = cap['first_page']
        ET.SubElement(pages, "last_page").text = cap['last_page']

        cap_doi_data = ET.SubElement(content_item, "doi_data")
        ET.SubElement(cap_doi_data, "doi").text = cap['doi']
        ET.SubElement(cap_doi_data, "resource").text = cap['url']

    return format_xml(root), batch_id, timestamp

def generate_audit_html(book_info, book_contributors, chapters, batch_id, timestamp):
    """Gera um arquivo HTML com o resumo dos dados para auditoria visual."""
    html_content = f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Auditoria de Metadados - DOI Crossref</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; background-color: #f4f7f6; color: #333; margin: 0; padding: 20px; }}
            .container {{ max-width: 1000px; margin: auto; background: #fff; padding: 30px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
            h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
            h2 {{ color: #2980b9; margin-top: 30px; }}
            .metadata-box {{ background: #ecf0f1; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
            .chapter-card {{ border: 1px solid #ddd; border-left: 5px solid #3498db; padding: 15px; margin-bottom: 15px; background: #fafafa; border-radius: 4px; }}
            .chapter-title {{ font-weight: bold; font-size: 1.1em; color: #2c3e50; }}
            .authors-list {{ margin: 10px 0; padding-left: 20px; }}
            .badge {{ display: inline-block; padding: 3px 8px; font-size: 12px; background: #34495e; color: #fff; border-radius: 12px; text-transform: uppercase; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Auditoria de Metadados Gerados (Crossref)</h1>
            
            <div class="metadata-box">
                <p><strong>Batch ID Gerado:</strong> <code>{batch_id}</code></p>
                <p><strong>Timestamp:</strong> <code>{timestamp}</code></p>
            </div>

            <h2>Dados do Livro (Obra Principal)</h2>
            <div class="metadata-box">
                <p><strong>Título:</strong> {html.escape(book_info['BOOK_TITLE'])}</p>
                <p><strong>DOI:</strong> {book_info['BOOK_DOI']}</p>
                <p><strong>ISBN:</strong> {book_info['BOOK_ISBN']}</p>
                <p><strong>Editora:</strong> {book_info['BOOK_PUBLISHER']}</p>
                <p><strong>Data de Publicação Online:</strong> {str(book_info['BOOK_DAY_ONLINE']).zfill(2)}/{str(book_info['BOOK_MONTH_ONLINE']).zfill(2)}/{book_info['BOOK_YEAR_ONLINE']}</p>
                
                <h3>Organizadores / Editores:</h3>
                <ul class="authors-list">
    """
    
    for c in book_contributors:
        orcid = f" | ORCID: {c['BOOK_ORCID_PERSON']}" if c.get('BOOK_ORCID_PERSON') else ""
        html_content += f"<li>{html.escape(c['BOOK_FIRST_NAME_PERSON'])} {html.escape(c['BOOK_LAST_NAME_PERSON'])} <span class='badge'>{c.get('BOOK_ROLE_PERSON', 'AUTHOR')}</span>{orcid}</li>"

    html_content += """
                </ul>
            </div>

            <h2>Capítulos Encontrados</h2>
    """

    for i, cap in enumerate(chapters, 1):
        html_content += f"""
            <div class="chapter-card">
                <div class="chapter-title">{i}. {html.escape(cap['title'])}</div>
                <p><strong>DOI:</strong> {cap['doi']} | <strong>Páginas:</strong> {cap['first_page']} - {cap['last_page']}</p>
                <p><strong>Recurso (URL):</strong> <a href="{cap['url']}" target="_blank">{cap['url']}</a></p>
                <strong>Autores:</strong>
                <ul class="authors-list">
        """
        for autor in cap['contributors']:
            orcid = f" | ORCID: <a href='{autor['orcid']}' target='_blank'>{autor['orcid']}</a>" if autor['orcid'] else ""
            html_content += f"<li>{html.escape(autor['first_name'])} {html.escape(autor['last_name'])} <span class='badge'>{autor['role']}</span>{orcid}</li>"
        
        html_content += """
                </ul>
            </div>
        """

    html_content += """
        </div>
    </body>
    </html>
    """
    return html_content

if __name__ == "__main__":
    print("Processando arquivos CSV...")
    book_info, book_contribs, chapters = process_csvs('BOOK.csv', 'CHAPTERS.csv')
    
    print("Gerando XML...")
    xml_string, batch_id, timestamp = build_xml(book_info, book_contribs, chapters)
    
    with open('doi_gerado.xml', 'w', encoding='utf-8') as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write(xml_string)
    
    print("Gerando página de auditoria HTML...")
    html_string = generate_audit_html(book_info, book_contribs, chapters, batch_id, timestamp)
    
    html_path = os.path.abspath('auditoria_doi.html')
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_string)
    
    print(f"\nSucesso! Arquivos gerados:")
    print(f"- XML: doi_gerado.xml")
    print(f"- Auditoria: auditoria_doi.html")
    
    webbrowser.open(f"file://{html_path}")