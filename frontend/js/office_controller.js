/**
 * Controlador de Estado y Conexión en Tiempo Real con FastAPI
 * Realiza el sondeo (polling), maneja el botón maestro de encendido de bots
 * y actualiza los registros del terminal inferior.
 */

import { OFFICE_CONFIG } from './config.js';
import { BOT_PALETTES, BotCharacter } from './bot_sprites.js';
import { OfficeRenderer } from './office_renderer.js';

class OfficeApp {
    constructor() {
        this.canvas = document.getElementById('officeCanvas');
        this.renderer = new OfficeRenderer(this.canvas);

        // Inicializar los 9 bots
        this.bots = [];
        for (let i = 1; i <= 9; i++) {
            const palette = BOT_PALETTES[i - 1];
            const workstation = OFFICE_CONFIG.WORKSTATIONS[i - 1];
            const loungeSpot = OFFICE_CONFIG.LOUNGE_SPOTS[i - 1];
            this.bots.push(new BotCharacter(i, palette, workstation, loungeSpot));
        }

        this.isAutoRunning = true;
        this.selectedBotsCount = 3; // Inicia con 3 bots (Cluster 1)
        this.logHistory = [];

        this.initUI();
        this.startLoop();
        this.pollBackend();
        setInterval(() => this.pollBackend(), 1000);
    }

    initUI() {
        this.btnMaster = document.getElementById('btnMasterToggle');
        this.masterText = document.getElementById('masterToggleText');
        this.masterLed = document.getElementById('masterLed');
        this.logContainer = document.getElementById('logTerminal');

        // Botón Maestro de Encendido/Apagado
        this.btnMaster.addEventListener('click', () => {
            this.toggleAutoBots();
        });

        // Botones de Escala Concurrente (1, 3, 5, 8 bots)
        document.querySelectorAll('.btn-scale').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const count = parseInt(e.target.dataset.count);
                this.setBotsCount(count);
            });
        });

        // Botón de Sincronización Manual ETL
        document.getElementById('btnSync').addEventListener('click', async () => {
            try {
                const res = await fetch('/sincronizacion/trigger', { method: 'POST' });
                const data = await res.json();
                this.addLog('SISTEMA', `ETL Ejecutado Manualmente: ${data.resumen?.mensaje || 'Completado'}`);
            } catch (err) {
                console.error('Error al forzar ETL:', err);
            }
        });
    }

    async toggleAutoBots() {
        if (this.isAutoRunning) {
            // Apagar todos los bots
            await fetch('/api/v1/bots/stop', { method: 'POST' });
            this.isAutoRunning = false;
            this.btnMaster.classList.add('stopped');
            this.masterLed.classList.add('off');
            this.masterText.innerText = 'ENCENDER BOTS (AUTO)';
            this.addLog('SISTEMA', 'Simulación Automática DETENIDA. Bots enviados al Lounge.');
        } else {
            // Encender bots con la cantidad seleccionada
            await fetch(`/api/v1/bots/control?count=${this.selectedBotsCount}`, { method: 'POST' });
            this.isAutoRunning = true;
            this.btnMaster.classList.remove('stopped');
            this.masterLed.classList.remove('off');
            this.masterText.innerText = 'APAGAR BOTS (AUTO)';
            this.addLog('SISTEMA', `Simulación Automática ACTIVADA (${this.selectedBotsCount} Bots trabajando).`);
        }
    }

    async setBotsCount(count) {
        this.selectedBotsCount = count;
        document.querySelectorAll('.btn-scale').forEach(b => {
            b.classList.toggle('active', parseInt(b.dataset.count) === count);
        });

        if (this.isAutoRunning) {
            await fetch(`/api/v1/bots/control?count=${count}`, { method: 'POST' });
            this.addLog('ENRUTADOR', `Ajuste de Concurrencia a ${count} bots.`);
        }
    }

    async pollBackend() {
        try {
            // 1. Consultar estado individual de los bots
            const resBots = await fetch('/api/v1/bots/status');
            const botsData = await resBots.json();

            let activeCount = 0;
            botsData.forEach((data, idx) => {
                const bot = this.bots[idx];
                const prevOp = bot.currentOp;
                bot.updateState(data);

                if (data.is_running) {
                    activeCount++;
                    // Si el bot realizó una nueva operación CRUD, registrar en terminal
                    if (data.current_op !== 'IDLE' && data.current_op !== prevOp) {
                        this.addLog(bot.name, `${data.current_op} en ${data.cluster_used} | ${data.status_message}`);
                    }
                }
            });

            // Actualizar estado del botón según la respuesta del backend
            if (activeCount > 0 && !this.isAutoRunning) {
                this.isAutoRunning = true;
                this.btnMaster.classList.remove('stopped');
                this.masterLed.classList.remove('off');
                this.masterText.innerText = 'APAGAR BOTS (AUTO)';
            }

            // 2. Consultar semáforo de sincronización ETL
            const resSync = await fetch('/sincronizacion');
            const syncData = await resSync.json();
            const syncLabel = document.getElementById('syncStatusText');
            const syncDot = document.getElementById('syncStatusDot');

            if (syncData.estado === 'EN_EJECUCION') {
                syncLabel.innerText = 'ETL en ejecución';
                syncDot.style.background = '#f59e0b';
            } else if (syncData.estado === 'ERROR') {
                syncLabel.innerText = 'ETL con error';
                syncDot.style.background = '#ef4444';
            } else {
                syncLabel.innerText = 'Sincronizado';
                syncDot.style.background = '#10b981';
            }

            // 3. Actualizar indicador de Cluster en la barra
            const clusterSpan = document.getElementById('activeClusterText');
            if (activeCount <= 3) clusterSpan.innerText = 'Cluster Mongo #1 activo (Bots 1-3)';
            else if (activeCount <= 6) clusterSpan.innerText = 'Clusters Mongo #1 & #2 activos (Bots 1-6)';
            else clusterSpan.innerText = 'Clusters Mongo #1, #2 & #3 activos (Bots 1-9)';

        } catch (err) {
            // Backend desconectado o iniciando
        }
    }

    addLog(source, message) {
        const time = new Date().toLocaleTimeString();
        const entry = document.createElement('div');
        entry.className = 'log-entry';

        // Determinar etiqueta CRUD si aplica
        let badgeHTML = '';
        if (message.includes('INSERT')) badgeHTML = '<span class="legend-badge badge-INSERT">INSERT</span>';
        else if (message.includes('READ')) badgeHTML = '<span class="legend-badge badge-READ">READ</span>';
        else if (message.includes('UPDATE')) badgeHTML = '<span class="legend-badge badge-UPDATE">UPDATE</span>';
        else if (message.includes('DELETE')) badgeHTML = '<span class="legend-badge badge-DELETE">DELETE</span>';

        entry.innerHTML = `
      <span class="log-time">[${time}]</span>
      <span class="log-bot">${source}:</span>
      ${badgeHTML}
      <span class="log-desc">${message}</span>
    `;

        this.logContainer.prepend(entry);

        // Mantener solo los últimos 40 registros
        while (this.logContainer.children.length > 40) {
            this.logContainer.removeChild(this.logContainer.lastChild);
        }
    }

    startLoop() {
        const loop = () => {
            this.renderer.render(this.bots);
            requestAnimationFrame(loop);
        };
        requestAnimationFrame(loop);
    }
}

// Inicializar la aplicación al cargar el DOM
window.addEventListener('DOMContentLoaded', () => {
    new OfficeApp();
});