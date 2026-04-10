# Book Metadata to Crossref XML

Este projeto consiste em um script Python que converte metadados de livros e seus respectivos capítulos a partir de arquivos CSV para um arquivo XML no formato aceito para depósito de DOIs na Crossref. Adicionalmente, o script gera um relatório em HTML para demonstrar visualmente os dados estruturados e facilitar a auditoria antes do depósito.

## Requisitos

- Python 3.x instalado no sistema. 
O script utiliza apenas bibliotecas padrão do Python (como `csv`, `xml`, `os` e `uuid`), não sendo necessária a instalação de pacotes externos ou do gerenciador `pip`.

## Como Executar

1. Clone ou baixe este repositório para o seu computador.
2. Certifique-se de que os arquivos de dados `BOOK.csv` e `CHAPTERS.csv` estejam presentes no mesmo nível de diretório que o script `gerador_doi.py`.
3. Abra o terminal (ou prompt de comando), navegue até a raiz do projeto e execute o seguinte comando:
   
   ```bash
   python gerador_doi.py
   ```

4. Após a execução bem-sucedida, o script criará ou substituirá dois arquivos de saída no mesmo diretório:
   - `doi_gerado.xml`: O arquivo principal já estruturado no padrão Crossref 5.4.0.
   - `auditoria_doi.html`: Uma página web contendo todas as relações de autoria, dados e URLs extraídos. O script abrirá este relatório automaticamente em seu navegador padrão.

## Estrutura e Formatação dos Arquivos CSV

O bom funcionamento do script depende da formatação dos dois arquivos contendo a tabela de dados: `BOOK.csv` (dados globais do livro e organizadores) e `CHAPTERS.csv` (dados de capítulos e seus autores).

### Codificação (Encoding) e Delimitadores

- **Codificação**: Recomenda-se salvar o documento adotando a formatação UTF-8 ou UTF-16. O código possui um leitor que tentará decodificar o arquivo rodando pelas codificações `utf-8`, `utf-8-sig`, `utf-16`, `latin-1` e `cp1252` visando driblar erros comuns de exportação pelo Excel.
- **Delimitadores**: É mandatório salvar o arquivo utilizando vírgulas (`,`) e proteger blocos de texto maiores adotando aspas duplas (`"`). As aspas impedem que o script quebre a linha ou a coluna caso haja vírgulas e aspas simples dentro do título ou do resumo do artigo.

### Estrutura do `BOOK.csv`

O arquivo lida com os autores ou organizadores do livro atrelados aos dados fundamentais da publicação principal.

**Colunas obrigatórias de cabeçalho:**
`BOOK_TYPE`, `BOOK_TITLE`, `BOOK_LANG_ABSTRACT`, `BOOK_ABSTRACT`, `BOOK_DOI`, `BOOK_URL`, `BOOK_ROLE_PERSON`, `BOOK_FIRST_NAME_PERSON`, `BOOK_LAST_NAME_PERSON`, `BOOK_ORCID_PERSON`, `BOOK_AFFILIATION_PERSON`, `BOOK_ROR_ID_PERSON`, `BOOK_PUBLISHER`, `BOOK_ISBN`, `BOOK_EDITION`, `BOOK_YEAR_ONLINE`, `BOOK_MONTH_ONLINE`, `BOOK_DAY_ONLINE`

Caso algum dado não conste ou deva ser em branco (ex: `BOOK_EDITION`), mantenha a estrutura da coluna respeitando os delimitadores.

### Estrutura do `CHAPTERS.csv`

Este arquivo relaciona todos os múltiplos capítulos presentes e os expande para relacionar os diversos autores por ordem. Assim como no livro, o nome do capítulo repetido na linha subsequente atrela os demais autores dele.

**Colunas obrigatórias de cabeçalho:**
`TITLE`, `LANG_ABSTRACT`, `ABSTRACT`, `ROLE_PERSON`, `FIRST_NAME_PERSON`, `LAST_NAME_PERSON`, `ORCID_PERSON`, `AFFILIATION_PERSON`, `ROR_ID_PERSON`, `DOI`, `URL`, `FIRST_PAGE`, `LAST_PAGE`

*Nota: Garanta que todas as URLs (como em DOI ou ORCID) estejam completas na planilha correspondente para a respectiva submissão via `resource` no XML contanto inclusive o protocolo http ou https dependendo caso.*

## Visualização e Exemplos

Para melhor compreensão, confira abaixo como os arquivos são estruturados e o resultado gerado pelo script considerando os dados de exemplo preenchidos no repositório.

### 1. Dados de Entrada (CSVs)

**Visão do arquivo `BOOK.csv` (Exemplo):**
Este arquivo lista as propriedades da obra central. Note que para múltiplos organizadores, a mesma linha é repetida, mudando apenas os parâmetros referentes aos dados do autor (`João Silva` e `Maria Oliveira`).

| BOOK_TYPE | BOOK_TITLE | BOOK_DOI | BOOK_ROLE_PERSON | BOOK_FIRST_NAME_PERSON | BOOK_LAST_NAME_PERSON | BOOK_PUBLISHER |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| EDITED BOOK | Avanços Tecnológicos e Sociedade | 10.5555/mock.978-00... | AUTHOR | João | Silva | Editora Mockup |
| EDITED BOOK | Avanços Tecnológicos e Sociedade | 10.5555/mock.978-00... | AUTHOR | Maria | Oliveira | Editora Mockup |

**Visão do arquivo `CHAPTERS.csv` (Exemplo):**
Cada capítulo segue a mesma lógica da listagem anterior. O capítulo "O Futuro do Trabalho Remoto" possui dois autores distintos, gerando duas linhas consecutivas e permitindo ao robô conectá-los na ordem.

| TITLE | ROLE_PERSON | FIRST_NAME_PERSON | LAST_NAME_PERSON | DOI | FIRST_PAGE | LAST_PAGE |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| A Inteligência Artificial no Cotidiano | Author | Pedro | Santos | 10.5555/mock.../cap1 | 10 | 25 |
| Privacidade de Dados e Regulamentações | Author | Carlos | Souza | 10.5555/mock.../cap2 | 26 | 40 |
| O Futuro do Trabalho Remoto | Author | Maria | Oliveira | 10.5555/mock.../cap3 | 41 | 60 |
| O Futuro do Trabalho Remoto | Author | João | Silva | 10.5555/mock.../cap3 | 41 | 60 |

### 2. Relatório de Auditoria (`auditoria_doi.html`)

O relatório HTML gerado funciona como um "print" e painel visual que agrupa as informações de forma humanamente legível para conferência de segurança. O modelo na tela terá aproximadamente o seguinte corpo de texto renderizado em caixas de verificação limpas:

> **Auditoria de Metadados Gerados (Crossref)**
> Batch ID Gerado: `6d692334-4017-47f3-acf8-c32b7a7ceda3`
> 
> **Dados do Livro (Obra Principal)**
> **Título:** Avanços Tecnológicos e Sociedade: Perspectivas Futuras - Vol. 01
> **DOI:** 10.5555/mock.978-00-00000-00-0
> **Editora:** Editora Mockup
> - João Silva [AUTHOR] | ORCID: https://orcid.org/0000...0001
> - Maria Oliveira [AUTHOR] | ORCID: https://orcid.org/0000...0002
>
> **Capítulos Encontrados**
> 1. A Inteligência Artificial no Cotidiano (Páginas: 10 - 25)
> - Pedro Santos [Author] | ORCID: https://orcid.org/0000...0003
> - Ana Costa [Author]

*Assegure-se de abrir este arquivo antes de enviar os dados para a plataforma da Crossref.*

### 3. Arquivo XML para submissão (`doi_gerado.xml`)

Abaixo é apresentada uma demonstração unificada do XML limpo gerado pelo código que envelopa perfeitamente os autores secundários em `<person_name sequence="additional">` e o conteúdo das submissões usando a sintaxe exigida pelo XSD do sistema Crossref 5.4.0.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<doi_batch xmlns="http://www.crossref.org/schema/5.4.0" version="5.4.0">
  <head>
    <doi_batch_id>6d692334-4017-4015-acf8-c37b7a8ceda3</doi_batch_id>
    <!-- ... -->
  </head>
  <body>
    <book book_type="edited_book">
      <!-- Obra principal -->
      <book_metadata>
        <contributors>
          <person_name sequence="first" contributor_role="author">
            <given_name>João</given_name>
            <surname>Silva</surname>
            <ORCID>https://orcid.org/0000-0000-0000-0001</ORCID>
          </person_name>
          <person_name sequence="additional" contributor_role="author">
            <given_name>Maria</given_name>
            <surname>Oliveira</surname>
            <ORCID>https://orcid.org/0000-0000-0000-0002</ORCID>
          </person_name>
        </contributors>
        <titles>
          <title>Avanços Tecnológicos e Sociedade: Perspectivas Futuras - Vol. 01</title>
        </titles>
        <doi_data>
          <doi>10.5555/mock.978-00-00000-00-0</doi>
          <resource>https://mockeditora.org/books/1</resource>
        </doi_data>
        <!-- ... -->
      </book_metadata>
      
      <!-- Capítulo de Exemplo Interno -->
      <content_item component_type="chapter">
        <contributors>
          <person_name sequence="first" contributor_role="author">
            <given_name>Pedro</given_name>
            <surname>Santos</surname>
            <ORCID>https://orcid.org/0000-0000-0000-0003</ORCID>
          </person_name>
          <person_name sequence="additional" contributor_role="author">
            <given_name>Ana</given_name>
            <surname>Costa</surname>
          </person_name>
        </contributors>
        <titles>
          <title>A Inteligência Artificial no Cotidiano</title>
        </titles>
        <pages>
          <first_page>10</first_page>
          <last_page>25</last_page>
        </pages>
        <doi_data>
          <doi>10.5555/mock.978-00-00000-00-0/cap1</doi>
          <resource>https://mockeditora.org/books/1/cap1</resource>
        </doi_data>
      </content_item>
      
      <!-- ... Demais capítulos da obra renderizados logo abaixo ... -->
    </book>
  </body>
</doi_batch>
```
# book-metadata-to-crossref-xml
