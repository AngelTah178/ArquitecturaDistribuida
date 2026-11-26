/**
 * Generador y Renderizador de Personajes Pixel Art
 * Define 9 personajes únicos inspirados en los avatares de la imagen de referencia.
 */

export const BOT_PALETTES = [
    // Bot 1: Castaño, camisa blanca (Escritorio superior)
    { hair: '#6b3e26', skin: '#ffd1b3', shirt: '#ffffff', pants: '#2563eb' },
    // Bot 2: Rubio, camisa verde
    { hair: '#d97706', skin: '#ffe0bd', shirt: '#10b981', pants: '#1e293b' },
    // Bot 3: Cabello negro corto, camisa azul
    { hair: '#18181b', skin: '#fcd34d', shirt: '#3b82f6', pants: '#374151' },
    // Bot 4: Coleta castaña, blusa azul (Chica en pasillo)
    { hair: '#78350f', skin: '#ffd1b3', shirt: '#0284c7', pants: '#1e1b4b' },
    // Bot 5: Cabello blanco, camisa blanca (Chico abajo-izq en mesa central)
    { hair: '#e2e8f0', skin: '#ffd1b3', shirt: '#f8fafc', pants: '#475569' },
    // Bot 6: Afro oscuro, camisa naranja (Chico abajo-der en mesa central)
    { hair: '#18181b', skin: '#8d5b4c', shirt: '#f97316', pants: '#1f2937' },
    // Bot 7: Pelo negro corto, blusa roja (Chica en sofá rojo)
    { hair: '#18181b', skin: '#ffd1b3', shirt: '#ef4444', pants: '#374151' },
    // Bot 8: Cabello rizado rubio/miel, traje negro (Chica en sofá derecho)
    { hair: '#b45309', skin: '#ffe0bd', shirt: '#0f172a', pants: '#0f172a' },
    // Bot 9: Cabello grisáceo, chaleco morado
    { hair: '#64748b', skin: '#f7d3ba', shirt: '#8b5cf6', pants: '#1e293b' }
];

export class BotCharacter {
    constructor(id, palette, homeWorkstation, loungeSpot) {
        this.id = id;
        this.name = `Bot ${id}`;
        this.palette = palette;
        this.workstation = homeWorkstation;
        this.loungeSpot = loungeSpot;

        // Estado actual
        this.isRunning = false;
        this.currentOp = 'IDLE';
        this.clusterUsed = 'Inactivo';
        this.opsCount = 0;
        this.statusMessage = 'Inactivo';

        // Posición interpolada en el Canvas
        this.x = loungeSpot.x;
        this.y = loungeSpot.y;
        this.targetX = loungeSpot.x;
        this.targetY = loungeSpot.y;
        this.speed = 3.5;

        // Dirección: 'up', 'down', 'left', 'right'
        this.dir = loungeSpot.dir || 'down';
        this.animFrame = 0;
        this.lastBubbleTime = 0;
        this.speechBubble = null;
    }

    updateState(data) {
        const wasRunning = this.isRunning;
        const prevOp = this.currentOp;

        this.isRunning = data.is_running;
        this.currentOp = data.current_op || 'IDLE';
        this.clusterUsed = data.cluster_used || 'Inactivo';
        this.opsCount = data.ops_count || 0;
        this.statusMessage = data.status_message || '';

        // Si está activo, su meta es su escritorio; si no, el lounge
        if (this.isRunning) {
            this.targetX = this.workstation.sitX;
            this.targetY = this.workstation.sitY;
        } else {
            this.targetX = this.loungeSpot.x;
            this.targetY = this.loungeSpot.y;
        }

        // Si cambió a una operación CRUD activa, mostrar globo de texto
        if (this.isRunning && this.currentOp !== 'IDLE' && this.currentOp !== prevOp) {
            this.speechBubble = {
                op: this.currentOp,
                text: `${this.currentOp}: ${this.clusterUsed.replace('Cluster Mongo #', 'C')}`,
                timer: 100 // Duración en fotogramas
            };
        }
    }

    update() {
        this.animFrame++;

        // Desplazamiento suave hacia la posición objetivo
        const dx = this.targetX - this.x;
        const dy = this.targetY - this.y;
        const dist = Math.hypot(dx, dy);

        if (dist > this.speed) {
            this.x += (dx / dist) * this.speed;
            this.y += (dy / dist) * this.speed;
            if (Math.abs(dx) > Math.abs(dy)) {
                this.dir = dx > 0 ? 'right' : 'left';
            } else {
                this.dir = dy > 0 ? 'down' : 'up';
            }
        } else {
            this.x = this.targetX;
            this.y = this.targetY;
            this.dir = this.isRunning ? this.workstation.dir : this.loungeSpot.dir;
        }

        // Reducir temporizador del globo de diálogo
        if (this.speechBubble) {
            this.speechBubble.timer--;
            if (this.speechBubble.timer <= 0) {
                this.speechBubble = null;
            }
        }
    }

    draw(ctx) {
        ctx.save();
        const bx = Math.round(this.x);
        const by = Math.round(this.y);

        const isMoving = (this.x !== this.targetX || this.y !== this.targetY);
        const isTyping = (this.isRunning && !isMoving && this.currentOp !== 'IDLE');

        // Desplazamiento por animación de tecleo o caminata
        const bob = isMoving ? (Math.sin(this.animFrame * 0.3) * 2) : 0;
        const typingOffset = isTyping ? (Math.sin(this.animFrame * 0.5) * 1.5) : 0;

        // Sombra en el suelo
        ctx.fillStyle = 'rgba(0, 0, 0, 0.35)';
        ctx.beginPath();
        ctx.ellipse(bx, by + 16, 10, 5, 0, 0, Math.PI * 2);
        ctx.fill();

        // 1. Piernas / Pantalón
        ctx.fillStyle = this.palette.pants;
        ctx.fillRect(bx - 6, by + 6, 5, 10);
        ctx.fillRect(bx + 1, by + 6, 5, 10);

        // 2. Torso / Camisa
        ctx.fillStyle = this.palette.shirt;
        ctx.fillRect(bx - 8, by - 6 + typingOffset, 16, 13);

        // Brazos tecleando si está trabajando
        if (isTyping) {
            ctx.fillStyle = this.palette.skin;
            ctx.fillRect(bx - 10, by - 2 + typingOffset, 4, 6);
            ctx.fillRect(bx + 6, by - 2 + typingOffset, 4, 6);
        }

        // 3. Cabeza
        ctx.fillStyle = this.palette.skin;
        ctx.fillRect(bx - 7, by - 20 + bob, 14, 13);

        // 4. Cabello
        ctx.fillStyle = this.palette.hair;
        ctx.fillRect(bx - 8, by - 23 + bob, 16, 8);
        if (this.dir === 'left') {
            ctx.fillRect(bx - 9, by - 19 + bob, 4, 7);
        } else if (this.dir === 'right') {
            ctx.fillRect(bx + 5, by - 19 + bob, 4, 7);
        }

        // 5. Ojos
        if (this.dir !== 'up') {
            ctx.fillStyle = '#18181b';
            if (this.dir === 'left') {
                ctx.fillRect(bx - 5, by - 14 + bob, 2, 3);
            } else if (this.dir === 'right') {
                ctx.fillRect(bx + 3, by - 14 + bob, 2, 3);
            } else {
                ctx.fillRect(bx - 4, by - 14 + bob, 2, 3);
                ctx.fillRect(bx + 2, by - 14 + bob, 2, 3);
            }
        }

        // 6. Etiqueta del Bot
        ctx.font = '8px "Press Start 2P", monospace';
        ctx.textAlign = 'center';
        ctx.fillStyle = this.isRunning ? '#38bdf8' : '#94a3b8';
        ctx.fillText(this.name, bx, by - 27 + bob);

        // 7. Globo de Diálogo de Operación CRUD (Speech Bubble)
        if (this.speechBubble) {
            this.drawSpeechBubble(ctx, bx, by - 36 + bob);
        }

        ctx.restore();
    }

    drawSpeechBubble(ctx, x, y) {
        const text = this.speechBubble.text;
        ctx.font = 'bold 9px "Share Tech Mono", monospace';
        const textWidth = ctx.measureText(text).width;
        const padding = 6;
        const bw = textWidth + padding * 2;
        const bh = 18;
        const bx = x - bw / 2;
        const by = y - bh;

        // Color según la operación
        let bubbleColor = '#10b981';
        if (this.speechBubble.op === 'READ') bubbleColor = '#3b82f6';
        if (this.speechBubble.op === 'UPDATE') bubbleColor = '#f59e0b';
        if (this.speechBubble.op === 'DELETE') bubbleColor = '#ef4444';

        // Fondo del globo
        ctx.fillStyle = '#0f172a';
        ctx.strokeStyle = bubbleColor;
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.roundRect(bx, by, bw, bh, 4);
        ctx.fill();
        ctx.stroke();

        // Flechita hacia abajo
        ctx.fillStyle = bubbleColor;
        ctx.beginPath();
        ctx.moveTo(x - 3, by + bh);
        ctx.lineTo(x + 3, by + bh);
        ctx.lineTo(x, by + bh + 4);
        ctx.fill();

        // Texto
        ctx.fillStyle = bubbleColor;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(text, x, by + bh / 2);
    }
}