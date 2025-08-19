/**
 * content_script.js
 * Este script roda no contexto da página web para extrair metadados.
 */

function scrapePage() {
    const metadata = {};
    const creators = [];

    // Tenta obter o título da página
    metadata.title = document.title;

    // Scraper para tags <meta name="citation_...">
    const metaTags = document.getElementsByTagName('meta');
    for (const tag of metaTags) {
        const name = tag.getAttribute('name');
        const content = tag.getAttribute('content');
        if (!name || !content) continue;

        switch (name.toLowerCase()) {
            case 'citation_title':
                metadata.title = content;
                break;
            case 'citation_author':
                // Simplificado: apenas divide o nome. Uma solução real seria mais robusta.
                const names = content.split(' ');
                creators.push({
                    first_name: names.slice(0, -1).join(' '),
                    last_name: names.slice(-1)[0] || '',
                    creator_type: 'author'
                });
                break;
            case 'citation_doi':
                metadata.doi = content;
                break;
            case 'citation_journal_title':
                metadata.publicationTitle = content;
                break;
            case 'citation_publication_date':
                metadata.date = content;
                break;
            case 'citation_abstract_html_url':
                metadata.url = content;
                break;
        }
    }

    // Se a URL não foi encontrada nas tags, pega a URL da página
    if (!metadata.url) {
        metadata.url = window.location.href;
    }

    return {
        item_type: 'journalArticle', // Default, poderia ser mais inteligente
        metadata: metadata,
        creators: creators
    };
}

// Ouve por mensagens do background script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "get_page_data") {
        const pageData = scrapePage();
        sendResponse(pageData);
    }
    // Retorna true para indicar que a resposta será enviada de forma assíncrona.
    return true;
});
