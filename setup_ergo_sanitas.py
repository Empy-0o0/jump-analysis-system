#!/usr/bin/env python3
"""
Script de Instalación y Configuración - Sistema Ergo SaniTas SpA
Automatiza la instalación y configuración inicial del sistema de análisis biomecánico

Este script verifica dependencias, configura el entorno y prepara el sistema
para su primer uso en el entorno de Ergo SaniTas SpA.
"""

import os
import sys
import subprocess
import platform
import json
from datetime import datetime

class ErgoSaniTasSetup:
    """Clase para manejar la instalación y configuración del sistema"""
    
    def __init__(self):
        self.sistema_os = platform.system()
        self.python_version = sys.version_info
        self.directorio_base = os.getcwd()
        self.errores = []
        self.advertencias = []
        
    def mostrar_bienvenida(self):
        """Muestra la pantalla de bienvenida del instalador"""
        print("\n" + "="*70)
        print("   ERGO SANITAS SpA - INSTALADOR DEL SISTEMA")
        print("="*70)
        print("   🏥 MEDICINA DEPORTIVA")
        print("   🔧 CONFIGURACIÓN AUTOMÁTICA DEL SISTEMA DE ANÁLISIS BIOMECÁNICO")
        print("="*70)
        print(f"   Sistema Operativo: {self.sistema_os}")
        print(f"   Versión de Python: {self.python_version.major}.{self.python_version.minor}.{self.python_version.micro}")
        print(f"   Directorio de instalación: {self.directorio_base}")
        print("="*70)
        
    def verificar_requisitos_sistema(self):
        """Verifica los requisitos mínimos del sistema"""
        print("\n🔍 VERIFICANDO REQUISITOS DEL SISTEMA...")
        
        # Verificar versión de Python
        if self.python_version < (3, 8):
            self.errores.append(f"Python 3.8+ requerido. Versión actual: {self.python_version.major}.{self.python_version.minor}")
        else:
            print(f"✅ Python {self.python_version.major}.{self.python_version.minor}.{self.python_version.micro} - OK")
        
        # Verificar pip
        try:
            subprocess.run([sys.executable, "-m", "pip", "--version"], 
                         check=True, capture_output=True)
            print("✅ pip - OK")
        except subprocess.CalledProcessError:
            self.errores.append("pip no está disponible")
        
        # Verificar espacio en disco (aproximado)
        try:
            import shutil
            espacio_libre = shutil.disk_usage(self.directorio_base).free / (1024**3)  # GB
            if espacio_libre < 2:
                self.advertencias.append(f"Espacio en disco bajo: {espacio_libre:.1f}GB disponibles")
            else:
                print(f"✅ Espacio en disco: {espacio_libre:.1f}GB - OK")
        except Exception:
            self.advertencias.append("No se pudo verificar el espacio en disco")
        
        # Verificar cámara (básico)
        try:
            import cv2
            cap = cv2.VideoCapture(0)
            if cap.isOpened():
                print("✅ Cámara detectada - OK")
                cap.release()
            else:
                self.advertencias.append("No se detectó cámara web")
        except ImportError:
            print("⚠️  OpenCV no instalado - se instalará con las dependencias")
        except Exception:
            self.advertencias.append("Error al verificar cámara")
    
    def instalar_dependencias(self):
        """Instala las dependencias del sistema"""
        print("\n📦 INSTALANDO DEPENDENCIAS...")
        
        if not os.path.exists("requirements.txt"):
            print("❌ Archivo requirements.txt no encontrado")
            self.errores.append("requirements.txt faltante")
            return False
        
        try:
            # Actualizar pip
            print("🔄 Actualizando pip...")
            subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], 
                         check=True, capture_output=True)
            
            # Instalar dependencias
            print("🔄 Instalando dependencias del proyecto...")
            resultado = subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                                     check=True, capture_output=True, text=True)
            
            print("✅ Dependencias instaladas correctamente")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Error instalando dependencias: {e}")
            if e.stdout:
                print(f"Salida: {e.stdout}")
            if e.stderr:
                print(f"Error: {e.stderr}")
            self.errores.append("Fallo en instalación de dependencias")
            return False
    
    def verificar_instalacion(self):
        """Verifica que las dependencias se instalaron correctamente"""
        print("\n🧪 VERIFICANDO INSTALACIÓN...")
        
        dependencias_criticas = [
            ("cv2", "OpenCV"),
            ("mediapipe", "MediaPipe"),
            ("numpy", "NumPy"),
            ("yaml", "PyYAML")
        ]
        
        for modulo, nombre in dependencias_criticas:
            try:
                __import__(modulo)
                print(f"✅ {nombre} - OK")
            except ImportError:
                print(f"❌ {nombre} - FALLO")
                self.errores.append(f"{nombre} no se pudo importar")
    
    def crear_estructura_directorios(self):
        """Crea la estructura de directorios necesaria"""
        print("\n📁 CREANDO ESTRUCTURA DE DIRECTORIOS...")
        
        directorios = [
            "logs",
            "perfiles",
            "sesiones",
            "reportes",
            "templates",
            "config"
        ]
        
        for directorio in directorios:
            try:
                os.makedirs(directorio, exist_ok=True)
                print(f"✅ Directorio '{directorio}' creado")
            except Exception as e:
                print(f"❌ Error creando directorio '{directorio}': {e}")
                self.advertencias.append(f"No se pudo crear directorio {directorio}")
    
    def configurar_archivos_iniciales(self):
        """Configura archivos de configuración iniciales"""
        print("\n⚙️ CONFIGURANDO ARCHIVOS INICIALES...")
        
        # Crear archivo de configuración de logging
        config_logging = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "standard": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                }
            },
            "handlers": {
                "file": {
                    "level": "INFO",
                    "class": "logging.FileHandler",
                    "filename": "logs/ergo_sanitas.log",
                    "formatter": "standard"
                }
            },
            "loggers": {
                "": {
                    "handlers": ["file"],
                    "level": "INFO",
                    "propagate": False
                }
            }
        }
        
        try:
            with open("config/logging_config.json", "w", encoding="utf-8") as f:
                json.dump(config_logging, f, indent=2)
            print("✅ Configuración de logging creada")
        except Exception as e:
            print(f"❌ Error creando configuración de logging: {e}")
            self.advertencias.append("No se pudo crear configuración de logging")
        
        # Crear archivo de configuración del sistema
        config_sistema = {
            "sistema": {
                "version": "2.0.0",
                "empresa": "Ergo SaniTas SpA",
                "fecha_instalacion": datetime.now().isoformat(),
                "directorio_base": self.directorio_base
            },
            "camara": {
                "indice_por_defecto": 0,
                "resolucion_ancho": 1280,
                "resolucion_alto": 720,
                "fps": 30
            },
            "analisis": {
                "frames_calibracion": 60,
                "umbral_confianza_deteccion": 0.5,
                "umbral_confianza_seguimiento": 0.5
            },
            "interfaz": {
                "mostrar_ayuda_inicial": True,
                "guardar_sesiones_automaticamente": True,
                "idioma": "es"
            }
        }
        
        try:
            with open("config/sistema_config.json", "w", encoding="utf-8") as f:
                json.dump(config_sistema, f, indent=2, ensure_ascii=False)
            print("✅ Configuración del sistema creada")
        except Exception as e:
            print(f"❌ Error creando configuración del sistema: {e}")
            self.advertencias.append("No se pudo crear configuración del sistema")
    
    def crear_scripts_utilidad(self):
        """Crea scripts de utilidad para el sistema"""
        print("\n🛠️ CREANDO SCRIPTS DE UTILIDAD...")
        
        # Script de inicio rápido
        script_inicio = '''#!/usr/bin/env python3
"""
Script de Inicio Rápido - Ergo SaniTas SpA
Inicia el sistema con configuración por defecto
"""

import sys
import os

# Agregar directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from main_ergo_sanitas import main
    print("🚀 Iniciando Sistema Ergo SaniTas...")
    main()
except ImportError as e:
    print(f"❌ Error de importación: {e}")
    print("Verifique que todas las dependencias estén instaladas")
except Exception as e:
    print(f"❌ Error inesperado: {e}")
    input("Presione ENTER para salir...")
'''
        
        try:
            with open("inicio_rapido.py", "w", encoding="utf-8") as f:
                f.write(script_inicio)
            print("✅ Script de inicio rápido creado")
        except Exception as e:
            print(f"❌ Error creando script de inicio: {e}")
            self.advertencias.append("No se pudo crear script de inicio")
        
        # Script de diagnóstico
        script_diagnostico = '''#!/usr/bin/env python3
"""
Script de Diagnóstico - Ergo SaniTas SpA
Verifica el estado del sistema y dependencias
"""

import sys
import cv2
import mediapipe as mp
import numpy as np

def diagnostico_completo():
    print("🔍 DIAGNÓSTICO DEL SISTEMA ERGO SANITAS")
    print("="*50)
    
    # Verificar OpenCV
    print(f"OpenCV versión: {cv2.__version__}")
    
    # Verificar MediaPipe
    print(f"MediaPipe versión: {mp.__version__}")
    
    # Verificar NumPy
    print(f"NumPy versión: {np.__version__}")
    
    # Probar cámara
    print("\\nProbando cámara...")
    cap = cv2.VideoCapture(0)
    if cap.isOpened():
        ret, frame = cap.read()
        if ret:
            print(f"✅ Cámara OK - Resolución: {frame.shape[1]}x{frame.shape[0]}")
        else:
            print("❌ No se pudo capturar frame")
        cap.release()
    else:
        print("❌ No se pudo abrir cámara")
    
    # Probar MediaPipe Pose
    print("\\nProbando MediaPipe Pose...")
    try:
        pose = mp.solutions.pose.Pose()
        print("✅ MediaPipe Pose inicializado correctamente")
        pose.close()
    except Exception as e:
        print(f"❌ Error con MediaPipe Pose: {e}")
    
    print("\\n✅ Diagnóstico completado")

if __name__ == "__main__":
    diagnostico_completo()
'''
        
        try:
            with open("diagnostico.py", "w", encoding="utf-8") as f:
                f.write(script_diagnostico)
            print("✅ Script de diagnóstico creado")
        except Exception as e:
            print(f"❌ Error creando script de diagnóstico: {e}")
            self.advertencias.append("No se pudo crear script de diagnóstico")
    
    def mostrar_resumen_instalacion(self):
        """Muestra el resumen final de la instalación"""
        print("\n" + "="*70)
        print("   RESUMEN DE INSTALACIÓN")
        print("="*70)
        
        if not self.errores:
            print("🎉 ¡INSTALACIÓN COMPLETADA EXITOSAMENTE!")
            print("\n✅ El sistema está listo para usar")
            print("\n🚀 PARA INICIAR EL SISTEMA:")
            print("   python main_ergo_sanitas.py")
            print("\n🔧 SCRIPTS DISPONIBLES:")
            print("   • python inicio_rapido.py - Inicio rápido")
            print("   • python diagnostico.py - Diagnóstico del sistema")
            print("   • python demo_web.py - Demostración web")
            
        else:
            print("❌ INSTALACIÓN COMPLETADA CON ERRORES")
            print("\n🔴 ERRORES ENCONTRADOS:")
            for error in self.errores:
                print(f"   • {error}")
        
        if self.advertencias:
            print("\n⚠️ ADVERTENCIAS:")
            for advertencia in self.advertencias:
                print(f"   • {advertencia}")
        
        print("\n📞 SOPORTE TÉCNICO:")
        print("   Email: tech@ergosanitas.cl")
        print("   Web: www.ergosanitas.cl")
        print("="*70)
    
    def ejecutar_instalacion(self):
        """Ejecuta el proceso completo de instalación"""
        try:
            self.mostrar_bienvenida()
            
            # Verificar requisitos
            self.verificar_requisitos_sistema()
            
            if self.errores:
                print("\n❌ No se puede continuar debido a errores críticos")
                self.mostrar_resumen_instalacion()
                return False
            
            # Confirmar instalación
            respuesta = input("\n¿Desea continuar con la instalación? (s/n): ").strip().lower()
            if respuesta not in ['s', 'si', 'yes', 'y']:
                print("⚠️ Instalación cancelada por el usuario")
                return False
            
            # Proceso de instalación
            if not self.instalar_dependencias():
                print("❌ Fallo en la instalación de dependencias")
                self.mostrar_resumen_instalacion()
                return False
            
            self.verificar_instalacion()
            self.crear_estructura_directorios()
            self.configurar_archivos_iniciales()
            self.crear_scripts_utilidad()
            
            # Resumen final
            self.mostrar_resumen_instalacion()
            
            return len(self.errores) == 0
            
        except KeyboardInterrupt:
            print("\n⚠️ Instalación interrumpida por el usuario")
            return False
        except Exception as e:
            print(f"\n❌ Error inesperado durante la instalación: {e}")
            return False

def main():
    """Función principal del instalador"""
    instalador = ErgoSaniTasSetup()
    exito = instalador.ejecutar_instalacion()
    
    if exito:
        print("\n🎯 ¡Sistema listo para evaluar atletas!")
        input("\nPresione ENTER para salir...")
    else:
        print("\n💡 Consulte la documentación o contacte soporte técnico")
        input("\nPresione ENTER para salir...")

if __name__ == "__main__":
    main()
