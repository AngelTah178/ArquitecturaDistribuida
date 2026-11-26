/**
 * Configuración del Escenario y Posiciones de la Oficina
 * Reproduce exactamente la distribución de la imagen pixel art:
 * - Sala Izquierda: Zona de Trabajo (Madera)
 * - Sala Derecha: Zona de Lounge (Alfombra azul y suelo ajedrezado)
 */

export const OFFICE_CONFIG = {
    CANVAS_WIDTH: 1000,
    CANVAS_HEIGHT: 600,
    SCALE: 2, // Escala de píxeles para estética retro

    // Zonas del Mapa
    ROOM_OFFICE: { x: 40, y: 40, width: 440, height: 520 },
    HALLWAY: { x: 480, y: 220, width: 50, height: 160 },
    ROOM_LOUNGE: { x: 530, y: 40, width: 430, height: 520 },

    // Estaciones de Trabajo (Escritorios y Computadoras en la sala de trabajo)
    WORKSTATIONS: [
        // 0: Escritorio Superior Izquierdo (Monitor Verde estilo Matrix)
        { id: 1, deskX: 130, deskY: 170, sitX: 190, sitY: 235, dir: 'up', screenGlow: '#10b981' },
        // 1: Escritorio Superior Derecho (Monitor Blanco)
        { id: 2, deskX: 310, deskY: 170, sitX: 370, sitY: 235, dir: 'up', screenGlow: '#e2e8f0' },

        // Isla Central de 4 Computadoras (Bots 3, 4, 5, 6)
        // 2: Puesto Arriba-Izquierda
        { id: 3, deskX: 200, deskY: 330, sitX: 205, sitY: 320, dir: 'down', screenGlow: '#3b82f6' },
        // 3: Puesto Arriba-Derecha
        { id: 4, deskX: 290, deskY: 330, sitX: 325, sitY: 320, dir: 'down', screenGlow: '#3b82f6' },
        // 4: Puesto Abajo-Izquierda (Chico cabello blanco)
        { id: 5, deskX: 200, deskY: 410, sitX: 195, sitY: 435, dir: 'right', screenGlow: '#10b981' },
        // 5: Puesto Abajo-Derecha (Chico afro camisa naranja)
        { id: 6, deskX: 290, deskY: 410, sitX: 365, sitY: 435, dir: 'left', screenGlow: '#f59e0b' },

        // Puestos Adicionales para carga alta (Bots 7, 8, 9)
        // 6: Mesa auxiliar izquierda
        { id: 7, deskX: 130, deskY: 330, sitX: 135, sitY: 350, dir: 'right', screenGlow: '#8b5cf6' },
        // 7: Mesa auxiliar derecha
        { id: 8, deskX: 390, deskY: 330, sitX: 410, sitY: 350, dir: 'left', screenGlow: '#8b5cf6' },
        // 8: Terminal de pie junto a librero
        { id: 9, deskX: 400, deskY: 170, sitX: 435, sitY: 210, dir: 'up', screenGlow: '#ec4899' }
    ],

    // Puntos de descanso en el Lounge (para bots inactivos o en break)
    LOUNGE_SPOTS: [
        // Sofá Rojo Izquierdo (Chica de rojo)
        { x: 650, y: 260, dir: 'right', pose: 'sitting' },
        // Sofá Rojo Derecho (Chica cabello rubio/traje negro)
        { x: 790, y: 270, dir: 'left', pose: 'sitting' },
        // Sofá Rojo Superior
        { x: 720, y: 200, dir: 'down', pose: 'sitting' },
        // Sofá Rojo Inferior
        { x: 720, y: 340, dir: 'up', pose: 'sitting' },
        // Cafetería Ajedrezada (Barra/Mesa)
        { x: 600, y: 460, dir: 'down', pose: 'standing' },
        { x: 700, y: 460, dir: 'down', pose: 'standing' },
        { x: 800, y: 460, dir: 'left', pose: 'standing' },
        { x: 860, y: 460, dir: 'left', pose: 'standing' },
        // Curioso en la Galería de Cuadros
        { x: 720, y: 120, dir: 'up', pose: 'standing' }
    ]
};