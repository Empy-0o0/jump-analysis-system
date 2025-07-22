import cv2
import mediapipe as mp
import numpy as np
import json
import time
from datetime import datetime
import logging
import yaml
from collections import deque
from enum import Enum
import os
import math

# --- Configuración de Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', filename='ergosanitas_saltos_mejorado.log')

# --- Clases de Excepciones Personalizadas ---
class PoseDetectionError(Exception):
    """Excepción para errores en la detección de pose."""
    pass

class CalibrationError(Exception):
    """Excepción para errores durante la calibración."""
    pass

# --- Configuración externa (Cargar desde config_Saltos.yaml) ---
try:
    with open('config_Saltos.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    PROPORCIONES = config.get('proporciones', {})
    ROM_OPTIMO_SALTO = config.get('rom_optimo_salto', {})
    PARAMETROS_SALTO = config.get('parametros_salto', {})
    NIVEL_USUARIO = config.get('nivel_usuario', {})
except FileNotFoundError:
    logging.error("config_Saltos.yaml no encontrado. Usando parámetros por defecto.")
    # Parámetros por defecto para saltos (tomados de Saltos.py)
    PROPORCIONES = {
        'm': {'altura_femur': 0.23, 'altura_tibia': 0.22, 'distancia_rodillas': 0.18},
        'f': {'altura_femur': 0.22, 'altura_tibia': 0.21, 'distancia_rodillas': 0.17}
    }
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

# --- Enum para Estados de Salto (tomado de Saltos3.0.py) ---
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

# --- Clase PerfilUsuario (combinación de Usuario y PerfilUsuario) ---
class UsuarioPerfil:
    def __init__(self, nombre="", sexo="", edad=0, altura_cm=0, peso_kg=0, nivel_actividad=""):
        self.nombre = nombre
        self.sexo = sexo.upper()
        self.edad = edad
        self.altura_cm = altura_cm
        self.peso_kg = peso_kg
        self.nivel_actividad = nivel_actividad if nivel_actividad in NIVEL_USUARIO else 'principiante'
        self.fecha_creacion = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.altura_m = self.altura_cm / 100.0
        self.imc = self.peso_kg / (self.altura_m ** 2) if self.altura_m > 0 else 0

        # Inicializar longitudes como diccionario vacío
        self.longitudes = {}
        # Solo calcular si tenemos datos válidos
        if self.sexo in ['M', 'F'] and self.altura_cm > 0:
            self.calcular_longitudes()
        else:
            self.longitudes = {
                "femur": 0,
                "tibia": 0,
                "distancia_rodillas": 0
            }

    def calcular_longitudes(self):
        """Calcula las longitudes de los segmentos corporales"""
        # Factor de corrección por edad (de Saltos.py)
        factor_correccion = 0.97 if self.edad > 50 else 1.0

        self.longitudes = {
            "femur": self.altura_m * PROPORCIONES[self.sexo.lower()]['altura_femur'] * factor_correccion,
            "tibia": self.altura_m * PROPORCIONES[self.sexo.lower()]['altura_tibia'] * factor_correccion,
            "distancia_rodillas": self.altura_m * PROPORCIONES[self.sexo.lower()]['distancia_rodillas'] * factor_correccion
        }
        self.umbrales_nivel = NIVEL_USUARIO[self.nivel_actividad]

    def obtener_datos_usuario(self):
        """Solicita y valida los datos del usuario (de Saltos3.0.py)"""
        print("\n" + "="*50)
        print("   CONFIGURACIÓN DE PERFIL DE USUARIO")
        print("="*50)

        while not self.nombre:
            self.nombre = input("Nombre completo: ").strip()
            if not self.nombre:
                print("❌ El nombre es obligatorio")

        while self.sexo not in ['M', 'F']:
            sexo_input = input("Sexo (M/F): ").strip().upper()
            if sexo_input in ['M', 'F']:
                self.sexo = sexo_input
            else:
                print("❌ Ingrese M para Masculino o F para Femenino")

        while self.edad <= 0:
            try:
                edad_input = int(input("Edad: "))
                if edad_input > 0:
                    self.edad = edad_input
                else:
                    print("❌ La edad debe ser un número positivo")
            except ValueError:
                print("❌ Entrada inválida. Por favor, ingrese un número.")

        while self.altura_cm <= 0:
            try:
                altura_input = float(input("Altura en cm (ej. 175): "))
                if altura_input > 0:
                    self.altura_cm = altura_input
                else:
                    print("❌ La altura debe ser un número positivo")
            except ValueError:
                print("❌ Entrada inválida. Por favor, ingrese un número.")

        while self.peso_kg <= 0:
            try:
                peso_input = float(input("Peso en kg (ej. 70.5): "))
                if peso_input > 0:
                    self.peso_kg = peso_input
                else:
                    print("❌ El peso debe ser un número positivo")
            except ValueError:
                print("❌ Entrada inválida. Por favor, ingrese un número.")

        niveles_disponibles = list(NIVEL_USUARIO.keys())
        while self.nivel_actividad not in niveles_disponibles:
            nivel_input = input(f"Nivel de actividad ({'/'.join(niveles_disponibles)}): ").strip().lower()
            if nivel_input in niveles_disponibles:
                self.nivel_actividad = nivel_input
            else:
                print(f"❌ Nivel inválido. Por favor, elija entre: {', '.join(niveles_disponibles)}")

        self.altura_m = self.altura_cm / 100.0
        self.imc = self.peso_kg / (self.altura_m ** 2) if self.altura_m > 0 else 0

        # Recalcular longitudes con los nuevos datos
        self.calcular_longitudes()

        print("✅ Perfil de usuario configurado correctamente.")
        self.guardar_perfil()

    def guardar_perfil(self, filename="perfil_usuario.json"):
        """Guarda el perfil del usuario en un archivo JSON (de Saltos3.0.py)"""
        data = self.__dict__.copy()
        # Eliminar atributos que no se desean guardar directamente o que se recalculan
        data.pop('altura_m', None)
        data.pop('imc', None)
        data.pop('longitudes', None)
        data.pop('umbrales_nivel', None)
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            logging.info(f"Perfil de usuario guardado en {filename}")
        except Exception as e:
            logging.error(f"Error al guardar el perfil: {e}")

    @classmethod
    def cargar_perfil(cls, filename="perfil_usuario.json"):
        """Carga un perfil de usuario desde un archivo JSON (de Saltos3.0.py)"""
        if os.path.exists(filename):
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                perfil = cls(
                    nombre=data.get('nombre', ""),
                    sexo=data.get('sexo', ""),
                    edad=data.get('edad', 0),
                    altura_cm=data.get('altura_cm', 0),
                    peso_kg=data.get('peso_kg', 0),
                    nivel_actividad=data.get('nivel_actividad', "")
                )
                perfil.fecha_creacion = data.get('fecha_creacion', perfil.fecha_creacion)
                # Calcular longitudes con los nuevos datos
                perfil.calcular_longitudes()
                logging.info(f"Perfil de usuario cargado desde {filename}")
                return perfil
            except Exception as e:
                logging.error(f"Error al cargar el perfil: {e}")
                return None
        return None

# --- Clase AnalizadorSaltos (Mejora de VerificadorSaltos de Saltos.py) ---
class AnalizadorSaltos:
    def __init__(self, usuario: UsuarioPerfil):
        self.usuario = usuario
        self.contador = 0
        self.correctas = 0
        self.estado = EstadoSalto.INICIAL # Usar Enum
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
        self.gravedad_errores = { # De Saltos.py
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

        self.initial_hip_y = 0
        self.initial_knee_x_diff = 0
        self.max_hip_y_cm = 0
        self.min_hip_y_flight = float('inf')
        self.takeoff_time = 0
        self.landing_time = 0
        self.peak_flight_time = 0
        self.jump_height_m = 0
        self.tipo_salto = TipoSalto.CMJ  # Valor por defecto

        self.historial_angulos_rodilla = [] # Para velocidad
        self.historial_angulos_cadera = [] # Para velocidad
        self.historial_pos_y_cadera = []
        self.historial_tiempos = []
        self.mensajes_feedback = []

        # Nuevas métricas
        self.alturas_saltos = []
        self.tiempos_vuelo = []
        self.potencias = []
        self.indice_elasticidad = 0.0
        self.indice_coordinacion = 0.0

        # Deque para suavizado de ángulos (inspirado en Saltos3.0.py)
        self.smoothed_knee_angles = deque(maxlen=5)
        self.smoothed_hip_angles = deque(maxlen=5)
        self.smoothed_ankle_angles = deque(maxlen=5)
        self.smoothed_trunk_angles = deque(maxlen=5)

        self.umbrales = { # De Saltos.py
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
        self.px_to_m = 0

    def set_tipo_salto(self, tipo_salto: TipoSalto):
        """Establece el tipo de salto a analizar"""
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

            for landmark in required_landmarks:
                if landmark.value >= len(lm) or not lm[landmark.value].visibility > 0.7:
                    logging.warning(f"Calibración fallida: Landmark {landmark.name} no visible o ausente.")
                    raise CalibrationError(f"Landmark {landmark.name} no detectado o visibilidad baja.")

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

            mid_hip_initial_y_px = (lhip_3d[1] + rhip_3d[1]) / 2
            dist_rodillas_px = np.hypot(lknee_3d[0] - rknee_3d[0], lknee_3d[1] - rknee_3d[1])
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
        self.t0 = datetime.now()
        self.frame_count = 0
        self.buenos_frames = 0
        self.historial_angulos_rodilla = []
        self.historial_angulos_cadera = []
        self.historial_pos_y_cadera = []
        self.historial_tiempos = []
        self.mensajes_feedback = [
            "ATENCION: Realice saltos solo si está en condiciones físicas",
            "Detenga el ejercicio si siente molestias o dolor"
        ]
        self.contador = 0
        self.correctas = 0
        self.estado = EstadoSalto.INICIAL # Reiniciar estado con Enum
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

    def finalizar(self):
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
        
        logging.info(f"Análisis finalizado. Total: {self.contador}, Correctas: {self.correctas}, Precision: {precision:.1f}%")

        return {
            "duracion": str(dt),
            "total": self.contador,
            "correctas": self.correctas,
            "errores": self.errores,
            "precision": precision,
            "altura_salto_promedio": altura_promedio,
            "potencia_promedio": potencia_promedio,
            "tiempo_vuelo_promedio": tiempo_vuelo_promedio,
            "indice_elasticidad": self.indice_elasticidad,
            "indice_coordinacion": self.indice_coordinacion,
            "clasificacion": clasificacion,
            "tipo_salto": self.tipo_salto.value,
            "puntuacion_tecnica": puntuacion,
            "evaluacion_rendimiento": evaluacion,
            "recomendaciones": recomendaciones
        }
        
    def generar_recomendaciones(self):
        """Genera recomendaciones basadas en el análisis"""
        recs = []
        
        if self.errores["rodillas_valgo_takeoff"] > 0 or self.errores["rodillas_valgo_takeoff"] > 0:
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

    def calcular_puntuacion(self):
        if self.contador == 0:
            return 0

        pesos = {
            'contramovimiento_profundidad_y_velocidad': 0.30,
            'despegue_extension_y_potencia': 0.35,
            'aterrizaje_amortiguacion_y_estabilidad': 0.35
        }

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
        """Clasifica al deportista según su rendimiento"""
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

    def calcular_potencia(self, altura_salto):
        """Calcula la potencia mecánica en watts"""
        # Fórmula: P = (m * g * h) / t
        # Donde:
        #   m = masa corporal (kg)
        #   g = aceleración gravitacional (9.81 m/s²)
        #   h = altura del salto (m)
        #   t = tiempo de impulso (s)
        
        # Estimación simplificada: t = sqrt(2*h/g)
        tiempo_impulso = math.sqrt(2 * altura_salto / 9.81)
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

    def verificar(self, lm):
        if not self.calibrado:
            logging.warning("Verificación llamada sin calibrar.")
            return 0, False, {"error": "Sin calibrar", "feedback": "Sin calibrar"}

        self.mensajes_feedback = []
        self.frame_count += 1
        current_time = time.time()
        delta_time = current_time - self.ultimo_tiempo
        self.ultimo_tiempo = current_time

        try:
            visible_lm = {}
            for i, p in enumerate(lm):
                if p.visibility > 0.5: # Usar umbral de visibilidad del 50%
                    visible_lm[i] = np.array([p.x, p.y, p.z])

            def pt(p_enum):
                idx = p_enum.value
                if idx in visible_lm:
                    return visible_lm[idx]
                logging.warning(f"Landmark {p_enum.name} no visible o ausente. Visibilidad: {lm[idx].visibility:.2f}")
                raise PoseDetectionError(f"Punto {p_enum.name} no detectado o visibilidad baja.")

            # Puntos clave
            lhip = pt(mp.solutions.pose.PoseLandmark.LEFT_HIP)
            lknee = pt(mp.solutions.pose.PoseLandmark.LEFT_KNEE)
            lankle = pt(mp.solutions.pose.PoseLandmark.LEFT_ANKLE)
            rhip = pt(mp.solutions.pose.PoseLandmark.RIGHT_HIP)
            rknee = pt(mp.solutions.pose.PoseLandmark.RIGHT_KNEE)
            rankle = pt(mp.solutions.pose.PoseLandmark.RIGHT_ANKLE)
            lshoulder = pt(mp.solutions.pose.PoseLandmark.LEFT_SHOULDER)
            rshoulder = pt(mp.solutions.pose.PoseLandmark.RIGHT_SHOULDER)
            lleel = pt(mp.solutions.pose.PoseLandmark.LEFT_HEEL)
            rheel = pt(mp.solutions.pose.PoseLandmark.RIGHT_HEEL)
            # lfoot_index = pt(mp.solutions.pose.PoseLandmark.LEFT_FOOT_INDEX)
            # rfoot_index = pt(mp.solutions.pose.PoseLandmark.RIGHT_FOOT_INDEX)

            mid_hip_y_px = (lhip[1] + rhip[1]) / 2
            # mid_hip_x = (lhip[0] + rhip[0]) / 2
            # mid_knee_x = (lknee[0] + rknee[0]) / 2
            # mid_shoulder = (lshoulder + rshoulder) / 2

            # Cálculo de ángulos
            ang_rodilla_l = self._angle_3d(lhip, lknee, lankle)
            ang_rodilla_r = self._angle_3d(rhip, rknee, rankle)
            prom_rodilla_raw = (ang_rodilla_l + ang_rodilla_r) / 2

            ang_cadera_l = self._angle_3d(lshoulder, lhip, lknee)
            ang_cadera_r = self._angle_3d(rshoulder, rhip, rknee)
            prom_cadera_raw = (ang_cadera_l + ang_cadera_r) / 2

            ang_tobillo_l = self._angle_3d(lknee, lankle, lleel)
            ang_tobillo_r = self._angle_3d(rknee, rankle, rheel)
            prom_tobillo_raw = (ang_tobillo_l + ang_tobillo_r) / 2

            ang_tronco_l = self._angle_3d(lshoulder, lhip, lknee)
            ang_tronco_r = self._angle_3d(rshoulder, rhip, rknee)
            prom_tronco_raw = (ang_tronco_l + ang_tronco_r) / 2

            # Aplicar suavizado (deque)
            self.smoothed_knee_angles.append(prom_rodilla_raw)
            self.smoothed_hip_angles.append(prom_cadera_raw)
            self.smoothed_ankle_angles.append(prom_tobillo_raw)
            self.smoothed_trunk_angles.append(prom_tronco_raw)

            prom_rodilla = np.mean(self.smoothed_knee_angles)
            prom_cadera = np.mean(self.smoothed_hip_angles)
            prom_tobillo = np.mean(self.smoothed_ankle_angles)
            prom_tronco = np.mean(self.smoothed_trunk_angles)

            # Posición de los pies respecto al suelo (aproximación para detectar vuelo/contacto)
            avg_heel_y = np.mean([lleel[1], rheel[1]])
            
            # Umbral de detección de vuelo más tolerante (cambiamos de 0.2 a 0.15)
            is_in_air = (avg_heel_y < (self.initial_hip_y - (self.usuario.altura_m * 0.15 * self.px_to_m)))

            # Detección de valgo de rodilla (diferencia en X entre rodillas)
            current_knee_x_diff = abs(lknee[0] - rknee[0])
            err_rodillas_valgo = (current_knee_x_diff * self.px_to_m) < (self.initial_knee_x_diff * self.px_to_m - self.umbrales["rodillas_valgo_tolerancia_x"])

            # Velocidades angulares (usando historial)
            velocidad_rodilla = 0
            if self.historial_angulos_rodilla and delta_time > 0:
                velocidad_rodilla = abs(prom_rodilla - self.historial_angulos_rodilla[-1]) / delta_time
                
            velocidad_cadera = 0
            if self.historial_angulos_cadera and delta_time > 0:
                velocidad_cadera = abs(prom_cadera - self.historial_angulos_cadera[-1]) / delta_time

            self.historial_angulos_rodilla.append(prom_rodilla)
            self.historial_angulos_cadera.append(prom_cadera)
            self.historial_pos_y_cadera.append(mid_hip_y_px)
            self.historial_tiempos.append(current_time)

            # Lógica de la máquina de estados
            postura_correcta_frame = True
            error_keys = []

            if self.estado == EstadoSalto.INICIAL:
                # Detectar inicio del contramovimiento (descenso de cadera y flexión de rodilla)
                if mid_hip_y_px > (self.initial_hip_y + (0.02 * self.px_to_m)) and prom_rodilla < (self.umbrales["rodilla_extension_takeoff"] - self.usuario.umbrales_nivel['tolerancia_angulo']):
                    self.estado = EstadoSalto.CONTRAMOVIMIENTO
                    self.max_hip_y_cm = mid_hip_y_px
                    logging.info("Estado: CONTRAMOVIMIENTO")
                    self.mensajes_feedback.append("¡Iniciando contramovimiento!")

            elif self.estado == EstadoSalto.CONTRAMOVIMIENTO:
                if mid_hip_y_px > self.max_hip_y_cm:
                    self.max_hip_y_cm = mid_hip_y_px # Sigue bajando

                # Verificar profundidad mínima de CM y velocidad
                if prom_rodilla > (self.umbrales["rodilla_flexion_objetivo_cm"] + self.usuario.umbrales_nivel['tolerancia_angulo']):
                     self.errores["insufficient_cm_depth"] += 1
                     error_keys.append("insufficient_cm_depth")
                     self.mensajes_feedback.append("¡Profundidad insuficiente! Flexione más rodillas")
                     postura_correcta_frame = False

                if velocidad_rodilla < self.usuario.umbrales_nivel['velocidad_cm_min']:
                    self.mensajes_feedback.append("¡Acelera el contramovimiento!")

                # Detectar inicio del despegue (cadera sube, rodilla extiende)
                if mid_hip_y_px < (self.max_hip_y_cm - (0.01 * self.px_to_m)) and prom_rodilla > (self.umbrales["rodilla_flexion_objetivo_cm"] + self.usuario.umbrales_nivel['tolerancia_angulo']) and prom_rodilla < self.umbrales["rodilla_extension_takeoff"]:
                    self.estado = EstadoSalto.DESPEGUE
                    logging.info("Estado: DESPEGUE")
                    self.mensajes_feedback.append("¡Despegando!")
                    self.takeoff_time = current_time
                    self.min_hip_y_flight = mid_hip_y_px

            elif self.estado == EstadoSalto.DESPEGUE:
                if mid_hip_y_px < self.min_hip_y_flight:
                    self.min_hip_y_flight = mid_hip_y_px

                # Reducir sensibilidad a errores durante movimiento rápido
                if err_rodillas_valgo and velocidad_rodilla > 0.5:
                    self.errores["rodillas_valgo_takeoff"] += 0.5  # Media penalización
                    error_keys.append("rodillas_valgo_takeoff")
                    self.mensajes_feedback.append("¡Atención a posición de rodillas!")
                    
                if prom_tobillo < self.umbrales["tobillo_plantarflexion_takeoff"] - self.usuario.umbrales_nivel['tolerancia_angulo']:
                    self.errores["insufficient_plantarflexion"] += 1
                    error_keys.append("insufficient_plantarflexion")
                    self.mensajes_feedback.append("¡Falta empuje de tobillos!")
                    postura_correcta_frame = False
                    
                if velocidad_rodilla < self.usuario.umbrales_nivel['velocidad_takeoff_min']:
                    self.mensajes_feedback.append("¡Fuerza más el despegue!")

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
                "estado_salto_str": self.estado.value, # Para visualización
                "tipo_salto": self.tipo_salto.value
            }

        except PoseDetectionError as e:
            logging.warning(f"Error de detección en verificar: {e}")
            return 0, False, {"error": str(e), "feedback": str(e), "estado_salto_str": self.estado.value}
        except Exception as e:
            logging.error(f"Error inesperado en verificar: {e}")
            return 0, False, {"error": f"Error: {e}", "feedback": f"Error: {e}", "estado_salto_str": self.estado.value}

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

    @staticmethod
    def _angle_3d(a, b, c):
        """Calcula el ángulo entre tres puntos en 3D."""
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

# --- InterfazVisual (de Saltos.py, con ajustes) ---
class InterfazVisual:
    @staticmethod
    def dibujar_contenedor(img, text, x, y, width, height, bg_color, text_color, font_scale=0.8):
        cv2.rectangle(img, (x, y), (x + width, y + height), bg_color, -1)
        cv2.rectangle(img, (x, y), (x + width, y + height), (255, 255, 255), 2)
        text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 2)[0]
        text_x = x + (width - text_size[0]) // 2
        text_y = y + (height + text_size[1]) // 2
        cv2.putText(img, text, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, font_scale, text_color, 2)

    @staticmethod
    def dibujar_barra_potencia(img, potencia, x, y, width, height):
        cv2.rectangle(img, (x, y), (x + width, y + height), (50, 50, 50), -1)
        cv2.rectangle(img, (x, y), (x + width, y + height), (255, 255, 255), 2)
        fill_height = int((potencia / 100) * height)
        if fill_height > 0:
            for i in range(fill_height):
                pos = y + height - i
                ratio = i / height
                if ratio < 0.33:
                    color = (0, 0, 255) # Rojo
                elif ratio < 0.66:
                    color = (0, 165, 255) # Naranja
                else:
                    color = (0, 255, 0) # Verde
                cv2.line(img, (x + 2, pos), (x + width - 2, pos), color, 2)
        cv2.putText(img, "EXPLOSIVIDAD", (x - 20, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(img, f"{potencia:.0f}%", (x, y + height + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    @staticmethod
    def dibujar_semaforo_tecnico(img, errores, x, y):
        cv2.putText(img, "MONITOR TECNICO", (x, y - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
        errores_monitor = [
            ("insufficient_cm_depth", "CM INSUF."),
            ("prematura_extension", "EXTENSION PREM."),
            ("rodillas_valgo_takeoff", "RODILLAS VALGO"),
            ("insufficient_plantarflexion", "FALTA EMPUJE"),
            ("stiff_landing", "ATERRIZAJE RIGIDO"),
            ("landing_imbalance", "DESEQ. ATERRIZAJE"),
            ("excessive_landing_impact", "IMPACTO EXCESIVO"),
            ("trunk_lean_takeoff_landing", "TRONCO INCLINADO")
        ]
        for i, (error_key, error_text) in enumerate(errores_monitor):
            color = (0, 255, 0) # Verde
            if errores.get(error_key, 0) > 0: # Si el contador de este error es mayor a 0
                color = (0, 0, 255) # Rojo
            cv2.circle(img, (x, y + i*30), 8, color, -1)
            cv2.putText(img, error_text, (x + 20, y + 10 + i*30), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)

    @staticmethod
    def dibujar_grafico_altura(img, historial_pos_y_cadera, initial_hip_y, px_to_m, jump_height_m_actual=0):
        if len(historial_pos_y_cadera) < 2:
            return

        h, w = img.shape[:2]
        graph_height = 120
        graph_width = 250
        start_x = w - graph_width - 20
        start_y = h - graph_height - 20
        overlay = img.copy()
        cv2.rectangle(overlay, (start_x, start_y), (start_x + graph_width, start_y + graph_height), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, img, 0.3, 0, img)
        cv2.rectangle(img, (start_x, start_y), (start_x + graph_width, start_y + graph_height), (255, 255, 255), 1)

        data_to_plot = np.array(historial_pos_y_cadera)
        min_y_data = np.min(data_to_plot)
        max_y_data = np.max(data_to_plot)
        
        padding_y_px = 0.1 * graph_height
        effective_y_range = (max_y_data - min_y_data) + (0.2 * abs(initial_hip_y - min_y_data))
        if effective_y_range == 0: effective_y_range = 1

        puntos = []
        max_points = 50
        start_index = max(0, len(historial_pos_y_cadera) - max_points)
        
        for i in range(start_index, len(historial_pos_y_cadera)):
            x = start_x + int((i - start_index) * graph_width / min(max_points, len(historial_pos_y_cadera) - start_index))
            y_normalized = (historial_pos_y_cadera[i] - min_y_data) / effective_y_range
            y = start_y + int((1 - y_normalized) * graph_height)
            puntos.append((x, y))

        if len(puntos) > 1:
            for i in range(1, len(puntos)):
                cv2.line(img, puntos[i-1], puntos[i], (0, 255, 0), 2)
        
        ref_y_normalized = (initial_hip_y - min_y_data) / effective_y_range
        ref_y_px_on_graph = start_y + int((1 - ref_y_normalized) * graph_height)

        cv2.line(img, (start_x, ref_y_px_on_graph), (start_x + graph_width, ref_y_px_on_graph), (0, 255, 255), 1)
        cv2.putText(img, "REF", (start_x - 30, ref_y_px_on_graph + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)

        cv2.putText(img, "ALTURA SALTO (m)", (start_x + 10, start_y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 0), 1)
        cv2.putText(img, f"Actual: {jump_height_m_actual:.2f}m", (start_x + 10, start_y + graph_height + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    @staticmethod
    def dibujar_guias_visuales(img, lm, estado_salto: EstadoSalto, analizador):
        if not lm: return
        
        try:
            h, w, _ = img.shape
            def get_px_coords(landmark_enum):
                p = lm[landmark_enum.value]
                return np.array([int(p.x * w), int(p.y * h)])

            lshoulder_px = get_px_coords(mp.solutions.pose.PoseLandmark.LEFT_SHOULDER)
            rshoulder_px = get_px_coords(mp.solutions.pose.PoseLandmark.RIGHT_SHOULDER)
            lhip_px = get_px_coords(mp.solutions.pose.PoseLandmark.LEFT_HIP)
            rhip_px = get_px_coords(mp.solutions.pose.PoseLandmark.RIGHT_HIP)
            lknee_px = get_px_coords(mp.solutions.pose.PoseLandmark.LEFT_KNEE)
            rknee_px = get_px_coords(mp.solutions.pose.PoseLandmark.RIGHT_KNEE)
            lankle_px = get_px_coords(mp.solutions.pose.PoseLandmark.LEFT_ANKLE)
            rankle_px = get_px_coords(mp.solutions.pose.PoseLandmark.RIGHT_ANKLE)
            
            # Línea de columna (hombro-cadera)
            cv2.line(img, lshoulder_px, lhip_px, (255, 0, 0), 2)
            cv2.line(img, rshoulder_px, rhip_px, (255, 0, 0), 2)

            # Línea de pierna (cadera-rodilla-tobillo)
            cv2.line(img, lhip_px, lknee_px, (0, 255, 0), 2)
            cv2.line(img, lknee_px, lankle_px, (0, 255, 0), 2)
            cv2.line(img, rhip_px, rknee_px, (0, 255, 0), 2)
            cv2.line(img, rknee_px, rankle_px, (0, 255, 0), 2)

            # Línea horizontal de rodillas para valgo
            if estado_salto in [EstadoSalto.CONTRAMOVIMIENTO, EstadoSalto.DESPEGUE, EstadoSalto.ATERRIZAJE]:
                knee_color = (0, 255, 0)
                current_knee_x_diff = abs(lm[mp.solutions.pose.PoseLandmark.LEFT_KNEE.value].x - lm[mp.solutions.pose.PoseLandmark.RIGHT_KNEE.value].x)
                if (current_knee_x_diff * analizador.px_to_m) < (analizador.initial_knee_x_diff * analizador.px_to_m - analizador.umbrales["rodillas_valgo_tolerancia_x"]):
                    knee_color = (0, 0, 255) # Rojo si hay valgo
                cv2.line(img, lknee_px, rknee_px, knee_color, 2)

            # Indicador de aterrizaje suave (círculo en pies)
            if estado_salto == EstadoSalto.ATERRIZAJE:
                landing_color = (0, 255, 255) # Amarillo
                if analizador.errores["stiff_landing"] > 0:
                    landing_color = (0, 0, 255) # Rojo
                cv2.circle(img, lankle_px, 15, landing_color, 2)
                cv2.circle(img, rankle_px, 15, landing_color, 2)
                
            # Instrucciones de movimiento según el estado
            if estado_salto == EstadoSalto.CONTRAMOVIMIENTO:
                cv2.putText(img, "FLEXIONE RODILLAS Y CADERAS", (w//2 - 150, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                cv2.putText(img, "Mantenga tronco recto", (w//2 - 100, 60), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 0), 1)

            elif estado_salto == EstadoSalto.DESPEGUE:
                cv2.putText(img, "EMPUJE CON FUERZA!", (w//2 - 100, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.putText(img, "Extienda completamente piernas", (w//2 - 140, 60), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 0), 1)

            elif estado_salto == EstadoSalto.ATERRIZAJE:
                cv2.putText(img, "FLEXIONE RODILLAS AL ATERRIZAR", (w//2 - 180, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)
                cv2.putText(img, "Absorba el impacto", (w//2 - 80, 60), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 0), 1)

        except Exception as e:
            logging.warning(f"Error dibujando guías visuales: {e}")

# --- Main execution loop ---
def main():
    # Mostrar instrucciones iniciales
    print("\n" + "="*50)
    print("   INSTRUCCIONES PARA UN ANÁLISIS PRECISO")
    print("="*50)
    print("1. Use ropa ajustada que permita ver su silueta")
    print("2. Asegúrese de tener buena iluminación")
    print("3. Manténgase a 2-3 metros de la cámara")
    print("4. Durante la calibración: Párese derecho con pies al ancho de hombros")
    print("5. En saltos: Mantenga las manos en la cadera o libres según el tipo de salto")
    print("6. Complete todo el movimiento (despegue y aterrizaje)")
    print("7. Descanse 15 segundos entre saltos")
    print("="*50)
    input("Presione ENTER para comenzar...")

    # 1. Configuración de perfil de usuario
    perfil = UsuarioPerfil.cargar_perfil()
    if perfil is None:
        perfil = UsuarioPerfil()
        perfil.obtener_datos_usuario()

    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: No se pudo abrir la cámara.")
        logging.error("No se pudo abrir la cámara.")
        return

    mp_pose = mp.solutions.pose
    pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

    analizador_saltos = AnalizadorSaltos(perfil)
    
    # Selección de tipo de salto
    print("\nSeleccione el tipo de salto:")
    print("1. Counter Movement Jump (CMJ)")
    print("2. Squat Jump (SQJ)")
    print("3. Abalakov")
    tipo_opcion = input("Ingrese el número correspondiente (1-3): ").strip()
    
    if tipo_opcion == "1":
        analizador_saltos.set_tipo_salto(TipoSalto.CMJ)
    elif tipo_opcion == "2":
        analizador_saltos.set_tipo_salto(TipoSalto.SQJ)
    elif tipo_opcion == "3":
        analizador_saltos.set_tipo_salto(TipoSalto.ABALAKOV)
    else:
        print("Opción inválida. Usando CMJ por defecto.")
        analizador_saltos.set_tipo_salto(TipoSalto.CMJ)

    calibrando = True
    calibracion_frames = 0
    max_calib_frames = 60
    debug_mode = True  # Modo depuración activado

    analizador_saltos.iniciar()

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("Error: No se pudo leer el frame de la cámara.")
            break

        frame = cv2.flip(frame, 1)
        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(image_rgb)

        lm = None
        if results.pose_landmarks:
            mp.solutions.drawing_utils.draw_landmarks(frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                                                     mp.solutions.drawing_utils.DrawingSpec(color=(245,117,66), thickness=2, circle_radius=2),
                                                     mp.solutions.drawing_utils.DrawingSpec(color=(245,66,230), thickness=2, circle_radius=2))
            lm = results.pose_landmarks.landmark

        if calibrando and lm:
            if analizador_saltos.calibrar(lm):
                calibracion_frames += 1
                progress = int(calibracion_frames / max_calib_frames * 100)
                msg = f"CALIBRANDO... {progress}% - Mantenga posición estable"
                InterfazVisual.dibujar_contenedor(frame, msg, 50, 50, 600, 50, (0, 255, 255), (0,0,0))
                
                # Dibujar guía visual de posición
                h, w = frame.shape[:2]
                cv2.putText(frame, "MANTENGA ESTA POSICION", (w//2 - 150, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                cv2.putText(frame, "Pies al ancho de hombros", (w//2 - 120, 60), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 0), 1)
                cv2.putText(frame, "Brazos ligeramente separados", (w//2 - 140, 85), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 0), 1)
                
                if calibracion_frames >= max_calib_frames:
                    calibrando = False
                    logging.info("Calibración completada.")
                    InterfazVisual.dibujar_contenedor(frame, "CALIBRACION COMPLETA. ¡Comienza a saltar!", 50, 50, 600, 50, (0, 255, 0), (0,0,0))
                    cv2.waitKey(1500)
            else:
                InterfazVisual.dibujar_contenedor(frame, "ERROR CALIBRACION: Asegurate de estar visible y quieto.", 50, 50, 600, 50, (0, 0, 255), (255,255,255))
                calibracion_frames = 0

        elif not calibrando and lm:
            angle_rodilla, postura_ok, detalles_salto = analizador_saltos.verificar(lm)
            
            # Dibujar contadores y estado
            InterfazVisual.dibujar_contenedor(frame, f"Saltos: {analizador_saltos.contador}", 20, 20, 200, 40, (20, 20, 160), (255, 255, 255))
            InterfazVisual.dibujar_contenedor(frame, f"Correctos: {analizador_saltos.correctas}", 20, 70, 200, 40, (20, 160, 20), (255, 255, 255))
            InterfazVisual.dibujar_contenedor(frame, f"Estado: {analizador_saltos.estado.value.replace('_', ' ').upper()}", 20, 120, 200, 40, (160, 20, 20), (255, 255, 255))
            InterfazVisual.dibujar_contenedor(frame, f"Altura Salto: {analizador_saltos.jump_height_m:.2f}m", 20, 170, 200, 40, (160, 160, 20), (255, 255, 255))
            InterfazVisual.dibujar_contenedor(frame, f"Tipo: {analizador_saltos.tipo_salto.value}", 20, 220, 200, 40, (100, 100, 100), (255, 255, 255), 0.6)
            
            # Dibujar barra de potencia
            InterfazVisual.dibujar_barra_potencia(frame, analizador_saltos.potencia, frame.shape[1] - 80, 50, 40, 200)

            # Dibujar semáforo técnico
            InterfazVisual.dibujar_semaforo_tecnico(frame, analizador_saltos.errores, frame.shape[1] - 250, 50)

            # Dibujar gráfico de altura de cadera
            InterfazVisual.dibujar_grafico_altura(frame, analizador_saltos.historial_pos_y_cadera, analizador_saltos.initial_hip_y, analizador_saltos.px_to_m, analizador_saltos.jump_height_m)
            
            # Dibujar guías visuales
            InterfazVisual.dibujar_guias_visuales(frame, lm, analizador_saltos.estado, analizador_saltos)

            # Mostrar mensajes de feedback
            y_offset_feedback = frame.shape[0] - 100
            for i, msg in enumerate(analizador_saltos.mensajes_feedback[-3:]):
                InterfazVisual.dibujar_contenedor(frame, msg, 20, y_offset_feedback + i * 30, 300, 25, (50,50,50), (255,255,255), 0.6)

        elif not lm:
            InterfazVisual.dibujar_contenedor(frame, "AJUSTE SU POSICION", 50, 50, 600, 50, (255, 165, 0), (255,255,255))
            cv2.putText(frame, "Asegure que todo su cuerpo sea visible", (100, 120), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            cv2.putText(frame, "Alejese/acerquese a la camara si es necesario", (100, 150), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            
        # Dibujar panel de ayuda permanente
        help_text = [
            "Teclas:",
            "1-CMJ  2-SQJ  3-Abalakov",
            "R-Reiniciar  Q-Salir",
            "C-Recalibrar"
        ]
        y_pos = 20
        for text in help_text:
            cv2.putText(frame, text, (frame.shape[1] - 200, y_pos), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 100), 1)
            y_pos += 25
            
        # Modo depuración: mostrar valores clave
        if debug_mode and lm:
            debug_info = [
                f"px_to_m: {analizador_saltos.px_to_m:.5f}",
                f"Hip Y: {analizador_saltos.initial_hip_y:.3f}",
                f"Estado: {analizador_saltos.estado.value}",
                f"Calibrado: {analizador_saltos.calibrado}"
            ]
            y_debug = 300
            for info in debug_info:
                cv2.putText(frame, info, (20, y_debug), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
                y_debug += 25

        cv2.imshow('Deteccion de Saltos', frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('r'): # Reiniciar la sesión de saltos
            print("Sesión reiniciada.")
            logging.info("Sesión reiniciada por el usuario.")
            analizador_saltos.iniciar()
            calibrando = True
            calibracion_frames = 0
        elif key == ord('c'): # Recalibrar
            print("Recalibrando...")
            logging.info("Recalibración iniciada por el usuario.")
            calibrando = True
            calibracion_frames = 0
        elif key == ord('1'):
            analizador_saltos.set_tipo_salto(TipoSalto.CMJ)
            print("Tipo de salto cambiado a CMJ")
        elif key == ord('2'):
            analizador_saltos.set_tipo_salto(TipoSalto.SQJ)
            print("Tipo de salto cambiado a SQJ")
        elif key == ord('3'):
            analizador_saltos.set_tipo_salto(TipoSalto.ABALAKOV)
            print("Tipo de salto cambiado a Abalakov")

    resultados_finales = analizador_saltos.finalizar()
    
    # Calcular índices de elasticidad y coordinación
    # Estos valores normalmente se calcularían comparando diferentes sesiones
    # En esta implementación, solo mostramos los valores base
    
    print("\n=== RESUMEN DE LA SESIÓN DE SALTOS ===")
    print(f"Usuario: {perfil.nombre}")
    print(f"Edad: {perfil.edad} años | Sexo: {perfil.sexo}")
    print(f"Peso: {perfil.peso_kg} kg | Altura: {perfil.altura_m:.2f} m")
    print(f"IMC: {perfil.imc:.1f} | Nivel: {perfil.nivel_actividad.capitalize()}")
    print(f"Tipo de salto: {resultados_finales['tipo_salto']}")
    print(f"Duración: {resultados_finales['duracion']}")
    print(f"Total de saltos: {resultados_finales['total']}")
    print(f"Saltos correctos: {resultados_finales['correctas']}")
    print(f"Precisión: {resultados_finales['precision']:.1f}%")
    print(f"Altura de Salto Promedio: {resultados_finales['altura_salto_promedio']:.2f}m ({resultados_finales['altura_salto_promedio']*100:.1f}cm)")
    print(f"Potencia Promedio: {resultados_finales['potencia_promedio']:.1f} Watts")
    print(f"Tiempo de Vuelo Promedio: {resultados_finales['tiempo_vuelo_promedio']:.3f}s")
    print(f"Clasificación: {resultados_finales['clasificacion']}")
    print(f"Evaluación de Rendimiento: {resultados_finales['evaluacion_rendimiento']}")
    print(f"Puntuación Técnica: {resultados_finales['puntuacion_tecnica']:.1f}/100")
    
    print("\n=== ERRORES DETECTADOS ===")
    for error, count in resultados_finales['errores'].items():
        if count > 0:
            print(f"- {error.replace('_', ' ').capitalize()}: {count} veces")
    
    print("\n=== RECOMENDACIONES ===")
    for i, rec in enumerate(resultados_finales['recomendaciones'], 1):
        print(f"{i}. {rec}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"saltos_{perfil.nombre.replace(' ', '_')}_{timestamp}.json"

    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(resultados_finales, f, indent=2, ensure_ascii=False)
        print(f"\n=== RESULTADOS GUARDADOS ===")
        print(f"Archivo: {filename}")
        logging.info(f"Resultados guardados en {filename}")
    except Exception as e:
        print(f"Error al guardar: {e}")
        logging.error(f"Error al guardar resultados: {e}")

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()