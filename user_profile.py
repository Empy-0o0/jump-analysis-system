import json
import os
import logging
from datetime import datetime
import yaml

# Cargar configuración
try:
    with open('config_Saltos.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    PROPORCIONES = config.get('proporciones', {})
    NIVEL_USUARIO = config.get('nivel_usuario', {})
except FileNotFoundError:
    logging.error("config_Saltos.yaml no encontrado. Usando parámetros por defecto.")
    PROPORCIONES = {
        'm': {'altura_femur': 0.23, 'altura_tibia': 0.22, 'distancia_rodillas': 0.18},
        'f': {'altura_femur': 0.22, 'altura_tibia': 0.21, 'distancia_rodillas': 0.17}
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

class UsuarioPerfil:
    """
    Clase para gestionar el perfil del usuario/atleta en el sistema de análisis de saltos
    de Ergo SaniTas SpA. Incluye datos antropométricos, nivel de actividad y cálculos
    biomecánicos personalizados.
    """
    
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
        """
        Calcula las longitudes de los segmentos corporales basado en proporciones
        antropométricas y factores de corrección por edad.
        """
        # Factor de corrección por edad
        factor_correccion = 0.97 if self.edad > 50 else 1.0

        self.longitudes = {
            "femur": self.altura_m * PROPORCIONES[self.sexo.lower()]['altura_femur'] * factor_correccion,
            "tibia": self.altura_m * PROPORCIONES[self.sexo.lower()]['altura_tibia'] * factor_correccion,
            "distancia_rodillas": self.altura_m * PROPORCIONES[self.sexo.lower()]['distancia_rodillas'] * factor_correccion
        }
        self.umbrales_nivel = NIVEL_USUARIO[self.nivel_actividad]

    def obtener_datos_usuario(self):
        """
        Interfaz interactiva para solicitar y validar los datos del usuario.
        Incluye validaciones específicas para el contexto de medicina deportiva.
        """
        print("\n" + "="*60)
        print("   ERGO SANITAS SpA - CONFIGURACIÓN DE PERFIL DE ATLETA")
        print("="*60)
        print("   Sistema de Evaluación Biomecánica de Saltos")
        print("   Medicina Deportiva - Análisis de Rendimiento")
        print("="*60)

        while not self.nombre:
            self.nombre = input("Nombre completo del atleta: ").strip()
            if not self.nombre:
                print("❌ El nombre es obligatorio para el registro")

        while self.sexo not in ['M', 'F']:
            sexo_input = input("Sexo (M/F): ").strip().upper()
            if sexo_input in ['M', 'F']:
                self.sexo = sexo_input
            else:
                print("❌ Ingrese M para Masculino o F para Femenino")

        while self.edad <= 0 or self.edad > 100:
            try:
                edad_input = int(input("Edad (años): "))
                if 10 <= edad_input <= 100:
                    self.edad = edad_input
                else:
                    print("❌ La edad debe estar entre 10 y 100 años")
            except ValueError:
                print("❌ Entrada inválida. Por favor, ingrese un número.")

        while self.altura_cm <= 0 or self.altura_cm > 250:
            try:
                altura_input = float(input("Altura en cm (ej. 175): "))
                if 100 <= altura_input <= 250:
                    self.altura_cm = altura_input
                else:
                    print("❌ La altura debe estar entre 100 y 250 cm")
            except ValueError:
                print("❌ Entrada inválida. Por favor, ingrese un número.")

        while self.peso_kg <= 0 or self.peso_kg > 200:
            try:
                peso_input = float(input("Peso en kg (ej. 70.5): "))
                if 30 <= peso_input <= 200:
                    self.peso_kg = peso_input
                else:
                    print("❌ El peso debe estar entre 30 y 200 kg")
            except ValueError:
                print("❌ Entrada inválida. Por favor, ingrese un número.")

        print("\nNiveles de actividad disponibles:")
        print("- principiante: Poca experiencia en saltos/ejercicio")
        print("- intermedio: Experiencia moderada, entrena regularmente")
        print("- avanzado: Atleta experimentado, entrena intensivamente")
        
        niveles_disponibles = list(NIVEL_USUARIO.keys())
        while self.nivel_actividad not in niveles_disponibles:
            nivel_input = input(f"Nivel de actividad ({'/'.join(niveles_disponibles)}): ").strip().lower()
            if nivel_input in niveles_disponibles:
                self.nivel_actividad = nivel_input
            else:
                print(f"❌ Nivel inválido. Por favor, elija entre: {', '.join(niveles_disponibles)}")

        # Recalcular valores derivados
        self.altura_m = self.altura_cm / 100.0
        self.imc = self.peso_kg / (self.altura_m ** 2) if self.altura_m > 0 else 0

        # Recalcular longitudes con los nuevos datos
        self.calcular_longitudes()

        # Mostrar resumen del perfil
        self._mostrar_resumen_perfil()
        
        print("✅ Perfil de atleta configurado correctamente.")
        self.guardar_perfil()

    def _mostrar_resumen_perfil(self):
        """Muestra un resumen del perfil creado"""
        print("\n" + "="*50)
        print("   RESUMEN DEL PERFIL")
        print("="*50)
        print(f"Nombre: {self.nombre}")
        print(f"Sexo: {'Masculino' if self.sexo == 'M' else 'Femenino'}")
        print(f"Edad: {self.edad} años")
        print(f"Altura: {self.altura_cm} cm ({self.altura_m:.2f} m)")
        print(f"Peso: {self.peso_kg} kg")
        print(f"IMC: {self.imc:.1f}")
        print(f"Nivel: {self.nivel_actividad.capitalize()}")
        print(f"Tolerancia angular: ±{self.umbrales_nivel['tolerancia_angulo']}°")
        print("="*50)

    def clasificar_nivel_usuario(self, metricas_sesion):
        """
        Clasifica al usuario en principiante, intermedio o avanzado basado en
        las métricas de la sesión de saltos.
        
        Args:
            metricas_sesion (dict): Diccionario con métricas de rendimiento
            
        Returns:
            str: Nivel clasificado ('principiante', 'intermedio', 'avanzado')
        """
        altura_promedio = metricas_sesion.get('altura_salto_promedio', 0)
        precision = metricas_sesion.get('precision', 0)
        puntuacion_tecnica = metricas_sesion.get('puntuacion_tecnica', 0)
        
        # Convertir altura a cm para comparación
        altura_cm = altura_promedio * 100
        
        # Criterios de clasificación basados en estándares biomecánicos
        if self.sexo == 'M':  # Hombres
            if altura_cm >= 35 and precision >= 80 and puntuacion_tecnica >= 75:
                return 'avanzado'
            elif altura_cm >= 25 and precision >= 60 and puntuacion_tecnica >= 60:
                return 'intermedio'
            else:
                return 'principiante'
        else:  # Mujeres
            if altura_cm >= 28 and precision >= 80 and puntuacion_tecnica >= 75:
                return 'avanzado'
            elif altura_cm >= 20 and precision >= 60 and puntuacion_tecnica >= 60:
                return 'intermedio'
            else:
                return 'principiante'

    def generar_recomendaciones_personalizadas(self, errores_sesion, nivel_clasificado):
        """
        Genera recomendaciones personalizadas basadas en el perfil del usuario
        y los errores detectados en la sesión.
        
        Args:
            errores_sesion (dict): Errores detectados durante la sesión
            nivel_clasificado (str): Nivel clasificado del usuario
            
        Returns:
            list: Lista de recomendaciones personalizadas
        """
        recomendaciones = []
        
        # Recomendaciones basadas en errores específicos
        if errores_sesion.get("insufficient_cm_depth", 0) > 0:
            if nivel_clasificado == 'principiante':
                recomendaciones.append("Practique sentadillas profundas para mejorar flexibilidad")
                recomendaciones.append("Realice estiramientos de cadera y tobillos diariamente")
            else:
                recomendaciones.append("Trabaje movilidad dinámica pre-entrenamiento")
                recomendaciones.append("Incorpore sentadillas con pausa en posición baja")
        
        if errores_sesion.get("rodillas_valgo_takeoff", 0) > 0:
            recomendaciones.append("Fortalezca glúteos medios con ejercicios específicos")
            recomendaciones.append("Practique sentadillas con banda elástica alrededor de rodillas")
            if self.sexo == 'F':
                recomendaciones.append("Enfoque especial en control neuromuscular de rodillas")
        
        if errores_sesion.get("stiff_landing", 0) > 0:
            recomendaciones.append("Practique aterrizajes suaves desde diferentes alturas")
            recomendaciones.append("Trabaje la absorción del impacto con ejercicios excéntricos")
        
        # Recomendaciones basadas en edad
        if self.edad > 40:
            recomendaciones.append("Incluya calentamiento extendido antes de saltos")
            recomendaciones.append("Considere ejercicios de bajo impacto como complemento")
        
        # Recomendaciones basadas en IMC
        if self.imc > 25:
            recomendaciones.append("Combine entrenamiento de saltos con trabajo cardiovascular")
            recomendaciones.append("Progrese gradualmente la intensidad de los ejercicios")
        
        # Recomendaciones generales por nivel
        if nivel_clasificado == 'principiante':
            recomendaciones.append("Enfoque en técnica antes que en altura de salto")
            recomendaciones.append("Realice 2-3 sesiones por semana con descanso adecuado")
        elif nivel_clasificado == 'intermedio':
            recomendaciones.append("Incorpore variaciones de saltos (unilaterales, con giro)")
            recomendaciones.append("Aumente progresivamente la complejidad de los ejercicios")
        else:  # avanzado
            recomendaciones.append("Enfoque en optimización de potencia y velocidad")
            recomendaciones.append("Considere entrenamiento pliométrico avanzado")
        
        return recomendaciones

    def guardar_perfil(self, filename=None):
        """
        Guarda el perfil del usuario en un archivo JSON.
        
        Args:
            filename (str, optional): Nombre del archivo. Si no se especifica,
                                    se genera automáticamente.
        """
        if filename is None:
            nombre_archivo = self.nombre.replace(' ', '_').lower()
            filename = f"perfil_{nombre_archivo}.json"
        
        data = self.__dict__.copy()
        # Eliminar atributos que se recalculan automáticamente
        data.pop('altura_m', None)
        data.pop('imc', None)
        data.pop('longitudes', None)
        data.pop('umbrales_nivel', None)
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            logging.info(f"Perfil de usuario guardado en {filename}")
            print(f"📁 Perfil guardado en: {filename}")
        except Exception as e:
            logging.error(f"Error al guardar el perfil: {e}")
            print(f"❌ Error al guardar el perfil: {e}")

    @classmethod
    def cargar_perfil(cls, filename=None):
        """
        Carga un perfil de usuario desde un archivo JSON.
        
        Args:
            filename (str, optional): Nombre del archivo. Si no se especifica,
                                    busca el más reciente.
                                    
        Returns:
            UsuarioPerfil: Instancia del perfil cargado o None si hay error
        """
        if filename is None:
            # Buscar el archivo de perfil más reciente
            archivos_perfil = [f for f in os.listdir('.') if f.startswith('perfil_') and f.endswith('.json')]
            if not archivos_perfil:
                return None
            filename = max(archivos_perfil, key=os.path.getctime)
        
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
                
                # Recalcular valores derivados
                perfil.calcular_longitudes()
                
                logging.info(f"Perfil de usuario cargado desde {filename}")
                print(f"📁 Perfil cargado: {perfil.nombre}")
                return perfil
                
            except Exception as e:
                logging.error(f"Error al cargar el perfil: {e}")
                print(f"❌ Error al cargar el perfil: {e}")
                return None
        return None

    def listar_perfiles_disponibles(self):
        """
        Lista todos los perfiles disponibles en el directorio actual.
        
        Returns:
            list: Lista de nombres de archivos de perfiles
        """
        archivos_perfil = [f for f in os.listdir('.') if f.startswith('perfil_') and f.endswith('.json')]
        return sorted(archivos_perfil, key=os.path.getctime, reverse=True)

    def __str__(self):
        """Representación en string del perfil"""
        return f"UsuarioPerfil({self.nombre}, {self.sexo}, {self.edad}años, {self.nivel_actividad})"

    def __repr__(self):
        """Representación técnica del perfil"""
        return self.__str__()
