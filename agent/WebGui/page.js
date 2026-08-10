let currentInventory = null;
        let serverConnected = false;

        async function analyze() {
            const btn = document.getElementById('btnAnalyze');
            const loading = document.getElementById('loadingAnalyze');
            const status = document.getElementById('statusMessage');

            btn.disabled = true;
            loading.classList.remove('hidden');
            status.className = 'status info';
            status.textContent = 'Analisando equipamento...';

            try {
                const response = await fetch('/api/analyze', {
                    method: 'POST'
                });
                const data = await response.json();

                if (data.success) {
                    currentInventory = data.hardware;
                    document.getElementById('hardwareInfo').style.display = 'block';
                    document.getElementById('fabricante').textContent = data.hardware.equipamento.fabricante || '-';
                    document.getElementById('modelo').textContent = data.hardware.equipamento.modelo || '-';
                    document.getElementById('serial').textContent = data.hardware.equipamento.serial || '-';
                    document.getElementById('cpu').textContent = data.hardware.cpu.modelo || '-';
                    document.getElementById('memoria').textContent = data.hardware.memoria.totalGB + ' GB (' + data.hardware.memoria.modulos + ' módulos)';
                    document.getElementById('armazenamento').textContent = data.hardware.discos.map(d => d.tipo + ' ' + d.tamanhoGB + 'GB').join(', ');
                    document.getElementById('sistema').textContent = data.hardware.sistema || '-';
                    document.getElementById('arquitetura').textContent = data.hardware.arquitetura || '-';

                    status.className = 'status success';
                    status.textContent = '✅ Análise concluída com sucesso!';

                    document.getElementById('btnSaveLocal').disabled = false;
                    updateSendButton();
                } else {
                    status.className = 'status error';
                    status.textContent = '❌ ' + data.message + (data.error ? ': ' + data.error : '');
                }
            } catch (error) {
                status.className = 'status error';
                status.textContent = '❌ Erro: ' + error.message;
            } finally {
                btn.disabled = false;
                loading.classList.add('hidden');
            }
        }

        async function testServer() {
            const server = document.getElementById('serverAddress').value.trim();
            const port = parseInt(document.getElementById('serverPort').value) || 54321;
            const status = document.getElementById('serverStatus');

            status.textContent = '🔄 Testando...';

            try {
                const response = await fetch('/api/test-server', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ servidor: server, porta: port })
                });
                const data = await response.json();

                if (data.success) {
                    serverConnected = true;
                    status.innerHTML = '✅ Conectado (v' + (data.version || '1.0') + ')';
                    status.style.color = 'green';
                } else {
                    serverConnected = false;
                    status.innerHTML = '❌ ' + (data.error || 'Não disponível');
                    status.style.color = 'red';
                }

                updateSendButton();
            } catch (error) {
                serverConnected = false;
                status.innerHTML = '❌ Erro: ' + error.message;
                status.style.color = 'red';
                updateSendButton();
            }
        }

        async function saveLocal() {
            const status = document.getElementById('statusMessage');

            try {
                const response = await fetch('/api/save', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        tombo: document.getElementById('tombo').value,
                        localizacao: document.getElementById('localizacao').value,
                        observacoes: document.getElementById('observacao').value
                    })
                });
                const data = await response.json();

                if (data.success) {
                    status.className = 'status success';
                    status.textContent = '✅ ' + data.message + ' (' + data.filename + ')';
                } else {
                    status.className = 'status error';
                    status.textContent = '❌ ' + data.error;
                }
            } catch (error) {
                status.className = 'status error';
                status.textContent = '❌ Erro: ' + error.message;
            }
        }

        async function sendToServer() {
            const status = document.getElementById('statusMessage');
            const btn = document.getElementById('btnSend');
            btn.disabled = true;

            try {
                const response = await fetch('/api/send', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        servidor: document.getElementById('serverAddress').value.trim(),
                        porta: parseInt(document.getElementById('serverPort').value) || 54321,
                        tombo: document.getElementById('tombo').value,
                        localizacao: document.getElementById('localizacao').value,
                        observacoes: document.getElementById('observacao').value
                    })
                });
                const data = await response.json();

                if (data.success) {
                    status.className = 'status success';
                    status.textContent = '✅ Enviado! Tombo: ' + data.tombo + ' - Data: ' + new Date().toLocaleString();
                } else {
                    status.className = 'status error';
                    status.textContent = '❌ ' + (data.message || data.error || 'Falha no envio');
                }
            } catch (error) {
                status.className = 'status error';
                status.textContent = '❌ Erro: ' + error.message;
            } finally {
                btn.disabled = false;
            }
        }

        function updateSendButton() {
            const btn = document.getElementById('btnSend');
            const localizacao = document.getElementById('localizacao').value.trim();
            btn.disabled = !(currentInventory && serverConnected && localizacao);
        }

        document.getElementById('localizacao').addEventListener('input', updateSendButton);
        document.getElementById('tombo').addEventListener('input', updateSendButton);
        document.getElementById('observacao').addEventListener('input', updateSendButton);

        async function checkStatus() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                if (data.status === 'analisado') {
                    // Recuperar estado se possível
                }
            } catch (e) {
                // Ignorar
            }
        }
        checkStatus();
        updateSendButton();

        console.log('DataCollector iniciado!');
        console.log('Acesse http://localhost:54322 para usar');