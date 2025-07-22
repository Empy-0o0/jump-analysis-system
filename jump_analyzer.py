import cv2
import mediapipe as mp
import numpy as np
import time
import logging
import math
from datetime import datetime
from collections import deque
from enum import Enum
import yaml

# Cargar configuración
try:
    with open('config_Saltos.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    ROM_OPTIMO_SALTO = config.get('rom_optimo_salto', {})
    PARAMETROS_SALTO = config.get('parametros_salto', {})
    NIVEL_USUARIO = config.get('nivel_usuario', {})
except FileNotFoundError:
    logging.error("config_Saltos.yaml no encontrado. Usando parámetros por defecto.")
    ROM_OPTIMO_SALTO = {
        "rodilla": {
            "flexion_min_cm": 90,
            "flexion_objetivo_cm": 70,
            "extension_takeoff": 170,
            "flexion_landing_max": 90,
            "extension_landing_min": 160
        },
        "cadera": {
            "flexion_min_cm": 100,
            "extension_takeoff": 170,
            "flexion_landing_max": 90
        },
        "tobillo": {
            "dorsiflexion_cm": 70,
            "plantarflexion_takeoff": 160,
            "dorsiflexion_landing": 80
        },
        "columna": {
            "alineacion_general": 170,
            "inclinacion_tronco_max": 30
        }
    }
    PARAMETROS_SALTO = {
        "min_flight_time": 0.15,
        "min_vertical_displacement_m": 0.10,
        "max_landing_time": 0.5,
        "rodillas_valgo_tolerancia_x": 0.04,
        "stiff_landing_tolerance": 10,
        "max_landing_impact_angle_vel": 1.5
    }
    NIVEL_USUARIO = {
        'principiante': {
            'tolerancia_angulo': 20,
            'velocidad_cm_min': 0.10,
            'velocidad_takeoff_min': 0.4,
            'rango_minimo_cm': 70
        },
        'intermedio': {
            'tolerancia_angulo': 10,
            'velocidad_cm_min': 0.20,
            'velocidad_takeoff_min': 0.8,
            'rango_minimo_cm': 80
        },
        'avanzado': {
            'tolerancia_angulo': 5,
            'velocidad_cm_min': 0.30,
            'velocidad_takeoff_min': 1.2,
            'rango_minimo_cm': 90
        }
    }

# --- Clases de Excepciones Personalizadas ---
class PoseDetectionError(Exception):
    """Excepción para errores en la detección de pose."""
    pass

class CalibrationError(Exception):
    """Excepción para errores durante la calibración."""
    pass

# --- Enum para Estados de Salto ---
class EstadoSalto(Enum):
    INICIAL = "INICIAL"
    CONTRAMOVIMIENTO = "CONTRAMOVIMIENTO"
    DESPEGUE = "DESPEGUE"
    VUELO = "VUELO"
    ATERRIZAJE = "ATERRIZAJE"
    ESTABLE_POST_ATERRIZAJE = "ESTABLE_POST_ATERRIZAJE"

# --- Enum para Tipos de Salto ---
class TipoSalto(Enum):
    CMJ = "Counter Movement Jump (CMJ)"
    SQJ = "Squat Jump (SQJ)"
    ABALAKOV = "Abalakov"

# --- Rangos de referencia para clasificación ---
RANGOS_CLASIFICACION = {
    'hombres': {
        'CMJ': {'bajo': (0, 30), 'medio': (30, 40), 'avanzado': (40, 50), 'elite': (50, 100)},
        'SQJ': {'bajo': (0, 25), 'medio': (25, 35), 'avanzado': (35, 45), 'elite': (45, 100)},
        'ABALAKOV': {'bajo': (0, 35), 'medio': (35, 45), 'avanzado': (45, 55), 'elite': (55, 100)}
    },
    'mujeres': {
        'CMJ': {'bajo': (0, 22), 'medio': (22, 30), 'avanzado': (30, 38), 'elite': (38, 100)},
        'SQJ': {'bajo': (0, 18), 'medio': (18, 25), 'avanzado': (25, 33), 'elite': (33, 100)},
        'ABALAKOV': {'bajo': (0, 25), 'medio': (25, 35), 'avanzado': (35, 43), 'elite': (43, 100)}
    }
}

class AnalizadorSaltos:
    """
    Clase principal para el análisis biomecánico de saltos en tiempo real.
    Implementa una máquina de estados para detectar y evaluar las diferentes
    fases del salto: contramovimiento, despegue, vuelo y aterrizaje.
    
    Desarrollado para Ergo SaniTas SpA - Medicina Deportiva
    """
    
    def __init__(self, usuario):
        self.usuario = usuario
        self.contador = 0
        self.correctas = 0
        self.estado = EstadoSalto.INICIAL
        self.errores = {
            "insufficient_cm_depth": 0,
            "prematura_extension": 0,
            "rodillas_valgo_takeoff": 0,
            "insufficient_plantarflexion": 0,
            "stiff_landing": 0,
            "landing_imbalance": 0,
            "excessive_landing_impact": 0,
            "trunk_lean_takeoff_landing": 0
        }
        
        # Pesos de gravedad para diferentes tipos de errores
        self.gravedad_errores = {
            "insufficient_cm_depth": 1,
            "prematura_extension": 2,
            "rodillas_valgo_takeoff": 2,
            "insufficient_plantarflexion": 1,
            "stiff_landing": 2,
            "landing_imbalance": 1.5,
            "excessive_landing_impact": 1.5,
            "trunk_lean_takeoff_landing": 1
        }
        
        self.potencia = 0.0
        self.potencia_target = 0.0
        self.frame_count = 0
        self.buenos_frames = 0
        self.calibrado = False
        self.ultimo_tiempo = time.time()

        # Variables de estado del salto
        self.initial_hip_y = 0
        self.initial_knee_x_diff = 0
        self.max_hip_y_cm = 0
        self.min_hip_y_flight = float('inf')
        self.takeoff_time = 0
        self.landing_time = 0
        self.peak_flight_time = 0
        self.jump_height_m = 0
        self.tipo_salto = TipoSalto.CMJ

        # Historial para análisis temporal
        self.historial_angulos_rodilla = []
        self.historial_angulos_cadera = []
        self.historial_pos_y_cadera = []
        self.historial_tiempos = []
        self.mensajes_feedback = []

        # Métricas de rendimiento
        self.alturas_saltos = []
        self.tiempos_vuelo = []
        self.potencias = []
        self.indice_elasticidad = 0.0
        self.indice_coordinacion = 0.0

        # Deques para suavizado de ángulos
        self.smoothed_knee_angles = deque(maxlen=5)
        self.smoothed_hip_angles = deque(maxlen=5)
        self.smoothed_ankle_angles = deque(maxlen=5)
        self.smoothed_trunk_angles = deque(maxlen=5)

        # Configurar umbrales biomecánicos
        self._configurar_umbrales()
        self.px_to_m = 0

    def _configurar_umbrales(self):
        """Configura los umbrales biomecánicos basados en la configuración"""
        self.umbrales = {
            "rodilla_flexion_min_cm": ROM_OPTIMO_SALTO["rodilla"]["flexion_min_cm"],
            "rodilla_flexion_objetivo_cm": ROM_OPTIMO_SALTO["rodilla"]["flexion_objetivo_cm"],
            "rodilla_extension_takeoff": ROM_OPTIMO_SALTO["rodilla"]["extension_takeoff"],
            "rodilla_flexion_landing_max": ROM_OPTIMO_SALTO["rodilla"]["flexion_landing_max"],
            "rodilla_extension_landing_min": ROM_OPTIMO_SALTO["rodilla"]["extension_landing_min"],

            "cadera_flexion_min_cm": ROM_OPTIMO_SALTO["cadera"]["flexion_min_cm"],
            "cadera_extension_takeoff": ROM_OPTIMO_SALTO["cadera"]["extension_takeoff"],
            "cadera_flexion_landing_max": ROM_OPTIMO_SALTO["cadera"]["flexion_landing_max"],

            "tobillo_dorsiflexion_cm": ROM_OPTIMO_SALTO["tobillo"]["dorsiflexion_cm"],
            "tobillo_plantarflexion_takeoff": ROM_OPTIMO_SALTO["tobillo"]["plantarflexion_takeoff"],
            "tobillo_dorsiflexion_landing": ROM_OPTIMO_SALTO["tobillo"]["dorsiflexion_landing"],

            "columna_alineacion_general": ROM_OPTIMO_SALTO["columna"]["alineacion_general"],
            "inclinacion_tronco_max": ROM_OPTIMO_SALTO["columna"]["inclinacion_tronco_max"],

            "min_flight_time": PARAMETROS_SALTO["min_flight_time"],
            "min_vertical_displacement_m": PARAMETROS_SALTO["min_vertical_displacement_m"],
            "max_landing_time": PARAMETROS_SALTO["max_landing_time"],
            "rodillas_valgo_tolerancia_x": PARAMETROS_SALTO["rodillas_valgo_tolerancia_x"],
            "stiff_landing_tolerance": PARAMETROS_SALTO["stiff_landing_tolerance"],
            "max_landing_impact_angle_vel": PARAMETROS_SALTO["max_landing_impact_angle_vel"]
        }

    def set_tipo_salto(self, tipo_salto: TipoSalto):
        """
        Establece el tipo de salto a analizar y proporciona instrucciones específicas.
        
        Args:
            tipo_salto (TipoSalto): Tipo de salto a analizar
        """
        self.tipo_salto = tipo_salto
        logging.info(f"Tipo de salto configurado: {tipo_salto.value}")
        
        # Instrucciones específicas para cada tipo de salto
        if tipo_salto == TipoSalto.CMJ:
            self.mensajes_feedback.append("SALTO CMJ: Inicie de pie, flexión rápida y salto")
        elif tipo_salto == TipoSalto.SQJ:
            self.mensajes_feedback.append("SALTO SQJ: Mantenga posición flexionada 3s antes de saltar")
        elif tipo_salto == TipoSalto.ABALAKOV:
            self.mensajes_feedback.append("SALTO ABALAKOV: Use brazos para impulsarse activamente")

    def calibrar(self, lm):
        """
        Calibra el sistema usando los landmarks de pose detectados.
        Establece las referencias iniciales para el análisis biomecánico.
        
        Args:
            lm: Landmarks de MediaPipe
            
        Returns:
            bool: True si la calibración fue exitosa
        """
        try:
            required_landmarks = [
                mp.solutions.pose.PoseLandmark.LEFT_HIP,
                mp.solutions.pose.PoseLandmark.RIGHT_HIP,
                mp.solutions.pose.PoseLandmark.LEFT_KNEE,
                mp.solutions.pose.PoseLandmark.RIGHT_KNEE,
                mp.solutions.pose.PoseLandmark.LEFT_ANKLE,
                mp.solutions.pose.PoseLandmark.RIGHT_ANKLE,
                mp.solutions.pose.PoseLandmark.LEFT_SHOULDER,
                mp.solutions.pose.PoseLandmark.RIGHT_SHOULDER
            ]

            # Verificar visibilidad de landmarks críticos
            for landmark in required_landmarks:
                if landmark.value >= len(lm) or not lm[landmark.value].visibility > 0.7:
                    logging.warning(f"Calibración fallida: Landmark {landmark.name} no visible o ausente.")
                    raise CalibrationError(f"Landmark {landmark.name} no detectado o visibilidad baja.")

            # Extraer posiciones 3D de landmarks clave
            lhip_3d = np.array([lm[mp.solutions.pose.PoseLandmark.LEFT_HIP.value].x,
                                lm[mp.solutions.pose.PoseLandmark.LEFT_HIP.value].y,
                                lm[mp.solutions.pose.PoseLandmark.LEFT_HIP.value].z])
            rhip_3d = np.array([lm[mp.solutions.pose.PoseLandmark.RIGHT_HIP.value].x,
                                lm[mp.solutions.pose.PoseLandmark.RIGHT_HIP.value].y,
                                lm[mp.solutions.pose.PoseLandmark.RIGHT_HIP.value].z])
            lknee_3d = np.array([lm[mp.solutions.pose.PoseLandmark.LEFT_KNEE.value].x,
                                 lm[mp.solutions.pose.PoseLandmark.LEFT_KNEE.value].y,
                                 lm[mp.solutions.pose.PoseLandmark.LEFT_KNEE.value].z])
            rknee_3d = np.array([lm[mp.solutions.pose.PoseLandmark.RIGHT_KNEE.value].x,
                                 lm[mp.solutions.pose.PoseLandmark.RIGHT_KNEE.value].y,
                                 lm[mp.solutions.pose.PoseLandmark.RIGHT_KNEE.value].z])

            # Calcular referencias iniciales
            mid_hip_initial_y_px = (lhip_3d[1] + rhip_3d[1]) / 2
            dist_rodillas_px = np.hypot(lknee_3d[0] - rknee_3d[0], lknee_3d[1] - rknee_3d[1])
            
            # Calcular factor de conversión píxeles a metros
            if dist_rodillas_px > 0:
                self.px_to_m = self.usuario.longitudes["distancia_rodillas"] / dist_rodillas_px
            else:
                logging.error("Distancia entre rodillas cero durante calibración.")
                raise CalibrationError("Distancia entre rodillas cero. Posición incorrecta.")

            self.initial_hip_y = mid_hip_initial_y_px
            self.initial_knee_x_diff = abs(lknee_3d[0] - rknee_3d[0])

            # Verificar valores de calibración
            if self.px_to_m < 0.001 or self.initial_hip_y <= 0:
                logging.error("Valores de calibración inválidos. Reiniciando calibración.")
                self.calibrado = False
                return False

            self.calibrado = True
            logging.info(f"Calibrado exitoso: factor_px_m={self.px_to_m:.5f}, initial_hip_y={self.initial_hip_y:.5f}")
            return True
            
        except CalibrationError as e:
            logging.error(f"Error específico en calibración: {e}")
            self.calibrado = False
            return False
        except Exception as e:
            logging.error(f"Error inesperado en calibración: {e}")
            self.calibrado = False
            return False

    def verificar_calibracion(self):
        """Verifica si la calibración es válida"""
        return self.px_to_m > 0.001 and self.initial_hip_y > 0

    def iniciar(self):
        """Inicializa una nueva sesión de análisis de saltos"""
        self.t0 = datetime.now()
        self.frame_count = 0
        self.buenos_frames = 0
        self.historial_angulos_rodilla = []
        self.historial_angulos_cadera = []
        self.historial_pos_y_cadera = []
        self.historial_tiempos = []
        
        # Mensajes de seguridad y bienvenida
        self.mensajes_feedback = [
            "ERGO SANITAS SpA - Sistema de Análisis Biomecánico",
            "ATENCIÓN: Realice saltos solo si está en condiciones físicas",
            "Detenga el ejercicio si siente molestias o dolor"
        ]
        
        self.contador = 0
        self.correctas = 0
        self.estado = EstadoSalto.INICIAL
        self.max_hip_y_cm = 0
        self.min_hip_y_flight = float('inf')
        self.takeoff_time = 0
        self.landing_time = 0
        self.jump_height_m = 0
        
        # Limpiar deques al iniciar
        self.smoothed_knee_angles.clear()
        self.smoothed_hip_angles.clear()
        self.smoothed_ankle_angles.clear()
        self.smoothed_trunk_angles.clear()

        # Reiniciar contadores de errores
        self.errores = {k: 0 for k in self.errores}

        logging.info("Análisis de saltos iniciado.")

    def verificar(self, lm):
        """
        Función principal de verificación que analiza cada frame del video.
        Implementa la máquina de estados para detectar las fases del salto.
        
        Args:
            lm: Landmarks de MediaPipe
            
        Returns:
            tuple: (ángulo_rodilla, postura_correcta, detalles_análisis)
        """
        if not self.calibrado:
            logging.warning("Verificación llamada sin calibrar.")
            return 0, False, {"error": "Sin calibrar", "feedback": "Sin calibrar"}

        self.mensajes_feedback = []
        self.frame_count += 1
        current_time = time.time()
        delta_time = current_time - self.ultimo_tiempo
        self.ultimo_tiempo = current_time

        try:
            # Filtrar landmarks visibles
            visible_lm = {}
            for i, p in enumerate(lm):
                if p.visibility > 0.5:
                    visible_lm[i] = np.array([p.x, p.y, p.z])

            def pt(p_enum):
                """Helper para obtener puntos con validación de visibilidad"""
                idx = p_enum.value
                if idx in visible_lm:
                    return visible_lm[idx]
                logging.warning(f"Landmark {p_enum.name} no visible. Visibilidad: {lm[idx].visibility:.2f}")
                raise PoseDetectionError(f"Punto {p_enum.name} no detectado o visibilidad baja.")

            # Extraer puntos clave
            lhip = pt(mp.solutions.pose.PoseLandmark.LEFT_HIP)
            lknee = pt(mp.solutions.pose.PoseLandmark.LEFT_KNEE)
            lankle = pt(mp.solutions.pose.PoseLandmark.LEFT_ANKLE)
            rhip = pt(mp.solutions.pose.PoseLandmark.RIGHT_HIP)
            rknee = pt(mp.solutions.pose.PoseLandmark.RIGHT_KNEE)
            rankle = pt(mp.solutions.pose.PoseLandmark.RIGHT_ANKLE)
            lshoulder = pt(mp.solutions.pose.PoseLandmark.LEFT_SHOULDER)
            rshoulder = pt(mp.solutions.pose.PoseLandmark.RIGHT_SHOULDER)
            lheel = pt(mp.solutions.pose.PoseLandmark.LEFT_HEEL)
            rheel = pt(mp.solutions.pose.PoseLandmark.RIGHT_HEEL)

            # Calcular posiciones y ángulos
            mid_hip_y_px = (lhip[1] + rhip[1]) / 2

            # Cálculo de ángulos articulares
            ang_rodilla_l = self._angle_3d(lhip, lknee, lankle)
            ang_rodilla_r = self._angle_3d(rhip, rknee, rankle)
            prom_rodilla_raw = (ang_rodilla_l + ang_rodilla_r) / 2

            ang_cadera_l = self._angle_3d(lshoulder, lhip, lknee)
            ang_cadera_r = self._angle_3d(rshoulder, rhip, rknee)
            prom_cadera_raw = (ang_cadera_l + ang_cadera_r) / 2

            ang_tobillo_l = self._angle_3d(lknee, lankle, lheel)
            ang_tobillo_r = self._angle_3d(rknee, rankle, rheel)
            prom_tobillo_raw = (ang_tobillo_l + ang_tobillo_r) / 2

            ang_tronco_l = self._angle_3d(lshoulder, lhip, lknee)
            ang_tronco_r = self._angle_3d(rshoulder, rhip, rknee)
            prom_tronco_raw = (ang_tronco_l + ang_tronco_r) / 2

            # Aplicar suavizado usando deques
            self.smoothed_knee_angles.append(prom_rodilla_raw)
            self.smoothed_hip_angles.append(prom_cadera_raw)
            self.smoothed_ankle_angles.append(prom_tobillo_raw)
            self.smoothed_trunk_angles.append(prom_tronco_raw)

            prom_rodilla = np.mean(self.smoothed_knee_angles)
            prom_cadera = np.mean(self.smoothed_hip_angles)
            prom_tobillo = np.mean(self.smoothed_ankle_angles)
            prom_tronco = np.mean(self.smoothed_trunk_angles)

            # Detección de vuelo (basado en posición de talones)
            avg_heel_y = np.mean([lheel[1], rheel[1]])
            is_in_air = (avg_heel_y < (self.initial_hip_y - (self.usuario.altura_m * 0.15 * self.px_to_m)))

            # Detección de valgo de rodilla
            current_knee_x_diff = abs(lknee[0] - rknee[0])
            err_rodillas_valgo = (current_knee_x_diff * self.px_to_m) < (self.initial_knee_x_diff * self.px_to_m - self.umbrales["rodillas_valgo_tolerancia_x"])

            # Calcular velocidades angulares
            velocidad_rodilla = 0
            if self.historial_angulos_rodilla and delta_time > 0:
                velocidad_rodilla = abs(prom_rodilla - self.historial_angulos_rodilla[-1]) / delta_time
                
            velocidad_cadera = 0
            if self.historial_angulos_cadera and delta_time > 0:
                velocidad_cadera = abs(prom_cadera - self.historial_angulos_cadera[-1]) / delta_time

            # Actualizar historial
            self.historial_angulos_rodilla.append(prom_rodilla)
            self.historial_angulos_cadera.append(prom_cadera)
            self.historial_pos_y_cadera.append(mid_hip_y_px)
            self.historial_tiempos.append(current_time)

            # Ejecutar máquina de estados
            postura_correcta_frame, error_keys = self._procesar_estado_salto(
                mid_hip_y_px, prom_rodilla, prom_cadera, prom_tobillo, prom_tronco,
                velocidad_rodilla, velocidad_cadera, is_in_air, err_rodillas_valgo, current_time
            )

            # Actualizar sistema de potencia
            self._actualizar_potencia(postura_correcta_frame, prom_rodilla, velocidad_rodilla)

            return prom_rodilla, postura_correcta_frame, {
                "angulo_rodilla": prom_rodilla,
                "angulo_cadera": prom_cadera,
                "angulo_tobillo": prom_tobillo,
                "angulo_tronco": prom_tronco,
                "velocidad_rodilla": velocidad_rodilla,
                "velocidad_cadera": velocidad_cadera,
                "rodilla_x_diff": current_knee_x_diff,
                "mid_hip_y_px": mid_hip_y_px,
                "is_in_air": is_in_air,
                "jump_height_m": self.jump_height_m,
                "estado_salto_str": self.estado.value,
                "tipo_salto": self.tipo_salto.value,
                "errores_detectados": error_keys
            }

        except PoseDetectionError as e:
            logging.warning(f"Error de detección en verificar: {e}")
            return 0, False, {"error": str(e), "feedback": str(e), "estado_salto_str": self.estado.value}
        except Exception as e:
            logging.error(f"Error inesperado en verificar: {e}")
            return 0, False, {"error": f"Error: {e}", "feedback": f"Error: {e}", "estado_salto_str": self.estado.value}

    def _procesar_estado_salto(self, mid_hip_y_px, prom_rodilla, prom_cadera, prom_tobillo, 
                              prom_tronco, velocidad_rodilla, velocidad_cadera, is_in_air, 
                              err_rodillas_valgo, current_time):
        """
        Procesa la máquina de estados del salto y detecta errores biomecánicos.
        
        Returns:
            tuple: (postura_correcta, lista_errores)
        """
        postura_correcta_frame = True
        error_keys = []

        if self.estado == EstadoSalto.INICIAL:
            # Detectar inicio del contramovimiento
            if mid_hip_y_px > (self.initial_hip_y + (0.02 * self.px_to_m)) and \
               prom_rodilla < (self.umbrales["rodilla_extension_takeoff"] - self.usuario.umbrales_nivel['tolerancia_angulo']):
                self.estado = EstadoSalto.CONTRAMOVIMIENTO
                self.max_hip_y_cm = mid_hip_y_px
                logging.info("Estado: CONTRAMOVIMIENTO")
                self.mensajes_feedback.append("¡Iniciando contramovimiento!")

        elif self.estado == EstadoSalto.CONTRAMOVIMIENTO:
            if mid_hip_y_px > self.max_hip_y_cm:
                self.max_hip_y_cm = mid_hip_y_px

            # Verificar profundidad mínima de contramovimiento
            if prom_rodilla > (self.umbrales["rodilla_flexion_objetivo_cm"] + self.usuario.umbrales_nivel['tolerancia_angulo']):
                self.errores["insufficient_cm_depth"] += 1
                error_keys.append("insufficient_cm_depth")
                self.mensajes_feedback.append("¡Profundidad insuficiente! Flexione más rodillas")
                postura_correcta_frame = False

            if velocidad_rodilla < self.usuario.umbrales_nivel['velocidad_cm_min']:
                self.mensajes_feedback.append("¡Acelere el contramovimiento!")

            # Detectar transición a despegue
            if mid_hip_y_px < (self.max_hip_y_cm - (0.01 * self.px_to_m)) and \
               prom_rodilla > (self.umbrales["rodilla_flexion_objetivo_cm"] + self.usuario.umbrales_nivel['tolerancia_angulo']):
                self.estado = EstadoSalto.DESPEGUE
                logging.info("Estado: DESPEGUE")
                self.mensajes_feedback.append("¡Despegando!")
                self.takeoff_time = current_time
                self.min_hip_y_flight = mid_hip_y_px

        elif self.estado == EstadoSalto.DESPEGUE:
            if mid_hip_y_px < self.min_hip_y_flight:
                self.min_hip_y_flight = mid_hip_y_px

            # Verificar errores en despegue
            if err_rodillas_valgo and velocidad_rodilla > 0.5:
                self.errores["rodillas_valgo_takeoff"] += 0.5
                error_keys.append("rodillas_valgo_takeoff")
                self.mensajes_feedback.append("¡Atención a posición de rodillas!")
                
            if prom_tobillo < self.umbrales["tobillo_plantarflexion_takeoff"] - self.usuario.umbrales_nivel['tolerancia_angulo']:
                self.errores["insufficient_plantarflexion"] += 1
                error_keys.append("insufficient_plantarflexion")
                self.mensajes_feedback.append("¡Falta empuje de tobillos!")
                postura_correcta_frame = False
                
            if velocidad_rodilla < self.usuario.umbrales_nivel['velocidad_takeoff_min']:
                self.mensajes_feedback.append("¡Fuerce más el despegue!")

            if is_in_air:
                self.estado = EstadoSalto.VUELO
                logging.info("Estado: VUELO")
                self.mensajes_feedback.append("¡En el aire!")
                self.peak_flight_time = current_time

        elif self.estado == EstadoSalto.VUELO:
            if not is_in_air:
                self.estado = EstadoSalto.ATERRIZAJE
                logging.info("Estado: ATERRIZAJE")
                self.mensajes_feedback.append("¡Aterrizando!")
                self.landing_time = current_time
                jump_peak_y_px = self.min_hip_y_flight
                cm_lowest_y_px = self.max_hip_y_cm
                self.jump_height_m = ((cm_lowest_y_px - jump_peak_y_px) * self.px_to_m)
                
                # Calcular tiempo de vuelo
                flight_duration = self.landing_time - self.takeoff_time
                self.tiempos_vuelo.append(flight_duration)
                
                # Calcular potencia del salto
                potencia = self.calcular_potencia(self.jump_height_m)
                self.potencias.append(potencia)
                
                # Guardar altura para estadísticas
                self.alturas_saltos.append(self.jump_height_m)

                if flight_duration < self.umbrales["min_flight_time"] or self.jump_height_m < self.umbrales["min_vertical_displacement_m"]:
                    self.mensajes_feedback.append("Salto no válido (tiempo de vuelo/altura insuficiente).")
                    self.estado = EstadoSalto.INICIAL
                    postura_correcta_frame = False

        elif self.estado == EstadoSalto.ATERRIZAJE:
            if prom_rodilla > self.umbrales["rodilla_flexion_landing_max"] + self.usuario.umbrales_nivel['tolerancia_angulo'] or \
               prom_cadera > self.umbrales["cadera_flexion_landing_max"] + self.usuario.umbrales_nivel['tolerancia_angulo']:
                self.errores["stiff_landing"] += 1
                error_keys.append("stiff_landing")
                self.mensajes_feedback.append("¡Aterrizaje rígido! Flexiona más rodillas al caer")
                postura_correcta_frame = False

            if prom_tronco < self.umbrales["columna_alineacion_general"] - self.usuario.umbrales_nivel['tolerancia_angulo'] or \
               prom_tronco > self.umbrales["columna_alineacion_general"] + self.usuario.umbrales_nivel['tolerancia_angulo']:
               self.errores["trunk_lean_takeoff_landing"] += 1
               error_keys.append("trunk_lean_takeoff_landing")
               self.mensajes_feedback.append("¡Alinea el tronco en el aterrizaje!")
               postura_correcta_frame = False

            if err_rodillas_valgo:
                self.errores["rodillas_valgo_takeoff"] += 1
                error_keys.append("rodillas_valgo_takeoff")
                self.mensajes_feedback.append("¡Rodillas hacia afuera en aterrizaje!")
                postura_correcta_frame = False

            if current_time - self.landing_time > self.umbrales["max_landing_time"] or \
               (prom_rodilla > self.umbrales["rodilla_extension_landing_min"] - self.usuario.umbrales_nivel['tolerancia_angulo'] and
                prom_cadera > self.umbrales["cadera_extension_takeoff"] - self.usuario.umbrales_nivel['tolerancia_angulo']):
                self.estado = EstadoSalto.ESTABLE_POST_ATERRIZAJE
                logging.info("Estado: ESTABLE_POST_ATERRIZAJE")
                
                if postura_correcta_frame:
                    self.correctas += 1
                    self.mensajes_feedback.append(f"¡BUEN SALTO! Altura: {self.jump_height_m*100:.1f}cm")
                else:
                    self.mensajes_feedback.append("¡Salto con errores!")
                
                self.contador += 1
                self.mensajes_feedback.append("Descanse 15 segundos antes del próximo salto")

        elif self.estado == EstadoSalto.ESTABLE_POST_ATERRIZAJE:
            if abs(mid_hip_y_px - self.initial_hip_y) < (0.05 * self.px_to_m):
                self.estado = EstadoSalto.INICIAL
                logging.info("Estado: INICIAL (listo para el próximo salto)")

        return postura_correcta_frame, error_keys

    def _actualizar_potencia(self, postura_ok, angulo_rodilla, velocidad):
        """Sistema de potencia para saltos."""
        factor_tecnica = 0.7 if postura_ok else 0.4
        
        factor_velocidad = 0
        vel_takeoff_min = self.usuario.umbrales_nivel['velocidad_takeoff_min']
        if velocidad > vel_takeoff_min * 1.5:
            factor_velocidad = 0.3
        elif velocidad > vel_takeoff_min:
            factor_velocidad = 0.15

        factor_altura = 0
        if self.estado == EstadoSalto.VUELO and self.jump_height_m > 0:
            target_height = self.usuario.altura_m * 0.25
            factor_altura = min(1, self.jump_height_m / target_height) * 0.2

        incremento = (factor_tecnica + factor_velocidad + factor_altura) * 5
        self.potencia_target = min(100, self.potencia_target + incremento)

        if not postura_ok:
            self.potencia_target = max(0, self.potencia_target - 5)

        self.potencia += (self.potencia_target - self.potencia) * 0.2

    def calcular_potencia(self, altura_salto):
        """
        Calcula la potencia mecánica en watts
        
        Args:
            altura_salto (float): Altura del salto en metros
            
        Returns:
            float: Potencia en watts
        """
        # Fórmula: P = (m * g * h) / t
        # Donde:
        #   m = masa corporal (kg)
        #   g = aceleración gravitacional (9.81 m/s²)
        #   h = altura del salto (m)
        #   t = tiempo de impulso (s)
        
        # Estimación simplificada: t = sqrt(2*h/g)
        tiempo_impulso = math.sqrt(2 * altura_salto / 9.81) if altura_salto > 0 else 0.1
        potencia = (self.usuario.peso_kg * 9.81 * altura_salto) / tiempo_impulso
        return potencia

    def calcular_indice_elasticidad(self, altura_cmj, altura_sqj):
        """Calcula el índice de elasticidad"""
        if altura_sqj == 0:
            return 0.0
        return ((altura_cmj - altura_sqj) / altura_sqj) * 100

    def calcular_indice_coordinacion(self, altura_abalakov, altura_cmj):
        """Calcula el índice de coordinación brazo-tronco"""
        if altura_cmj == 0:
            return 0.0
        return ((altura_abalakov - altura_cmj) / altura_cmj) * 100

    def calcular_puntuacion(self):
        """
        Calcula la puntuación técnica basada en errores y rendimiento
        
        Returns:
            float: Puntuación de 0 a 100
        """
        if self.contador == 0:
            return 0

        total_error_impact = 0
        for error_key, count in self.errores.items():
            total_error_impact += (count * self.gravedad_errores.get(error_key, 1))
        
        max_possible_error_impact = sum(self.gravedad_errores.values()) * self.contador * 10
        
        if max_possible_error_impact > 0:
            normalized_error_score = total_error_impact / max_possible_error_impact
            score = 100 * (1 - normalized_error_score)
        else:
            score = 100

        return max(0, min(100, score))

    def clasificar_nivel(self, altura_promedio):
        """
        Clasifica al deportista según su rendimiento
        
        Args:
            altura_promedio (float): Altura promedio de saltos en metros
            
        Returns:
            str: Nivel clasificado
        """
        if altura_promedio == 0:
            return "Sin datos suficientes"
        
        altura_cm = altura_promedio * 100
        genero = "hombres" if self.usuario.sexo == "M" else "mujeres"
        tipo = self.tipo_salto.name
        
        rangos = RANGOS_CLASIFICACION[genero][tipo]
        
        if altura_cm < rangos['bajo'][1]:
            return "Bajo"
        elif altura_cm < rangos['medio'][1]:
            return "Medio"
        elif altura_cm < rangos['avanzado'][1]:
            return "Avanzado"
        else:
            return "Alto rendimiento"

    def generar_recomendaciones(self):
        """Genera recomendaciones basadas en el análisis"""
        recs = []
        
        if self.errores["rodillas_valgo_takeoff"] > 0:
            recs.append("Fortalezca glúteos medios para control de rodillas")
            recs.append("Practique sentadillas con banda elástica alrededor de rodillas")
            
        if self.errores["stiff_landing"] > 0:
            recs.append("Practique aterrizajes con mayor flexión de rodillas")
            recs.append("Entrene saltos a cajón con recepción suave")
            
        if self.errores["insufficient_cm_depth"] > 0:
            recs.append("Mejore la profundidad del contramovimiento")
            recs.append("Trabaje movilidad de cadera y tobillos")
            
        if self.alturas_saltos and max(self.alturas_saltos) < 0.25:
            recs.append("Trabaje ejercicios pliométricos para mejorar potencia")
            recs.append("Incorpore saltos con contramovimiento profundo")
            
        if self.errores["trunk_lean_takeoff_landing"] > 0:
            recs.append("Fortalezca core para mantener tronco erguido")
            recs.append("Practique planchas y ejercicios de estabilidad")
            
        if not recs:
            recs.append("¡Buen trabajo! Continúe con su rutina actual")
            
        return recs

    def finalizar(self):
        """
        Finaliza la sesión de análisis y genera el reporte completo
        
        Returns:
            dict: Diccionario con todos los resultados de la sesión
        """
        dt = datetime.now() - self.t0
        precision = (self.correctas / max(self.contador, 1)) * 100 if self.contador > 0 else 0

        puntuacion = self.calcular_puntuacion()
        
        # Calcular métricas agregadas
        altura_promedio = np.mean(self.alturas_saltos) if self.alturas_saltos else 0
        potencia_promedio = np.mean(self.potencias) if self.potencias else 0
        tiempo_vuelo_promedio = np.mean(self.tiempos_vuelo) if self.tiempos_vuelo else 0
        
        # Clasificación por nivel
        clasificacion = self.clasificar_nivel(altura_promedio)
        
        # Evaluación cualitativa
        if altura_promedio > 0.4:
            evaluacion = "EXCELENTE"
        elif altura_promedio > 0.3:
            evaluacion = "BUENO"
        elif altura_promedio > 0.2:
            evaluacion = "PROMEDIO"
        else:
            evaluacion = "POR DEBAJO DEL PROMEDIO"
            
        # Generar recomendaciones
        recomendaciones = self.generar_recomendaciones()
        
        # Clasificación final del usuario
        nivel_usuario_final = self.usuario.clasificar_nivel_usuario({
            'altura_salto_promedio': altura_promedio,
            'precision': precision,
            'puntuacion_tecnica': puntuacion
        })
        
        logging.info(f"Análisis finalizado. Total: {self.contador}, Correctas: {self.correctas}, Precision: {precision:.1f}%")

        return {
            "usuario": {
                "nombre": self.usuario.nombre,
                "sexo": self.usuario.sexo,
                "edad": self.usuario.edad,
                "peso_kg": self.usuario.peso_kg,
                "altura_m": self.usuario.altura_m,
                "imc": self.usuario.imc,
                "nivel_inicial": self.usuario.nivel_actividad
            },
            "sesion": {
                "duracion": str(dt),
                "total": self.contador,
                "correctas": self.correctas,
                "precision": precision,
                "tipo_salto": self.tipo_salto.value
            },
            "metricas": {
                "altura_salto_promedio": altura_promedio,
                "altura_salto_maxima": max(self.alturas_saltos) if self.alturas_saltos else 0,
                "potencia_promedio": potencia_promedio,
                "tiempo_vuelo_promedio": tiempo_vuelo_promedio,
                "indice_elasticidad": self.indice_elasticidad,
                "indice_coordinacion": self.indice_coordinacion
            },
            "evaluacion": {
                "clasificacion_rendimiento": clasificacion,
                "nivel_usuario_final": nivel_usuario_final,
                "puntuacion_tecnica": puntuacion,
                "evaluacion_cualitativa": evaluacion
            },
            "errores": self.errores,
            "recomendaciones": recomendaciones,
            "fecha_analisis": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    @staticmethod
    def _angle_3d(a, b, c):
        """
        Calcula el ángulo entre tres puntos en 3D.
        
        Args:
            a, b, c: Puntos 3D como arrays de numpy
            
        Returns:
            float: Ángulo en grados
        """
        ba = a - b
        bc = c - b
        dot_product = np.dot(ba, bc)
        norm_ba = np.linalg.norm(ba)
        norm_bc = np.linalg.norm(bc)
        
        denominator = norm_ba * norm_bc
        if denominator < 1e-6:
            return 180.0
            
        cos_angle = dot_product / denominator
        return np.degrees(np.arccos(np.clip(cos_angle, -1, 1)))
