from langchain_community.document_loaders import AsyncChromiumLoader
from langchain_community.document_loaders import AsyncHtmlLoader

from langchain_community.document_transformers import BeautifulSoupTransformer
from langchain_community.document_transformers import Html2TextTransformer


def load_html(url):
    # Load HTML
    loader = AsyncChromiumLoader([url])
    html = loader.load()

    # Transform
    bs_transformer = BeautifulSoupTransformer()
    docs_transformed = bs_transformer.transform_documents(html, tags_to_extract=["span"])

    # Result
    return docs_transformed[0].page_content[0:500]


def load_html_2(list_urls):
    loader = AsyncHtmlLoader(list_urls)
    docs = loader.load()

    html2text = Html2TextTransformer()
    docs_transformed = html2text.transform_documents(docs)
    return docs_transformed[0].page_content[0:500]

urls = ["https://www.nu.nl/economie/6351889/consumentenbond-opent-meldpunt-voor-gedupeerden-variabel-energiecontract.html"]

if __name__ == "__main__":
    ans = load_html(urls[0])
    print(ans)

    res = load_html_2(urls)
    print(res)

