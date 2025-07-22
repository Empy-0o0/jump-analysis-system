#!/usr/bin/env python3
"""
Script de Pruebas del Sistema - Ergo SaniTas SpA
Verifica el funcionamiento de todos los módulos del sistema de análisis biomecánico

Este script ejecuta pruebas unitarias y de integración para validar
que el sistema funcione correctamente antes del despliegue.
"""

import sys
import os
import traceback
import json
import numpy as np
from datetime import datetime

# Agregar directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class TestSistemaErgoSaniTas:
    """Clase para ejecutar pruebas del sistema completo"""
    
    def __init__(self):
        self.pruebas_exitosas = 0
        self.pruebas_fallidas = 0
        self.errores = []
        
    def log_resultado(self, nombre_prueba, exitosa, mensaje=""):
        """Registra el resultado de una prueba"""
        if exitosa:
            print(f"✅ {nombre_prueba}")
            self.pruebas_exitosas += 1
        else:
            print(f"❌ {nombre_prueba} - {mensaje}")
            self.pruebas_fallidas += 1
            self.errores.append(f"{nombre_prueba}: {mensaje}")
    
    def test_importaciones(self):
        """Prueba que todos los módulos se puedan importar correctamente"""
        print("\n🔍 PROBANDO IMPORTACIONES DE MÓDULOS...")
        
        # Probar importaciones básicas
        try:
            import cv2
            self.log_resultado("Importación OpenCV", True)
        except ImportError as e:
            self.log_resultado("Importación OpenCV", False, str(e))
        
        try:
            import mediapipe as mp
            self.log_resultado("Importación MediaPipe", True)
        except ImportError as e:
            self.log_resultado("Importación MediaPipe", False, str(e))
        
        try:
            import numpy as np
            self.log_resultado("Importación NumPy", True)
        except ImportError as e:
            self.log_resultado("Importación NumPy", False, str(e))
        
        try:
            import yaml
            self.log_resultado("Importación PyYAML", True)
        except ImportError as e:
            self.log_resultado("Importación PyYAML", False, str(e))
        
        # Probar importaciones de módulos del sistema
        try:
            from user_profile import UsuarioPerfil
            self.log_resultado("Importación user_profile", True)
        except ImportError as e:
            self.log_resultado("Importación user_profile", False, str(e))
        
        try:
            from jump_analyzer import AnalizadorSaltos, TipoSalto, EstadoSalto
            self.log_resultado("Importación jump_analyzer", True)
        except ImportError as e:
            self.log_resultado("Importación jump_analyzer", False, str(e))
        
        try:
            from visual_interface import InterfazVisual
            self.log_resultado("Importación visual_interface", True)
        except ImportError as e:
            self.log_resultado("Importación visual_interface", False, str(e))
    
    def test_configuracion(self):
        """Prueba que el archivo de configuración se cargue correctamente"""
        print("\n⚙️ PROBANDO CONFIGURACIÓN...")
        
        try:
            import yaml
            if os.path.exists('config_Saltos.yaml'):
                with open('config_Saltos.yaml', 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                
                # Verificar secciones principales
                secciones_requeridas = ['proporciones', 'rom_optimo_salto', 'parametros_salto', 'nivel_usuario']
                for seccion in secciones_requeridas:
                    if seccion in config:
                        self.log_resultado(f"Configuración - {seccion}", True)
                    else:
                        self.log_resultado(f"Configuración - {seccion}", False, "Sección faltante")
                
                self.log_resultado("Carga de configuración YAML", True)
            else:
                self.log_resultado("Archivo config_Saltos.yaml", False, "Archivo no encontrado")
                
        except Exception as e:
            self.log_resultado("Carga de configuración YAML", False, str(e))
    
    def test_perfil_usuario(self):
        """Prueba la funcionalidad del perfil de usuario"""
        print("\n👤 PROBANDO PERFIL DE USUARIO...")
        
        try:
            from user_profile import UsuarioPerfil
            
            # Crear perfil de prueba
            perfil = UsuarioPerfil(
                nombre="Atleta Test",
                sexo="M",
                edad=25,
                altura_cm=175,
                peso_kg=70,
                nivel_actividad="intermedio"
            )
            
            # Verificar cálculos básicos
            if perfil.altura_m == 1.75:
                self.log_resultado("Cálculo altura en metros", True)
            else:
                self.log_resultado("Cálculo altura en metros", False, f"Esperado 1.75, obtenido {perfil.altura_m}")
            
            if 22 <= perfil.imc <= 23:
                self.log_resultado("Cálculo IMC", True)
            else:
                self.log_resultado("Cálculo IMC", False, f"IMC fuera de rango esperado: {perfil.imc}")
            
            # Verificar longitudes corporales
            perfil.calcular_longitudes()
            if perfil.longitudes["femur"] > 0:
                self.log_resultado("Cálculo longitud fémur", True)
            else:
                self.log_resultado("Cálculo longitud fémur", False, "Longitud cero o negativa")
            
            # Probar clasificación de nivel
            metricas_test = {
                'altura_salto_promedio': 0.35,
                'precision': 80,
                'puntuacion_tecnica': 75
            }
            nivel = perfil.clasificar_nivel_usuario(metricas_test)
            if nivel in ['principiante', 'intermedio', 'avanzado']:
                self.log_resultado("Clasificación de nivel", True)
            else:
                self.log_resultado("Clasificación de nivel", False, f"Nivel inválido: {nivel}")
            
            # Probar guardado/carga de perfil
            perfil.guardar_perfil("test_perfil.json")
            if os.path.exists("test_perfil.json"):
                self.log_resultado("Guardado de perfil", True)
                
                # Limpiar archivo de prueba
                os.remove("test_perfil.json")
            else:
                self.log_resultado("Guardado de perfil", False, "Archivo no creado")
                
        except Exception as e:
            self.log_resultado("Funcionalidad perfil usuario", False, str(e))
    
    def test_analizador_saltos(self):
        """Prueba la funcionalidad del analizador de saltos"""
        print("\n🏃 PROBANDO ANALIZADOR DE SALTOS...")
        
        try:
            from user_profile import UsuarioPerfil
            from jump_analyzer import AnalizadorSaltos, TipoSalto, EstadoSalto
            
            # Crear perfil y analizador de prueba
            perfil = UsuarioPerfil(
                nombre="Test",
                sexo="M", 
                edad=25,
                altura_cm=175,
                peso_kg=70,
                nivel_actividad="intermedio"
            )
            
            analizador = AnalizadorSaltos(perfil)
            
            # Verificar inicialización
            if analizador.estado == EstadoSalto.INICIAL:
                self.log_resultado("Inicialización analizador", True)
            else:
                self.log_resultado("Inicialización analizador", False, f"Estado inicial incorrecto: {analizador.estado}")
            
            # Probar configuración de tipo de salto
            analizador.set_tipo_salto(TipoSalto.CMJ)
            if analizador.tipo_salto == TipoSalto.CMJ:
                self.log_resultado("Configuración tipo de salto", True)
            else:
                self.log_resultado("Configuración tipo de salto", False, "Tipo no configurado correctamente")
            
            # Probar cálculo de potencia
            potencia = analizador.calcular_potencia(0.35)  # 35cm de altura
            if potencia > 0:
                self.log_resultado("Cálculo de potencia", True)
            else:
                self.log_resultado("Cálculo de potencia", False, f"Potencia inválida: {potencia}")
            
            # Probar cálculo de puntuación
            analizador.contador = 5
            analizador.correctas = 4
            puntuacion = analizador.calcular_puntuacion()
            if 0 <= puntuacion <= 100:
                self.log_resultado("Cálculo de puntuación", True)
            else:
                self.log_resultado("Cálculo de puntuación", False, f"Puntuación fuera de rango: {puntuacion}")
            
            # Probar generación de recomendaciones
            recomendaciones = analizador.generar_recomendaciones()
            if isinstance(recomendaciones, list) and len(recomendaciones) > 0:
                self.log_resultado("Generación de recomendaciones", True)
            else:
                self.log_resultado("Generación de recomendaciones", False, "Lista vacía o tipo incorrecto")
                
        except Exception as e:
            self.log_resultado("Funcionalidad analizador saltos", False, str(e))
    
    def test_interfaz_visual(self):
        """Prueba la funcionalidad de la interfaz visual"""
        print("\n🎨 PROBANDO INTERFAZ VISUAL...")
        
        try:
            import cv2
            from visual_interface import InterfazVisual
            
            # Crear imagen de prueba
            img_test = np.zeros((480, 640, 3), dtype=np.uint8)
            
            # Probar dibujo de contenedor
            InterfazVisual.dibujar_contenedor_moderno(
                img_test, "Test", 10, 10, 200, 50,
                InterfazVisual.COLORS['primary'],
                InterfazVisual.COLORS['text_primary']
            )
            self.log_resultado("Dibujo de contenedor", True)
            
            # Probar barra de potencia
            InterfazVisual.dibujar_barra_potencia_moderna(
                img_test, 75, 500, 50, 40, 200
            )
            self.log_resultado("Dibujo de barra de potencia", True)
            
            # Probar header corporativo
            InterfazVisual.dibujar_header_corporativo(
                img_test, "Test User", "Test Session"
            )
            self.log_resultado("Dibujo de header corporativo", True)
            
            # Verificar que la imagen se modificó
            if not np.array_equal(img_test, np.zeros((480, 640, 3), dtype=np.uint8)):
                self.log_resultado("Modificación de imagen", True)
            else:
                self.log_resultado("Modificación de imagen", False, "Imagen no modificada")
                
        except Exception as e:
            self.log_resultado("Funcionalidad interfaz visual", False, str(e))
    
    def test_mediapipe_pose(self):
        """Prueba la funcionalidad de MediaPipe Pose"""
        print("\n🤖 PROBANDO MEDIAPIPE POSE...")
        
        try:
            import mediapipe as mp
            import cv2
            
            # Inicializar MediaPipe Pose
            mp_pose = mp.solutions.pose
            pose = mp_pose.Pose(
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
            )
            
            # Crear imagen de prueba (persona simulada)
            img_test = np.ones((480, 640, 3), dtype=np.uint8) * 128
            
            # Procesar imagen
            results = pose.process(cv2.cvtColor(img_test, cv2.COLOR_BGR2RGB))
            
            # Verificar que MediaPipe funciona (aunque no detecte pose en imagen vacía)
            self.log_resultado("Inicialización MediaPipe Pose", True)
            
            # Verificar landmarks disponibles
            if hasattr(results, 'pose_landmarks'):
                self.log_resultado("Estructura de landmarks", True)
            else:
                self.log_resultado("Estructura de landmarks", False, "Atributo pose_landmarks no encontrado")
            
            pose.close()
            
        except Exception as e:
            self.log_resultado("Funcionalidad MediaPipe Pose", False, str(e))
    
    def test_calculo_angulos(self):
        """Prueba los cálculos de ángulos 3D"""
        print("\n📐 PROBANDO CÁLCULOS DE ÁNGULOS...")
        
        try:
            from jump_analyzer import AnalizadorSaltos
            
            # Puntos de prueba para formar un ángulo de 90 grados
            punto_a = np.array([0, 1, 0])  # Arriba
            punto_b = np.array([0, 0, 0])  # Centro
            punto_c = np.array([1, 0, 0])  # Derecha
            
            angulo = AnalizadorSaltos._angle_3d(punto_a, punto_b, punto_c)
            
            # Verificar que el ángulo calculado sea aproximadamente 90 grados
            if 89 <= angulo <= 91:
                self.log_resultado("Cálculo de ángulo 90°", True)
            else:
                self.log_resultado("Cálculo de ángulo 90°", False, f"Ángulo calculado: {angulo}°")
            
            # Probar ángulo de 180 grados (línea recta)
            punto_a = np.array([0, 0, 0])
            punto_b = np.array([1, 0, 0])
            punto_c = np.array([2, 0, 0])
            
            angulo = AnalizadorSaltos._angle_3d(punto_a, punto_b, punto_c)
            
            if 179 <= angulo <= 181:
                self.log_resultado("Cálculo de ángulo 180°", True)
            else:
                self.log_resultado("Cálculo de ángulo 180°", False, f"Ángulo calculado: {angulo}°")
                
        except Exception as e:
            self.log_resultado("Cálculos de ángulos", False, str(e))
    
    def test_demo_web(self):
        """Prueba la funcionalidad del demo web"""
        print("\n🌐 PROBANDO DEMO WEB...")
        
        try:
            from demo_web import DemoData
            
            # Probar generación de datos demo
            perfil_demo = DemoData.generar_perfil_demo()
            if isinstance(perfil_demo, dict) and 'nombre' in perfil_demo:
                self.log_resultado("Generación perfil demo", True)
            else:
                self.log_resultado("Generación perfil demo", False, "Estructura incorrecta")
            
            metricas_demo = DemoData.generar_metricas_demo()
            if isinstance(metricas_demo, dict) and 'altura_promedio' in metricas_demo:
                self.log_resultado("Generación métricas demo", True)
            else:
                self.log_resultado("Generación métricas demo", False, "Estructura incorrecta")
            
            errores_demo = DemoData.generar_errores_demo()
            if isinstance(errores_demo, dict):
                self.log_resultado("Generación errores demo", True)
            else:
                self.log_resultado("Generación errores demo", False, "Tipo incorrecto")
                
        except Exception as e:
            self.log_resultado("Funcionalidad demo web", False, str(e))
    
    def test_integracion_completa(self):
        """Prueba de integración completa del sistema"""
        print("\n🔗 PROBANDO INTEGRACIÓN COMPLETA...")
        
        try:
            from user_profile import UsuarioPerfil
            from jump_analyzer import AnalizadorSaltos, TipoSalto
            from visual_interface import InterfazVisual
            import cv2
            
            # Crear perfil
            perfil = UsuarioPerfil(
                nombre="Test Integración",
                sexo="F",
                edad=22,
                altura_cm=165,
                peso_kg=60,
                nivel_actividad="principiante"
            )
            
            # Crear analizador
            analizador = AnalizadorSaltos(perfil)
            analizador.set_tipo_salto(TipoSalto.CMJ)
            analizador.iniciar()
            
            # Simular algunos datos de salto
            analizador.contador = 3
            analizador.correctas = 2
            analizador.alturas_saltos = [0.25, 0.28, 0.22]
            analizador.potencias = [2200, 2400, 2100]
            analizador.tiempos_vuelo = [0.35, 0.38, 0.33]
            
            # Generar reporte final
            resultados = analizador.finalizar()
            
            # Verificar estructura del reporte
            secciones_requeridas = ['usuario', 'sesion', 'metricas', 'evaluacion', 'errores', 'recomendaciones']
            todas_presentes = all(seccion in resultados for seccion in secciones_requeridas)
            
            if todas_presentes:
                self.log_resultado("Estructura de reporte final", True)
            else:
                self.log_resultado("Estructura de reporte final", False, "Secciones faltantes")
            
            # Crear imagen para interfaz
            img_test = np.zeros((720, 1280, 3), dtype=np.uint8)
            InterfazVisual.dibujar_resumen_sesion(img_test, resultados)
            
            self.log_resultado("Integración completa del sistema", True)
            
        except Exception as e:
            self.log_resultado("Integración completa del sistema", False, str(e))
    
    def ejecutar_todas_las_pruebas(self):
        """Ejecuta todas las pruebas del sistema"""
        print("🧪 INICIANDO PRUEBAS DEL SISTEMA ERGO SANITAS SpA")
        print("="*60)
        print("Sistema de Análisis Biomecánico de Saltos")
        print("Medicina Deportiva - Validación Técnica")
        print("="*60)
        
        # Ejecutar todas las pruebas
        self.test_importaciones()
        self.test_configuracion()
        self.test_perfil_usuario()
        self.test_analizador_saltos()
        self.test_interfaz_visual()
        self.test_mediapipe_pose()
        self.test_calculo_angulos()
        self.test_demo_web()
        self.test_integracion_completa()
        
        # Mostrar resumen final
        self.mostrar_resumen()
    
    def mostrar_resumen(self):
        """Muestra el resumen final de las pruebas"""
        print("\n" + "="*60)
        print("   RESUMEN DE PRUEBAS")
        print("="*60)
        
        total_pruebas = self.pruebas_exitosas + self.pruebas_fallidas
        porcentaje_exito = (self.pruebas_exitosas / total_pruebas * 100) if total_pruebas > 0 else 0
        
        print(f"📊 ESTADÍSTICAS:")
        print(f"   Total de pruebas: {total_pruebas}")
        print(f"   Pruebas exitosas: {self.pruebas_exitosas}")
        print(f"   Pruebas fallidas: {self.pruebas_fallidas}")
        print(f"   Porcentaje de éxito: {porcentaje_exito:.1f}%")
        
        if self.pruebas_fallidas == 0:
            print("\n🎉 ¡TODAS LAS PRUEBAS PASARON EXITOSAMENTE!")
            print("✅ El sistema está listo para producción")
            print("🚀 Puede proceder con la implementación en Ergo SaniTas SpA")
        else:
            print(f"\n⚠️ {self.pruebas_fallidas} PRUEBAS FALLARON")
            print("\n❌ ERRORES ENCONTRADOS:")
            for error in self.errores:
                print(f"   • {error}")
            print("\n🔧 Corrija estos errores antes del despliegue")
        
        print("\n📞 SOPORTE TÉCNICO:")
        print("   Email: tech@ergosanitas.cl")
        print("   Web: www.ergosanitas.cl")
        print("="*60)
        
        return self.pruebas_fallidas == 0

def main():
    """Función principal del script de pruebas"""
    try:
        # Importar dependencias necesarias
        import yaml
        import cv2
        import mediapipe as mp
        import numpy as np
        
        # Ejecutar pruebas
        tester = TestSistemaErgoSaniTas()
        exito = tester.ejecutar_todas_las_pruebas()
        
        # Guardar reporte de pruebas
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        reporte = {
            "fecha": datetime.now().isoformat(),
            "total_pruebas": tester.pruebas_exitosas + tester.pruebas_fallidas,
            "exitosas": tester.pruebas_exitosas,
            "fallidas": tester.pruebas_fallidas,
            "porcentaje_exito": (tester.pruebas_exitosas / (tester.pruebas_exitosas + tester.pruebas_fallidas) * 100) if (tester.pruebas_exitosas + tester.pruebas_fallidas) > 0 else 0,
            "errores": tester.errores,
            "sistema_listo": exito
        }
        
        with open(f"reporte_pruebas_{timestamp}.json", "w", encoding="utf-8") as f:
            json.dump(reporte, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Reporte guardado: reporte_pruebas_{timestamp}.json")
        
        return exito
        
    except ImportError as e:
        print(f"❌ Error de importación: {e}")
        print("🔧 Ejecute: python setup_ergo_sanitas.py")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    exito = main()
    sys.exit(0 if exito else 1)
