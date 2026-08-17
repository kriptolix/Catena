let currentInventory = null;
        let serverConnected = false;

        async function analyze() {
            const btn = document.getElementById('btnAnalyze');
            const loading = document.getElementById('loadingAnalyze');
            const status = document.getElementById('statusMessage');

            btn.disabled = true;
            loading.classList.remove('hidden');
            status.className = 'status info';
            status.textContent = 'Analisando Equipment...';

            try {
                const response = await fetch('/api/analyze', {
                    method: 'POST'
                });
                const data = await response.json();

                if (data.success) {
                    currentInventory = data.hardware;
                    document.getElementById('hardwareInfo').style.display = 'block';
                    document.getElementById('manufacturer').textContent = data.hardware.equipment.manufacturer || '-';
                    document.getElementById('model').textContent = data.hardware.equipment.model || '-';
                    document.getElementById('serial').textContent = data.hardware.equipment.serial || '-';
                    document.getElementById('cpu').textContent = data.hardware.processor.model || '-';
                    document.getElementById('memory').textContent = data.hardware.memory.totalGB + ' GB (' + data.hardware.memory.modules + ' modules)';
                    document.getElementById('storage').textContent = data.hardware.disk.map(d => d.type + ' ' + d.sizeGB + 'GB').join(', ');
                    document.getElementById('system').textContent = data.hardware.system || '-';
                    document.getElementById('architecture').textContent = data.hardware.architecture || '-';

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
                        asset_number: document.getElementById('assetTag').value,
                        location: document.getElementById('location').value,
                        observacoes: document.getElementById('annotation').value
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
                        asset_number: document.getElementById('tombo').value,
                        location: document.getElementById('location').value,
                        observacoes: document.getElementById('observacao').value
                    })
                });
                const data = await response.json();

                if (data.success) {
                    status.className = 'status success';
                    status.textContent = '✅ Enviado! Tombo: ' + data.tombo + ' - date: ' + new Date().toLocaleString();
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
            const location = document.getElementById('location').value.trim();
            btn.disabled = !(currentInventory && serverConnected && location);
        }
        
        document.getElementById('assetTag').addEventListener('input', updateSendButton);
        document.getElementById('annotation').addEventListener('input', updateSendButton);
        document.getElementById('location').addEventListener('input', updateSendButton);

        async function checkStatus() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                if (data.status === 'analisado') {
                    // Recuperar status se possível
                }
            } catch (e) {
                // Ignorar
            }
        }
        checkStatus();
        updateSendButton();

        console.log('DataCollector iniciado!');
        console.log('Acesse http://localhost:54322 para usar');