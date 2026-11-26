/**
 * Motor de Renderizado Canvas 2D
 * Dibuja todos los elementos visuales del escenario pixel art de la imagen:
 * - Habitación izquierda: duela de madera, libreros, reloj funcional, escritorios, computadoras CRT.
 * - Habitación derecha: alfombra azul, cuadros de arte, sofás rojos, cafetería con piso ajedrezado.
 */

import { OFFICE_CONFIG } from './config.js';

export class OfficeRenderer {
    constructor(canvas) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        this.canvas.width = OFFICE_CONFIG.CANVAS_WIDTH;
        this.canvas.height = OFFICE_CONFIG.CANVAS_HEIGHT;
        this.animTime = 0;
    }

    render(bots) {
        this.animTime += 0.05;
        const ctx = this.ctx;

        // Limpiar pantalla
        ctx.fillStyle = '#020617';
        ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

        // 1. Suelos
        this.drawFloors(ctx);

        // 2. Muros y Pasillo
        this.drawWallsAndHallway(ctx);

        // 3. Decoraciones de Pared (Reloj, Libreros, Cuadros)
        this.drawWallDecor(ctx);

        // 4. Muebles y Escritorios
        this.drawFurniture(ctx, bots);

        // 5. Renderizar Personajes (Bots) ordenados por eje Y para correcta profundidad
        const sortedBots = [...bots].sort((a, b) => a.y - b.y);
        sortedBots.forEach(bot => {
            bot.update();
            bot.draw(ctx);
        });

        // 6. Elementos que se superponen a los personajes (frente de escritorios y monitores)
        this.drawForegroundFurniture(ctx, bots);
    }

    drawFloors(ctx) {
        // Habitación Izquierda: Duela de Madera Marrón
        const off = OFFICE_CONFIG.ROOM_OFFICE;
        ctx.fillStyle = '#654321';
        ctx.fillRect(off.x, off.y, off.width, off.height);

        // Líneas de duela
        ctx.fillStyle = '#543618';
        for (let y = off.y; y < off.y + off.height; y += 18) {
            ctx.fillRect(off.x, y, off.width, 2);
        }

        // Habitación Derecha: Suelo Azul (Lounge)
        const lz = OFFICE_CONFIG.ROOM_LOUNGE;
        ctx.fillStyle = '#3a6288';
        ctx.fillRect(lz.x, lz.y, lz.width, lz.height - 140);

        // Parte Inferior Derecha: Suelo Ajedrezado (Blanco y Negro)
        const checkY = lz.y + lz.height - 140;
        const tileSize = 28;
        for (let x = lz.x; x < lz.x + lz.width; x += tileSize) {
            for (let y = checkY; y < lz.y + lz.height; y += tileSize) {
                const isWhite = ((x - lz.x) / tileSize + (y - checkY) / tileSize) % 2 === 0;
                ctx.fillStyle = isWhite ? '#e2e8f0' : '#1e293b';
                ctx.fillRect(x, y, tileSize, tileSize);
            }
        }

        // Pasillo Central Azul
        const hw = OFFICE_CONFIG.HALLWAY;
        ctx.fillStyle = '#3a6288';
        ctx.fillRect(hw.x, hw.y, hw.width, hw.height);
    }

    drawWallsAndHallway(ctx) {
        // Muros oscuros con biseles
        ctx.fillStyle = '#0f172a';
        ctx.strokeStyle = '#1e293b';
        ctx.lineWidth = 8;

        // Pared exterior izquierda
        ctx.strokeRect(OFFICE_CONFIG.ROOM_OFFICE.x, OFFICE_CONFIG.ROOM_OFFICE.y, OFFICE_CONFIG.ROOM_OFFICE.width, OFFICE_CONFIG.ROOM_OFFICE.height);
        // Pared exterior derecha
        ctx.strokeRect(OFFICE_CONFIG.ROOM_LOUNGE.x, OFFICE_CONFIG.ROOM_LOUNGE.y, OFFICE_CONFIG.ROOM_LOUNGE.width, OFFICE_CONFIG.ROOM_LOUNGE.height);

        // Muro divisor central con apertura de puerta
        ctx.fillStyle = '#090d16';
        ctx.fillRect(472, 40, 16, 180);
        ctx.fillRect(472, 380, 16, 180);
    }

    drawWallDecor(ctx) {
        // Librero 1 (Izquierda)
        ctx.fillStyle = '#854d0e';
        ctx.fillRect(80, 50, 80, 36);
        ctx.fillStyle = '#f8fafc';
        ctx.fillRect(85, 55, 70, 10); // Libros

        // Librero 2 (Centro-Izquierda)
        ctx.fillStyle = '#854d0e';
        ctx.fillRect(280, 50, 80, 36);
        ctx.fillStyle = '#f8fafc';
        ctx.fillRect(285, 55, 70, 10);

        // Reloj Funcional de Pared
        const cx = 220;
        const cy = 68;
        ctx.fillStyle = '#ffffff';
        ctx.beginPath();
        ctx.arc(cx, cy, 14, 0, Math.PI * 2);
        ctx.fill();
        ctx.strokeStyle = '#ef4444';
        ctx.lineWidth = 3;
        ctx.stroke();

        // Manecilla del reloj rotando
        ctx.strokeStyle = '#000000';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(cx, cy);
        ctx.lineTo(cx + Math.cos(this.animTime) * 8, cy + Math.sin(this.animTime) * 8);
        ctx.stroke();

        // Plantas en maceta
        this.drawPottedPlant(ctx, 50, 60);
        this.drawPottedPlant(ctx, 390, 60);
        this.drawPottedPlant(ctx, 545, 60);
        this.drawPottedPlant(ctx, 920, 60);

        // Galería de Cuadros en el Lounge
        // Cuadro pequeño 1
        ctx.fillStyle = '#ca8a04';
        ctx.fillRect(600, 55, 30, 30);
        // Cuadro panorámico central
        ctx.fillStyle = '#ca8a04';
        ctx.fillRect(680, 50, 80, 36);
        ctx.fillStyle = '#38bdf8';
        ctx.fillRect(685, 55, 70, 26);
        // Cuadro pequeño 2
        ctx.fillStyle = '#ca8a04';
        ctx.fillRect(820, 55, 30, 30);
    }

    drawPottedPlant(ctx, x, y) {
        ctx.fillStyle = '#92400e';
        ctx.fillRect(x, y + 16, 18, 16); // Maceta
        ctx.fillStyle = '#15803d';
        ctx.beginPath();
        ctx.arc(x + 9, y + 10, 12, 0, Math.PI * 2);
        ctx.fill();
    }

    drawFurniture(ctx, bots) {
        // --- ZONA DE TRABAJO ---
        // Escritorio 1 (Superior Izq)
        this.drawDesk(ctx, 130, 170, 120, 42);
        // Escritorio 2 (Superior Der)
        this.drawDesk(ctx, 310, 170, 120, 42);

        // Isla Central de 4 Escritorios
        this.drawDesk(ctx, 200, 330, 160, 100);

        // Mueble archivador y papelera (esquina inferior izq)
        ctx.fillStyle = '#b45309';
        ctx.fillRect(50, 460, 40, 60);
        ctx.fillStyle = '#94a3b8';
        ctx.beginPath();
        ctx.arc(105, 500, 8, 0, Math.PI * 2);
        ctx.fill(); // Papelera

        // --- ZONA LOUNGE ---
        // Sofás Rojos
        ctx.fillStyle = '#991b1b';
        // Sofá Izquierdo
        ctx.fillRect(630, 220, 34, 75);
        // Sofá Derecho
        ctx.fillRect(780, 220, 34, 75);
        // Sofá Superior
        ctx.fillRect(675, 185, 90, 32);
        // Sofá Inferior
        ctx.fillRect(675, 305, 90, 32);

        // Mesita de Café de madera con taza
        ctx.fillStyle = '#d97706';
        ctx.fillRect(680, 230, 80, 60);
        // Taza de café
        ctx.fillStyle = '#ffffff';
        ctx.beginPath();
        ctx.arc(710, 260, 6, 0, Math.PI * 2);
        ctx.fill();

        // Mostrador en cafetería ajedrezada
        ctx.fillStyle = '#b45309';
        ctx.fillRect(820, 490, 90, 36);
    }

    drawDesk(ctx, x, y, w, h) {
        ctx.fillStyle = '#b45309';
        ctx.fillRect(x, y, w, h);
        ctx.fillStyle = '#92400e';
        ctx.fillRect(x, y + h - 6, w, 6);
    }

    drawForegroundFurniture(ctx, bots) {
        // Dibuja las computadoras CRT encima de los escritorios con brillo interactivo
        OFFICE_CONFIG.WORKSTATIONS.forEach((ws, idx) => {
            const assignedBot = bots[idx];
            let glowColor = '#64748b'; // Apagado / Gris

            if (assignedBot && assignedBot.isRunning) {
                if (assignedBot.currentOp === 'INSERT') glowColor = '#10b981'; // Verde
                else if (assignedBot.currentOp === 'READ') glowColor = '#3b82f6'; // Azul
                else if (assignedBot.currentOp === 'UPDATE') glowColor = '#f59e0b'; // Amarillo
                else if (assignedBot.currentOp === 'DELETE') glowColor = '#ef4444'; // Rojo
                else glowColor = '#22c55e'; // Verde terminal activo
            }

            this.drawCRTMonitor(ctx, ws.deskX + 25, ws.deskY + 8, glowColor);
        });
    }

    drawCRTMonitor(ctx, x, y, glowColor) {
        // Carcasa beige retro
        ctx.fillStyle = '#cbd5e1';
        ctx.fillRect(x, y, 26, 20);
        ctx.fillStyle = '#94a3b8';
        ctx.fillRect(x + 7, y + 20, 12, 5); // Pie
        ctx.fillRect(x + 4, y + 25, 18, 3); // Base

        // Pantalla CRT
        ctx.fillStyle = '#0f172a';
        ctx.fillRect(x + 3, y + 3, 20, 14);

        // Brillo de pantalla según estado del CRUD
        ctx.fillStyle = glowColor;
        ctx.fillRect(x + 5, y + 5, 16, 10);

        // Líneas simuladas de texto retro
        ctx.fillStyle = '#ffffff';
        ctx.fillRect(x + 7, y + 7, 8, 2);
        ctx.fillRect(x + 7, y + 10, 12, 2);
    }
}