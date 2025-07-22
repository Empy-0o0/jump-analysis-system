import cv2
import numpy as np
import mediapipe as mp
from jump_analyzer import EstadoSalto
import logging

class InterfazVisual:
    """
    Clase para la interfaz visual moderna del sistema de análisis de saltos.
    Implementa elementos UI modernos usando OpenCV con diseño limpio y profesional.
    
    Desarrollado para Ergo SaniTas SpA - Medicina Deportiva
    """
    
    # Paleta de colores moderna
    COLORS = {
        'primary': (50, 150, 200),      # Azul profesional
        'secondary': (100, 100, 100),   # Gris neutro
        'success': (50, 200, 50),       # Verde éxito
        'warning': (0, 165, 255),       # Naranja advertencia
        'danger': (0, 50, 200),         # Rojo peligro
        'info': (200, 200, 0),          # Cyan información
        'background': (30, 30, 30),     # Fondo oscuro
        'text_primary': (255, 255, 255), # Texto principal
        'text_secondary': (200, 200, 200), # Texto secundario
        'accent': (255, 200, 0),        # Acento dorado
        'ergo_blue': (200, 100, 50),    # Azul corporativo Ergo SaniTas
        'ergo_green': (100, 200, 100)   # Verde corporativo
    }
    
    @staticmethod
    def dibujar_contenedor_moderno(img, text, x, y, width, height, bg_color, text_color, 
                                  font_scale=0.7, border_radius=5, icon=None):
        """Dibuja un contenedor moderno con bordes redondeados simulados"""
        # Fondo principal
        overlay = img.copy()
        cv2.rectangle(overlay, (x, y), (x + width, y + height), bg_color, -1)
        cv2.addWeighted(overlay, 0.8, img, 0.2, 0, img)
        
        # Borde sutil
        cv2.rectangle(img, (x, y), (x + width, y + height), InterfazVisual.COLORS['secondary'], 1)
        
        # Texto centrado
        text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 2)[0]
        text_x = x + (width - text_size[0]) // 2
        text_y = y + (height + text_size[1]) // 2
        
        cv2.putText(img, text, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 
                   font_scale, text_color, 2)

    @staticmethod
    def dibujar_barra_potencia_moderna(img, potencia, x, y, width, height):
        """Dibuja una barra de potencia moderna con gradiente"""
        # Fondo de la barra
        cv2.rectangle(img, (x, y), (x + width, y + height), InterfazVisual.COLORS['background'], -1)
        cv2.rectangle(img, (x, y), (x + width, y + height), InterfazVisual.COLORS['secondary'], 2)
        
        # Calcular altura de llenado
        fill_height = int((potencia / 100) * height)
        
        if fill_height > 0:
            # Crear gradiente de color basado en el nivel
            for i in range(fill_height):
                pos_y = y + height - i - 1
                ratio = i / height
                
                # Gradiente de color: rojo -> naranja -> verde
                if ratio < 0.33:
                    color = InterfazVisual.COLORS['danger']
                elif ratio < 0.66:
                    color = InterfazVisual.COLORS['warning']
                else:
                    color = InterfazVisual.COLORS['success']
                
                cv2.line(img, (x + 3, pos_y), (x + width - 3, pos_y), color, 2)
        
        # Etiquetas
        cv2.putText(img, "EXPLOSIVIDAD", (x - 30, y - 15), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, InterfazVisual.COLORS['text_primary'], 1)
        cv2.putText(img, f"{potencia:.0f}%", (x + 5, y + height + 25), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, InterfazVisual.COLORS['accent'], 2)

    @staticmethod
    def dibujar_header_corporativo(img, usuario_nombre="", session_info=""):
        """Dibuja el header corporativo de Ergo SaniTas SpA"""
        h, w = img.shape[:2]
        header_height = 80
        
        # Fondo del header
        overlay = img.copy()
        cv2.rectangle(overlay, (0, 0), (w, header_height), InterfazVisual.COLORS['background'], -1)
        cv2.addWeighted(overlay, 0.9, img, 0.1, 0, img)
        
        # Línea superior corporativa
        cv2.rectangle(img, (0, 0), (w, 5), InterfazVisual.COLORS['ergo_blue'], -1)
        
        # Logo/Título corporativo
        cv2.putText(img, "ERGO SANITAS SpA", (20, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, InterfazVisual.COLORS['ergo_blue'], 2)
        cv2.putText(img, "Sistema de Analisis Biomecanico", (20, 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, InterfazVisual.COLORS['text_secondary'], 1)
        
        # Información del usuario (lado derecho)
        if usuario_nombre:
            text_size = cv2.getTextSize(usuario_nombre, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
            cv2.putText(img, f"Atleta: {usuario_nombre}", (w - text_size[0] - 20, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, InterfazVisual.COLORS['text_primary'], 2)
        
        if session_info:
            text_size = cv2.getTextSize(session_info, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
            cv2.putText(img, session_info, (w - text_size[0] - 20, 55), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, InterfazVisual.COLORS['text_secondary'], 1)
        
        # Línea separadora
        cv2.line(img, (0, header_height), (w, header_height), InterfazVisual.COLORS['secondary'], 2)

    @staticmethod
    def dibujar_panel_metricas(img, metricas, x, y, width, height):
        """Dibuja un panel moderno con métricas clave"""
        # Fondo del panel
        overlay = img.copy()
        cv2.rectangle(overlay, (x, y), (x + width, y + height), InterfazVisual.COLORS['background'], -1)
        cv2.addWeighted(overlay, 0.85, img, 0.15, 0, img)
        
        # Borde del panel
        cv2.rectangle(img, (x, y), (x + width, y + height), InterfazVisual.COLORS['ergo_blue'], 2)
        
        # Título del panel
        cv2.putText(img, "METRICAS EN TIEMPO REAL", (x + 10, y + 25), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, InterfazVisual.COLORS['ergo_blue'], 2)
        
        # Línea separadora
        cv2.line(img, (x + 10, y + 35), (x + width - 10, y + 35), 
                InterfazVisual.COLORS['secondary'], 1)
        
        # Mostrar métricas
        y_offset = 55
        for key, value in metricas.items():
            if isinstance(value, float):
                text = f"{key}: {value:.2f}"
            else:
                text = f"{key}: {value}"
            
            cv2.putText(img, text, (x + 15, y + y_offset), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, InterfazVisual.COLORS['text_primary'], 1)
            y_offset += 25

    @staticmethod
    def dibujar_monitor_tecnico_avanzado(img, errores, x, y):
        """Dibuja un monitor técnico avanzado con indicadores visuales mejorados"""
        cv2.putText(img, "MONITOR TECNICO AVANZADO", (x, y - 25), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, InterfazVisual.COLORS['ergo_blue'], 2)
        
        errores_monitor = [
            ("insufficient_cm_depth", "CM INSUF."),
            ("rodillas_valgo_takeoff", "VALGO ROD."),
            ("stiff_landing", "ATER. RIGIDO"),
            ("insufficient_plantarflexion", "EMPUJE TOB.")
        ]
        
        for i, (error_key, error_short) in enumerate(errores_monitor):
            y_pos = y + i * 35
            error_count = errores.get(error_key, 0)
            
            # Determinar color basado en severidad
            if error_count == 0:
                color = InterfazVisual.COLORS['success']
            elif error_count <= 2:
                color = InterfazVisual.COLORS['warning']
            else:
                color = InterfazVisual.COLORS['danger']
            
            # Indicador circular
            cv2.circle(img, (x, y_pos), 12, color, -1)
            cv2.circle(img, (x, y_pos), 12, InterfazVisual.COLORS['text_primary'], 2)
            
            # Texto del error
            cv2.putText(img, error_short, (x + 25, y_pos + 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, InterfazVisual.COLORS['text_primary'], 1)
            
            # Contador de errores
            if error_count > 0:
                cv2.putText(img, f"({error_count})", (x + 120, y_pos + 5), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)

    @staticmethod
    def dibujar_grafico_altura_mejorado(img, historial_pos_y_cadera, initial_hip_y, px_to_m, 
                                       jump_height_m_actual=0, estado_actual=None):
        """Dibuja un gráfico mejorado de altura con mejor visualización"""
        if len(historial_pos_y_cadera) < 2:
            return

        h, w = img.shape[:2]
        graph_height = 150
        graph_width = 300
        start_x = w - graph_width - 30
        start_y = h - graph_height - 50
        
        # Fondo del gráfico
        overlay = img.copy()
        cv2.rectangle(overlay, (start_x, start_y), (start_x + graph_width, start_y + graph_height), 
                     InterfazVisual.COLORS['background'], -1)
        cv2.addWeighted(overlay, 0.8, img, 0.2, 0, img)
        
        # Borde del gráfico
        cv2.rectangle(img, (start_x, start_y), (start_x + graph_width, start_y + graph_height), 
                     InterfazVisual.COLORS['ergo_blue'], 2)

        # Título del gráfico
        cv2.putText(img, "TRAYECTORIA DE SALTO", (start_x + 10, start_y - 10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, InterfazVisual.COLORS['ergo_blue'], 1)

        # Información de altura actual
        cv2.putText(img, f"Altura: {jump_height_m_actual:.2f}m", 
                   (start_x + 10, start_y + graph_height + 25), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, InterfazVisual.COLORS['accent'], 2)

    @staticmethod
    def dibujar_pantalla_calibracion(img, progreso, mensaje=""):
        """Dibuja la pantalla de calibración con indicadores visuales"""
        h, w = img.shape[:2]
        
        # Fondo semitransparente
        overlay = img.copy()
        cv2.rectangle(overlay, (0, 0), (w, h), InterfazVisual.COLORS['background'], -1)
        cv2.addWeighted(overlay, 0.7, img, 0.3, 0, img)
        
        # Título principal
        cv2.putText(img, "CALIBRACION DEL SISTEMA", (w//2 - 200, h//2 - 100), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.0, InterfazVisual.COLORS['ergo_blue'], 3)
        
        # Barra de progreso
        bar_width = 400
        bar_height = 30
        bar_x = w//2 - bar_width//2
        bar_y = h//2 - 50
        
        # Fondo de la barra
        cv2.rectangle(img, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), 
                     InterfazVisual.COLORS['secondary'], -1)
        
        # Progreso
        progress_width = int((progreso / 100) * bar_width)
        cv2.rectangle(img, (bar_x, bar_y), (bar_x + progress_width, bar_y + bar_height), 
                     InterfazVisual.COLORS['success'], -1)
        
        # Borde de la barra
        cv2.rectangle(img, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), 
                     InterfazVisual.COLORS['text_primary'], 2)
        
        # Porcentaje
        cv2.putText(img, f"{progreso:.0f}%", (w//2 - 20, bar_y + 20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, InterfazVisual.COLORS['text_primary'], 2)

    @staticmethod
    def dibujar_resumen_sesion(img, resultados):
        """Dibuja el resumen final de la sesión"""
        h, w = img.shape[:2]
        
        # Fondo
        overlay = img.copy()
        cv2.rectangle(overlay, (50, 50), (w-50, h-50), InterfazVisual.COLORS['background'], -1)
        cv2.addWeighted(overlay, 0.9, img, 0.1, 0, img)
        
        # Borde
        cv2.rectangle(img, (50, 50), (w-50, h-50), InterfazVisual.COLORS['ergo_blue'], 3)
        
        # Título
        cv2.putText(img, "RESUMEN DE SESION", (w//2 - 150, 100), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.0, InterfazVisual.COLORS['ergo_blue'], 3)
        
        # Información básica
        usuario = resultados.get('usuario', {})
        cv2.putText(img, f"Atleta: {usuario.get('nombre', 'N/A')}", (70, 140), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, InterfazVisual.COLORS['text_primary'], 2)

    @staticmethod
    def dibujar_panel_ayuda(img):
        """Dibuja el panel de ayuda con controles"""
        h, w = img.shape[:2]
        
        # Panel de ayuda en la esquina superior derecha
        panel_width = 200
        panel_height = 120
        panel_x = w - panel_width - 10
        panel_y = 90
        
        # Fondo del panel
        overlay = img.copy()
        cv2.rectangle(overlay, (panel_x, panel_y), (panel_x + panel_width, panel_y + panel_height), 
                     InterfazVisual.COLORS['background'], -1)
        cv2.addWeighted(overlay, 0.8, img, 0.2, 0, img)
        
        # Título
        cv2.putText(img, "CONTROLES", (panel_x + 10, panel_y + 20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, InterfazVisual.COLORS['ergo_blue'], 1)
        
        # Controles
        controles = [
            "1-CMJ  2-SQJ  3-Abalakov",
            "R-Reiniciar  Q-Salir",
            "C-Recalibrar  H-Ayuda"
        ]
        
        for i, control in enumerate(controles):
            cv2.putText(img, control, (panel_x + 10, panel_y + 45 + i*20), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, InterfazVisual.COLORS['text_secondary'], 1)
