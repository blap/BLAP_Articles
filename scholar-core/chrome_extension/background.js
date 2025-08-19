/**
 * background.js
 * O service worker da extensão. Lida com a comunicação com o host nativo.
 */

const nativeHostName = "com.my_company.scholarcore";

// Ouve por cliques no ícone da extensão
chrome.action.onClicked.addListener((tab) => {
    console.log("Ícone da extensão clicado. Solicitando dados da página...");

    // Envia uma mensagem para o content script da aba ativa
    chrome.tabs.sendMessage(tab.id, { action: "get_page_data" }, (response) => {
        if (chrome.runtime.lastError) {
            console.error("Erro ao enviar mensagem para o content script:", chrome.runtime.lastError.message);
            // Poderia atualizar o popup para mostrar um erro aqui
            return;
        }

        if (response) {
            console.log("Dados recebidos do content script:", response);

            // Verifica se algum dado útil foi extraído
            if (response.metadata && response.metadata.title) {
                console.log("Enviando dados para o host nativo...");

                // Conecta e envia a mensagem para o host nativo
                const port = chrome.runtime.connectNative(nativeHostName);
                port.postMessage(response);

                port.onMessage.addListener((message) => {
                    console.log("Resposta recebida do host nativo:", message);
                    // Aqui você poderia atualizar o popup da extensão com o status
                });

                port.onDisconnect.addListener(() => {
                    if (chrome.runtime.lastError) {
                        console.error("Desconectado com erro:", chrome.runtime.lastError.message);
                    } else {
                        console.log("Desconectado do host nativo.");
                    }
                });

            } else {
                console.log("Nenhum dado útil encontrado na página.");
                // Poderia atualizar o popup para mostrar que nada foi encontrado
            }
        }
    });
});
