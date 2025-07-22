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
    def dibujar_header_corporativo(img, usuario_nombre="", session_info=""):
        """
        Dibuja el header corporativo de Ergo SaniTas SpA
        
        Args:
            img: Imagen donde dibujar
            usuario_nombre: Nombre del usuario/atleta
            session_info: Información de la sesión
        """
        h, w = img.shape[:2]
        header_height = 80
        
        # Fondo del header con gradiente simulado
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
    def dibujar_contenedor_moderno(img, text, x, y, width, height, bg_color, text_color, 
                                  font_scale=0.7, border_radius=5, icon=None):
        """
        Dibuja un contenedor moderno con bordes redondeados simulados
        
        Args:
            img: Imagen donde dibujar
            text: Texto a mostrar
            x, y: Posición
            width, height: Dimensiones
            bg_color: Color de fondo
            text_color: Color del texto
            font_scale: Escala de la fuente
            border_radius: Radio del borde (simulado)
            icon: Icono opcional (no implementado por restricciones)
        """
        # Fondo principal
        overlay = img.copy()
        cv2.rectangle(overlay, (x, y), (x + width, y + height), bg_color, -1)
        cv2.addWeighted(overlay, 0.8, img, 0.2, 0, img)
        
        # Borde sutil
        cv2.rectangle(img, (x, y), (x + width, y + height), InterfazVisual.COLORS['secondary'], 1)
        
        # Efecto de profundidad (sombra simulada)
        shadow_offset = 2
        cv2.rectangle(img, (x + shadow_offset, y + shadow_offset), 
                     (x + width + shadow_offset, y + height + shadow_offset), 
                     (20, 20, 20), -1)
        cv2.rectangle(img, (x, y), (x + width, y + height), bg_color, -1)
        cv2.rectangle(img, (x, y), (x + width, y + height), InterfazVisual.COLORS['text_secondary'], 1)
        
        # Texto centrado
        text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 2)[0]
        text_x = x + (width - text_size[0]) // 2
        text_y = y + (height + text_size[1]) // 2
        
        cv2.putText(img, text, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 
                   font_scale, text_color, 2)

    @staticmethod
    def dibujar_barra_potencia_moderna(img, potencia, x, y, width, height):
        """
        Dibuja una barra de potencia moderna con gradiente y animación
        
        Args:
            img: Imagen donde dibujar
            potencia: Valor de potencia (0-100)
            x, y: Posición
            width, height: Dimensiones
        """
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
                
                # Línea con intensidad variable
                intensity = min(255, int(150 + (ratio * 105)))
                adjusted_color = tuple(min(255, int(c * intensity / 255)) for c in color)
                
                cv2.line(img, (x + 3, pos_y), (x + width - 3, pos_y), adjusted_color, 2)
        
        # Etiquetas
        cv2.putText(img, "EXPLOSIVIDAD", (x - 30, y - 15), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, InterfazVisual.COLORS['text_primary'], 1)
        cv2.putText(img, f"{potencia:.0f}%", (x + 5, y + height + 25), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, InterfazVisual.COLORS['accent'], 2)
        
        # Marcadores de nivel
        for level in [25, 50, 75]:
            marker_y = y + height - int((level / 100) * height)
            cv2.line(img, (x - 5, marker_y), (x, marker_y), InterfazVisual.COLORS['text_secondary'], 1)
            cv2.putText(img, f"{level}", (x - 25, marker_y + 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.3, InterfazVisual.COLORS['text_secondary'], 1)

    @staticmethod
    def dibujar_panel_metricas(img, metricas, x, y, width, height):
        """
        Dibuja un panel moderno con métricas clave
        
        Args:
            img: Imagen donde dibujar
            metricas: Diccionario con métricas a mostrar
            x, y: Posición
            width, height: Dimensiones
        """
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
        """
        Dibuja un monitor técnico avanzado con indicadores visuales mejorados
        
        Args:
            img: Imagen donde dibujar
            errores: Diccionario de errores detectados
            x, y: Posición
        """
        cv2.putText(img, "MONITOR TECNICO AVANZADO", (x, y - 25), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, InterfazVisual.COLORS['ergo_blue'], 2)
        
        errores_monitor = [
            ("insufficient_cm_depth", "Profundidad CM", "CM INSUF."),
            ("prematura_extension", "Extensión Prematura", "EXT. PREM."),
            ("rodillas_valgo_takeoff", "Valgo Rodillas", "VALGO ROD."),
            ("insufficient_plantarflexion", "Empuje Tobillo", "EMPUJE TOB."),
            ("stiff_landing", "Aterrizaje Rígido", "ATER. RIGIDO"),
            ("landing_imbalance", "Desequilibrio", "DESEQUIL."),
            ("excessive_landing_impact", "Impacto Excesivo", "IMPACTO EXC."),
            ("trunk_lean_takeoff_landing", "Inclinación Tronco", "INCL. TRONCO")
        ]
        
        for i, (error_key, error_desc, error_short) in enumerate(errores_monitor):
            y_pos = y + i * 35
            error_count = errores.get(error_key, 0)
            
            # Determinar color basado en severidad
            if error_count == 0:
                color = InterfazVisual.COLORS['success']
                status = "OK"
            elif error_count <= 2:
                color = InterfazVisual.COLORS['warning']
                status = "ATENCION"
            else:
                color = InterfazVisual.COLORS['danger']
                status = "CRITICO"
            
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
        """
        Dibuja un gráfico mejorado de altura con mejor visualización
        
        Args:
            img: Imagen donde dibujar
            historial_pos_y_cadera: Historial de posiciones Y de cadera
            initial_hip_y: Posición inicial de cadera
            px_to_m: Factor de conversión píxeles a metros
            jump_height_m_actual: Altura actual del salto
            estado_actual: Estado actual del salto
        """
        if len(historial_pos_y_cadera) < 2:
            return

        h, w = img.shape[:2]
        graph_height = 150
        graph_width = 300
        start_x = w - graph_width - 30
        start_y = h - graph_height - 50
        
        # Fondo del gráfico con transparencia
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

        # Procesar datos
        data_to_plot = np.array(historial_pos_y_cadera)
        min_y_data = np.min(data_to_plot)
        max_y_data = np.max(data_to_plot)
        
        effective_y_range = (max_y_data - min_y_data) + (0.2 * abs(initial_hip_y - min_y_data))
        if effective_y_range == 0: 
            effective_y_range = 1

        # Dibujar líneas de cuadrícula
        for i in range(5):
            grid_y = start_y + (i * graph_height // 4)
            cv2.line(img, (start_x, grid_y), (start_x + graph_width, grid_y), 
                    InterfazVisual.COLORS['secondary'], 1)

        # Dibujar puntos de datos
        puntos = []
        max_points = 60
        start_index = max(0, len(historial_pos_y_cadera) - max_points)
        
        for i in range(start_index, len(historial_pos_y_cadera)):
            x = start_x + int((i - start_index) * graph_width / min(max_points, len(historial_pos_y_cadera) - start_index))
            y_normalized = (historial_pos_y_cadera[i] - min_y_data) / effective_y_range
            y = start_y + int((1 - y_normalized) * graph_height)
            puntos.append((x, y))

        # Dibujar línea de trayectoria con color según estado
        if len(puntos) > 1:
            color_linea = InterfazVisual.COLORS['success']
            if estado_actual == EstadoSalto.CONTRAMOVIMIENTO:
                color_linea = InterfazVisual.COLORS['warning']
            elif estado_actual == EstadoSalto.DESPEGUE:
                color_linea = InterfazVisual.COLORS['info']
            elif estado_actual == EstadoSalto.VUELO:
                color_linea = InterfazVisual.COLORS['accent']
            elif estado_actual == EstadoSalto.ATERRIZAJE:
                color_linea = InterfazVisual.COLORS['danger']
            
            for i in range(1, len(puntos)):
                cv2.line(img, puntos[i-1], puntos[i], color_linea, 3)
        
        # Línea de referencia
        ref_y_normalized = (initial_hip_y - min_y_data) / effective_y_range
        ref_y_px_on_graph = start_y + int((1 - ref_y_normalized) * graph_height)
        cv2.line(img, (start_x, ref_y_px_on_graph), (start_x + graph_width, ref_y_px_on_graph), 
                InterfazVisual.COLORS['text_secondary'], 2)
        cv2.putText(img, "REF", (start_x - 35, ref_y_px_on_graph + 5), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, InterfazVisual.COLORS['text_secondary'], 1)

        # Información de altura actual
        cv2.putText(img, f"Altura: {jump_height_m_actual:.2f}m", 
                   (start_x + 10, start_y + graph_height + 25), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, InterfazVisual.COLORS['accent'], 2)

    @staticmethod
    def dibujar_guias_visuales_avanzadas(img, lm, estado_salto, analizador):
        """
        Dibuja guías visuales avanzadas con mejor feedback visual
        
        Args:
            img: Imagen donde dibujar
            lm: Landmarks de MediaPipe
            estado_salto: Estado actual del salto
            analizador: Instancia del analizador
        """
        if not lm: 
            return
        
        try:
            h, w, _ = img.shape
            
            def get_px_coords(landmark_enum):
                p = lm[landmark_enum.value]
                return np.array([int(p.x * w), int(p.y * h)])

            # Obtener coordenadas de landmarks clave
            lshoulder_px = get_px_coords(mp.solutions.pose.PoseLandmark.LEFT_SHOULDER)
            rshoulder_px = get_px_coords(mp.solutions.pose.PoseLandmark.RIGHT_SHOULDER)
            lhip_px = get_px_coords(mp.solutions.pose.PoseLandmark.LEFT_HIP)
            rhip_px = get_px_coords(mp.solutions.pose.PoseLandmark.RIGHT_HIP)
            lknee_px = get_px_coords(mp.solutions.pose.PoseLandmark.LEFT_KNEE)
            rknee_px = get_px_coords(mp.solutions.pose.PoseLandmark.RIGHT_KNEE)
            lankle_px = get_px_coords(mp.solutions.pose.PoseLandmark.LEFT_ANKLE)
            rankle_px = get_px_coords(mp.solutions.pose.PoseLandmark.RIGHT_ANKLE)
            
            # Colores según el estado del salto
            color_esqueleto = InterfazVisual.COLORS['success']
            if estado_salto == EstadoSalto.CONTRAMOVIMIENTO:
                color_esqueleto = InterfazVisual.COLORS['warning']
            elif estado_salto == EstadoSalto.DESPEGUE:
                color_esqueleto = InterfazVisual.COLORS['info']
            elif estado_salto == EstadoSalto.VUELO:
                color_esqueleto = InterfazVisual.COLORS['accent']
            elif estado_salto == EstadoSalto.ATERRIZAJE:
                color_esqueleto = InterfazVisual.COLORS['danger']
            
            # Líneas del esqueleto con grosor variable según estado
            line_thickness = 3 if estado_salto != EstadoSalto.INICIAL else 2
            
            # Línea de columna (hombro-cadera)
            cv2.line(img, lshoulder_px, lhip_px, color_esqueleto, line_thickness)
            cv2.line(img, rshoulder_px, rhip_px, color_esqueleto, line_thickness)

            # Línea de pierna (cadera-rodilla-tobillo)
            cv2.line(img, lhip_px, lknee_px, color_esqueleto, line_thickness)
            cv2.line(img, lknee_px, lankle_px, color_esqueleto, line_thickness)
            cv2.line(img, rhip_px, rknee_px, color_esqueleto, line_thickness)
            cv2.line(img, rknee_px, rankle_px, color_esqueleto, line_thickness)

            # Línea horizontal de rodillas para valgo con indicador visual mejorado
            if estado_salto in [EstadoSalto.CONTRAMOVIMIENTO, EstadoSalto.DESPEGUE, EstadoSalto.ATERRIZAJE]:
                knee_color = InterfazVisual.COLORS['success']
                current_knee_x_diff = abs(lm[mp.solutions.pose.PoseLandmark.LEFT_KNEE.value].x - 
                                        lm[mp.solutions.pose.PoseLandmark.RIGHT_KNEE.value].x)
                
                if (current_knee_x_diff * analizador.px_to_m) < (analizador.initial_knee_x_diff * analizador.px_to_m - 
                                                               analizador.umbrales["rodillas_valgo_tolerancia_x"]):
                    knee_color = InterfazVisual.COLORS['danger']
                    # Indicador de advertencia parpadeante
                    cv2.putText(img, "¡ATENCION RODILLAS!", (w//2 - 100, 100), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, InterfazVisual.COLORS['danger'], 2)
                
                cv2.line(img, lknee_px, rknee_px, knee_color, 4)

            # Indicadores de aterrizaje suave
            if estado_salto == EstadoSalto.ATERRIZAJE:
                landing_color = InterfazVisual.COLORS['info']
                if analizador.errores.get("stiff_landing", 0) > 0:
                    landing_color = InterfazVisual.COLORS['danger']
                
                # Círculos pulsantes en los pies
                cv2.circle(img, lankle_px, 20, landing_color, 3)
                cv2.circle(img, rankle_px, 20, landing_color, 3)
                cv2.circle(img, lankle_px, 10, landing_color, -1)
                cv2.circle(img, rankle_px, 10, landing_color, -1)
                
            # Instrucciones contextuales mejoradas
            InterfazVisual._dibujar_instrucciones_contextuales(img, estado_salto, w, h)
                
        except Exception as e:
            logging.warning(f"Error dibujando guías visuales: {e}")

    @staticmethod
    def _dibujar_instrucciones_contextuales(img, estado_salto, w, h):
        """
        Dibuja instrucciones contextuales según el estado del salto
        
        Args:
            img: Imagen donde dibujar
            estado_salto: Estado actual del salto
            w, h: Dimensiones de la imagen
        """
        # Fondo semitransparente para las instrucciones
        overlay = img.copy()
        cv2.rectangle(overlay, (w//2 - 200, 20), (w//2 + 200, 120), 
                     InterfazVisual.COLORS['background'], -1)
        cv2.addWeighted(overlay, 0.8, img, 0.2, 0, img)
        
        # Borde del panel de instrucciones
        cv2.rectangle(img, (w//2 - 200, 20), (w//2 + 200, 120), 
                     InterfazVisual.COLORS['ergo_blue'], 2)
        
        if estado_salto == EstadoSalto.INICIAL:
            cv2.putText(img, "POSICION INICIAL", (w//2 - 80, 45), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, InterfazVisual.COLORS['ergo_blue'], 2)
            cv2.putText(img, "Mantengase erguido y relajado", (w//2 - 120, 70), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, InterfazVisual.COLORS['text_primary'], 1)
            cv2.putText(img, "Pies al ancho de hombros", (w//2 - 100, 90), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, InterfazVisual.COLORS['text_secondary'], 1)
                       
        elif estado_salto == EstadoSalto.CONTRAMOVIMIENTO:
            cv2.putText(img, "CONTRAMOVIMIENTO", (w//2 - 90, 45), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, InterfazVisual.COLORS['warning'], 2)
            cv2.putText(img, "Flexione rodillas y caderas", (w//2 - 110, 70), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, InterfazVisual.COLORS['text_primary'], 1)
            cv2.putText(img, "Mantenga tronco recto", (w//2 - 90, 90), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, InterfazVisual.COLORS['text_secondary'], 1)

        elif estado_salto == EstadoSalto.DESPEGUE:
            cv2.putText(img, "¡DESPEGUE!", (w//2 - 60, 45), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, InterfazVisual.COLORS['success'], 2)
            cv2.putText(img, "Empuje con fuerza maxima", (w//2 - 110, 70), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, InterfazVisual.COLORS['text_primary'], 1)
            cv2.putText(img, "Extienda completamente", (w//2 - 90, 90), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, InterfazVisual.COLORS['text_secondary'], 1)

        elif estado_salto == EstadoSalto.VUELO:
            cv2.putText(img, "¡EN VUELO!", (w//2 - 60, 45), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, InterfazVisual.COLORS['accent'], 2)
            cv2.putText(img, "Prepare el aterrizaje", (w//2 - 90, 70), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, InterfazVisual.COLORS['text_primary'], 1)
            cv2.putText(img, "Flexione para absorber", (w//2 - 95, 90), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, InterfazVisual.COLORS['text_secondary'], 1)

        elif estado_salto == EstadoSalto.ATERRIZAJE:
            cv2.putText(img, "ATERRIZAJE", (w//2 - 60, 45), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, InterfazVisual.COLORS['danger'], 2)
            cv2.putText(img, "Flexione rodillas al caer", (w//2 - 110, 70), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, InterfazVisual.COLORS['text_primary'], 1)
            cv2.putText(img, "Absorba el impacto", (w//2 - 80, 90), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, InterfazVisual.COLORS['text_secondary'], 1)

    @staticmethod
    def dibujar_pantalla_calibracion(img, progreso, mensaje=""):
        """
        Dibuja la pantalla de calibración con indicadores visuales
        
        Args:
            img: Imagen donde dibujar
            progreso: Progreso de calibración (0-100)
            mensaje: Mensaje adicional
        """
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
        
        # Instrucciones
        instrucciones = [
            "Mantengase en posicion estable",
            "Pies al ancho de hombros",
            "Brazos ligeramente separados del cuerpo",
            "Mire hacia la camara"
        ]
        
        for i, instruccion in enumerate(instrucciones):
            cv2.putText(img, instruccion, (w//2 - 150, h//2 + 20 + i*30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, InterfazVisual.COLORS['text_secondary'], 1)
        
        # Mensaje adicional
        if mensaje:
            cv2.putText(img, mensaje, (w//2 - 100, h//2 + 150), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, InterfazVisual.COLORS['warning'], 2)

    @staticmethod
    def dibujar_resumen_sesion(img, resultados):
        """
        Dibuja el resumen final de la sesión
        
        Args:
            img: Imagen donde dibujar
            resultados: Diccionario con resultados de la sesión
        """
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
        
        # Información del usuario
        usuario = resultados.get('usuario', {})
        cv2.putText(img, f"Atleta: {usuario.get('nombre', 'N/A')}", (70, 140), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, InterfazVisual.COLORS['text_primary'], 2)
        
        # Métricas principales
        metricas = resultados.get('metricas', {})
        sesion = resultados.get('sesion', {})
        evaluacion = resultados.get('evaluacion', {})
        
        y_pos = 180
        info_items = [
            f"Saltos Totales: {sesion.get('total', 0)}",
            f"Saltos Correctos: {sesion.get('correctas', 0)}",
            f"Precision: {sesion.get('precision', 0):.1f}%",
            f"Altura Promedio: {metricas.get('altura_salto_promedio', 0)*100:.1f} cm",
            f"Potencia Promedio: {metricas.get('potencia_promedio', 0):.0f} W",
            f"Clasificacion: {evaluacion.get('nivel_usuario_final', 'N/A')}",
            f"Puntuacion Tecnica: {evaluacion.get('puntuacion_tecnica', 0):.1f}/100"
        ]
        
        for item in info_items:
            cv2.putText(img, item, (70, y_pos), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, InterfazVisual.COLORS['text_primary'], 1)
            y_pos += 35
        
        # Recomendaciones
        cv2.putText(img, "RECOMENDACIONES:", (70, y_pos + 20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, InterfazVisual.COLORS['ergo_green'], 2)
        
        recomendaciones = resultados.get('recomendaciones', [])[:3]  # Mostrar solo las primeras 3
        for i, rec in enumerate(recomendaciones):
            cv2.putText(img, f"• {rec}", (70, y_pos + 60 + i*25), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, InterfazVisual.COLORS['text_secondary'], 1)

    @staticmethod
    def dibujar_panel_ayuda(img):
        """
        Dibuja el panel de ayuda con controles
        
        Args:
            img: Imagen donde dibujar
        """
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
        
        # Borde
        cv2.rectangle(img, (panel_x, panel_y), (panel_x + panel_width, panel_y + panel_height), 
                     InterfazVisual.COLORS['secondary'], 1)
        
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
</read_file>
