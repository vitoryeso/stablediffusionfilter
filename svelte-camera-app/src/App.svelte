<script>
    import { onMount } from 'svelte';

    let videoElement;
    let canvasElement;
    let generatedImageSrc = ''; // Para armazenar a imagem gerada
    let userPrompt = "big forest environment. fantasy, detailed, cartoon"; // Prompt padrão
    let captureInterval; // Para armazenar o intervalo de captura

    async function startCamera() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ video: true });
            videoElement.srcObject = stream;

            // Inicia a captura de frames após o canvas estar pronto
            captureInterval = setInterval(async () => {
                await captureFrame();
            }, 1000); // Ajuste o intervalo conforme necessário
        } catch (error) {
            console.error("Erro ao acessar a webcam:", error);
        }
    }

    // Função para capturar o frame da webcam
    async function captureFrame() {
        if (!canvasElement) return; // Verifica se o canvasElement está definido

        const context = canvasElement.getContext('2d');
        context.drawImage(videoElement, 0, 0, canvasElement.width, canvasElement.height);

        const frame = canvasElement.toDataURL('image/jpeg'); // Converte o frame para base64

        // Enviar a imagem para a API
        await sendRequest('http://192.168.120.143:5000/generate', frame);
    }

    // Função para enviar a imagem para a API e receber a imagem gerada
    async function sendRequest(apiUrl, frame) {
        try {
            const response = await fetch(apiUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    prompt: userPrompt, // Usar o prompt do usuário
                    control_image: frame.split(',')[1] // Enviando apenas a parte base64
                })
            });

            if (response.ok) {
                const data = await response.json();
                generatedImageSrc = `data:image/png;base64,${data.generated_image}`;
            } else {
                console.error("Erro:", await response.json());
            }
        } catch (error) {
            console.error("Erro ao enviar requisição:", error);
        }
    }

    function stopCapturing() {
        clearInterval(captureInterval); // Para o envio das requisições
    }

    onMount(() => {
        startCamera();
    });
</script>

<style>
    .camera-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        height: 100vh;
        background-color: #f0f0f0;
        padding: 20px;
    }

    .video-image-container {
        display: flex;
        justify-content: space-around;
        width: 100%;
    }

    video {
        border-radius: 12px;
        box-shadow: 0px 4px 20px rgba(0, 0, 0, 0.2);
        width: 640px;
        height: 480px;
    }

    img {
        margin-left: 20px;
        border-radius: 12px;
        box-shadow: 0px 4px 20px rgba(0, 0, 0, 0.2);
        width: 640px; /* Ajuste a largura se necessário */
        height: 480px; /* Ajuste a altura se necessário */
    }

    canvas {
        display: none; /* Esconde o canvas, já que só precisamos dele para processar a imagem */
    }

    .controls {
        margin-top: 20px;
        display: flex;
        flex-direction: column;
        align-items: center;
    }

    input {
        margin-top: 10px;
        padding: 10px;
        width: 300px; /* Ajuste a largura do campo de texto conforme necessário */
    }

    button {
        margin-top: 10px;
        padding: 10px 20px;
        cursor: pointer;
        background-color: #007bff;
        color: white;
        border: none;
        border-radius: 5px;
    }

    button:hover {
        background-color: #0056b3;
    }
</style>

<div class="camera-container">
    <div class="video-image-container">
        <video bind:this={videoElement} autoplay playsinline></video>
        {#if generatedImageSrc}
            <img src={generatedImageSrc} alt="Imagem gerada" />
        {/if}
    </div>
    <div class="controls">
        <input 
            type="text" 
            bind:value={userPrompt} 
            placeholder="Digite seu prompt aqui" 
        />
        <button on:click={stopCapturing}>Stop</button>
    </div>
    <canvas bind:this={canvasElement} width="640" height="480"></canvas>
</div>
