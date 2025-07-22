#!/usr/bin/env python3
"""
Sistema de Análisis Biomecánico de Saltos - Ergo SaniTas SpA
Medicina Deportiva - Evaluación de Rendimiento Atlético

Este sistema permite a los atletas autoevaluarse y determinar su nivel
entre principiante, intermedio y avanzado mediante análisis biomecánico
en tiempo real de diferentes tipos de saltos.

Desarrollado para: Ergo SaniTas SpA - Chile
Versión: 2.0
"""

import cv2
import mediapipe as mp
import numpy as np
import json
import time
import logging
import os
from datetime import datetime

# Importar módulos del sistema
from user_profile import UsuarioPerfil
from jump_analyzer import AnalizadorSaltos, TipoSalto, EstadoSalto
from visual_interface import InterfazVisual

# Configuración de logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s', 
    filename=f'ergo_sanitas_session_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
)

class SistemaErgoSaniTas:
    """
    Clase principal del Sistema de Análisis Biomecánico de Saltos
    para Ergo SaniTas SpA.
    
    Integra todos los módulos del sistema para proporcionar una experiencia
    completa de evaluación biomecánica para atletas.
    """
    
    def __init__(self):
        self.perfil_usuario = None
        self.analizador_saltos = None
        self.interfaz_visual = InterfazVisual()
        
        # Estado del sistema
        self.calibrando = True
        self.calibracion_frames = 0
        self.max_calib_frames = 60
        self.mostrar_ayuda = False
        self.sesion_activa = False
        
        # MediaPipe setup
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            min_detection_confidence=0.5, 
            min_tracking_confidence=0.5
        )
        
        # Cámara
        self.cap = None
        
        logging.info("Sistema Ergo SaniTas inicializado")

    def mostrar_bienvenida(self):
        """Muestra la pantalla de bienvenida del sistema"""
        print("\n" + "="*70)
        print("   ERGO SANITAS SpA - SISTEMA DE ANÁLISIS BIOMECÁNICO")
        print("="*70)
        print("   🏥 MEDICINA DEPORTIVA - EVALUACIÓN DE RENDIMIENTO ATLÉTICO")
        print("   🏃 ANÁLISIS DE SALTOS EN TIEMPO REAL")
        print("   📊 CLASIFICACIÓN AUTOMÁTICA DE NIVEL DEPORTIVO")
        print("="*70)
        print()
        print("CARACTERÍSTICAS DEL SISTEMA:")
        print("• Análisis biomecánico en tiempo real")
        print("• Detección automática de errores técnicos")
        print("• Clasificación en: Principiante, Intermedio, Avanzado")
        print("• Recomendaciones personalizadas de entrenamiento")
        print("• Tipos de salto: CMJ, SQJ, Abalakov")
        print("• Reportes detallados de sesión")
        print()
        print("INSTRUCCIONES DE SEGURIDAD:")
        print("⚠️  Realice saltos solo si está en condiciones físicas adecuadas")
        print("⚠️  Detenga el ejercicio si siente molestias o dolor")
        print("⚠️  Asegúrese de tener espacio suficiente y superficie adecuada")
        print("⚠️  Use ropa deportiva apropiada")
        print("="*70)
        
        input("\n📋 Presione ENTER para configurar su perfil de atleta...")

    def configurar_perfil_usuario(self):
        """Configura o carga el perfil del usuario"""
        print("\n🔍 Buscando perfiles existentes...")
        
        # Intentar cargar perfil existente
        perfil_existente = UsuarioPerfil.cargar_perfil()
        
        if perfil_existente:
            print(f"✅ Perfil encontrado: {perfil_existente.nombre}")
            print(f"   Edad: {perfil_existente.edad} años")
            print(f"   Nivel: {perfil_existente.nivel_actividad.capitalize()}")
            
            usar_existente = input("\n¿Desea usar este perfil? (s/n): ").strip().lower()
            if usar_existente in ['s', 'si', 'yes', 'y']:
                self.perfil_usuario = perfil_existente
                return
        
        # Crear nuevo perfil
        print("\n📝 Creando nuevo perfil de atleta...")
        self.perfil_usuario = UsuarioPerfil()
        self.perfil_usuario.obtener_datos_usuario()

    def inicializar_camara(self):
        """Inicializa la cámara del sistema"""
        print("\n📹 Inicializando cámara...")
        
        self.cap = cv2.VideoCapture(0)
        
        if not self.cap.isOpened():
            print("❌ Error: No se pudo acceder a la cámara")
            print("   Verifique que:")
            print("   • La cámara esté conectada correctamente")
            print("   • No esté siendo usada por otra aplicación")
            print("   • Tenga permisos de acceso a la cámara")
            return False
        
        # Configurar resolución óptima
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        
        print("✅ Cámara inicializada correctamente")
        return True

    def seleccionar_tipo_salto(self):
        """Permite al usuario seleccionar el tipo de salto a analizar"""
        print("\n🏃 SELECCIÓN DE TIPO DE SALTO")
        print("="*40)
        print("1. CMJ (Counter Movement Jump)")
        print("   • Salto con contramovimiento")
        print("   • Más común y natural")
        print("   • Evalúa potencia reactiva")
        print()
        print("2. SQJ (Squat Jump)")
        print("   • Salto desde posición estática")
        print("   • Sin contramovimiento")
        print("   • Evalúa potencia concéntrica pura")
        print()
        print("3. Abalakov")
        print("   • Salto con uso de brazos")
        print("   • Máxima altura posible")
        print("   • Evalúa coordinación total")
        print("="*40)
        
        while True:
            try:
                opcion = input("Seleccione el tipo de salto (1-3): ").strip()
                
                if opcion == "1":
                    self.analizador_saltos.set_tipo_salto(TipoSalto.CMJ)
                    print("✅ Tipo de salto: CMJ seleccionado")
                    break
                elif opcion == "2":
                    self.analizador_saltos.set_tipo_salto(TipoSalto.SQJ)
                    print("✅ Tipo de salto: SQJ seleccionado")
                    break
                elif opcion == "3":
                    self.analizador_saltos.set_tipo_salto(TipoSalto.ABALAKOV)
                    print("✅ Tipo de salto: Abalakov seleccionado")
                    break
                else:
                    print("❌ Opción inválida. Por favor, seleccione 1, 2 o 3.")
                    
            except KeyboardInterrupt:
                print("\n⚠️ Operación cancelada por el usuario")
                return False
        
        return True

    def ejecutar_calibracion(self, frame, lm):
        """
        Ejecuta el proceso de calibración del sistema
        
        Args:
            frame: Frame de video actual
            lm: Landmarks de MediaPipe
            
        Returns:
            bool: True si la calibración está completa
        """
        if lm and self.analizador_saltos.calibrar(lm):
            self.calibracion_frames += 1
            progreso = (self.calibracion_frames / self.max_calib_frames) * 100
            
            # Dibujar pantalla de calibración
            self.interfaz_visual.dibujar_pantalla_calibracion(
                frame, progreso, "Mantenga posición estable"
            )
            
            if self.calibracion_frames >= self.max_calib_frames:
                self.calibrando = False
                self.sesion_activa = True
                logging.info("Calibración completada exitosamente")
                
                # Mostrar mensaje de éxito
                self.interfaz_visual.dibujar_pantalla_calibracion(
                    frame, 100, "¡Calibración completa! Comenzando análisis..."
                )
                cv2.imshow('Ergo SaniTas - Análisis Biomecánico', frame)
                cv2.waitKey(2000)  # Mostrar mensaje por 2 segundos
                
                return True
        else:
            # Error en calibración
            self.interfaz_visual.dibujar_pantalla_calibracion(
                frame, 0, "Error: Asegúrese de estar visible y quieto"
            )
            self.calibracion_frames = 0
        
        return False

    def procesar_frame_analisis(self, frame, lm):
        """
        Procesa un frame durante el análisis activo
        
        Args:
            frame: Frame de video actual
            lm: Landmarks de MediaPipe
        """
        if not lm:
            # Sin detección de pose
            self.interfaz_visual.dibujar_contenedor_moderno(
                frame, "AJUSTE SU POSICIÓN", 50, 50, 600, 50, 
                InterfazVisual.COLORS['warning'], InterfazVisual.COLORS['text_primary']
            )
            cv2.putText(frame, "Asegúrese de que todo su cuerpo sea visible", 
                       (100, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.6, 
                       InterfazVisual.COLORS['text_primary'], 1)
            return

        # Realizar análisis biomecánico
        angle_rodilla, postura_ok, detalles_salto = self.analizador_saltos.verificar(lm)
        
        # Dibujar header corporativo
        self.interfaz_visual.dibujar_header_corporativo(
            frame, self.perfil_usuario.nombre, 
            f"Sesión: {datetime.now().strftime('%H:%M:%S')}"
        )
        
        # Dibujar contadores principales
        self.interfaz_visual.dibujar_contenedor_moderno(
            frame, f"Saltos: {self.analizador_saltos.contador}", 
            20, 100, 180, 40, InterfazVisual.COLORS['primary'], 
            InterfazVisual.COLORS['text_primary']
        )
        
        self.interfaz_visual.dibujar_contenedor_moderno(
            frame, f"Correctos: {self.analizador_saltos.correctas}", 
            20, 150, 180, 40, InterfazVisual.COLORS['success'], 
            InterfazVisual.COLORS['text_primary']
        )
        
        precision = (self.analizador_saltos.correctas / max(self.analizador_saltos.contador, 1)) * 100
        self.interfaz_visual.dibujar_contenedor_moderno(
            frame, f"Precisión: {precision:.1f}%", 
            20, 200, 180, 40, InterfazVisual.COLORS['info'], 
            InterfazVisual.COLORS['text_primary']
        )
        
        # Estado actual del salto
        estado_color = InterfazVisual.COLORS['secondary']
        if self.analizador_saltos.estado == EstadoSalto.CONTRAMOVIMIENTO:
            estado_color = InterfazVisual.COLORS['warning']
        elif self.analizador_saltos.estado == EstadoSalto.DESPEGUE:
            estado_color = InterfazVisual.COLORS['info']
        elif self.analizador_saltos.estado == EstadoSalto.VUELO:
            estado_color = InterfazVisual.COLORS['accent']
        elif self.analizador_saltos.estado == EstadoSalto.ATERRIZAJE:
            estado_color = InterfazVisual.COLORS['danger']
        
        self.interfaz_visual.dibujar_contenedor_moderno(
            frame, f"Estado: {self.analizador_saltos.estado.value.replace('_', ' ')}", 
            20, 250, 180, 40, estado_color, InterfazVisual.COLORS['text_primary'], 0.6
        )
        
        # Altura del salto actual
        self.interfaz_visual.dibujar_contenedor_moderno(
            frame, f"Altura: {self.analizador_saltos.jump_height_m*100:.1f}cm", 
            20, 300, 180, 40, InterfazVisual.COLORS['accent'], 
            InterfazVisual.COLORS['text_primary']
        )
        
        # Tipo de salto
        self.interfaz_visual.dibujar_contenedor_moderno(
            frame, f"Tipo: {self.analizador_saltos.tipo_salto.name}", 
            20, 350, 180, 40, InterfazVisual.COLORS['secondary'], 
            InterfazVisual.COLORS['text_primary'], 0.6
        )
        
        # Barra de potencia/explosividad
        h, w = frame.shape[:2]
        self.interfaz_visual.dibujar_barra_potencia_moderna(
            frame, self.analizador_saltos.potencia, w - 100, 100, 50, 250
        )
        
        # Monitor técnico avanzado
        self.interfaz_visual.dibujar_monitor_tecnico_avanzado(
            frame, self.analizador_saltos.errores, w - 300, 100
        )
        
        # Panel de métricas en tiempo real
        metricas_tiempo_real = {
            "Ángulo Rodilla": f"{detalles_salto.get('angulo_rodilla', 0):.1f}°",
            "Ángulo Cadera": f"{detalles_salto.get('angulo_cadera', 0):.1f}°",
            "Velocidad": f"{detalles_salto.get('velocidad_rodilla', 0):.2f}",
            "En Aire": "Sí" if detalles_salto.get('is_in_air', False) else "No"
        }
        
        self.interfaz_visual.dibujar_panel_metricas(
            frame, metricas_tiempo_real, 20, 400, 200, 150
        )
        
        # Gráfico de altura mejorado
        self.interfaz_visual.dibujar_grafico_altura_mejorado(
            frame, self.analizador_saltos.historial_pos_y_cadera,
            self.analizador_saltos.initial_hip_y, self.analizador_saltos.px_to_m,
            self.analizador_saltos.jump_height_m, self.analizador_saltos.estado
        )
        
        # Guías visuales avanzadas
        self.interfaz_visual.dibujar_guias_visuales_avanzadas(
            frame, lm, self.analizador_saltos.estado, self.analizador_saltos
        )
        
        # Panel de ayuda (si está activado)
        if self.mostrar_ayuda:
            self.interfaz_visual.dibujar_panel_ayuda(frame)
        
        # Mostrar mensajes de feedback
        self._mostrar_mensajes_feedback(frame)

    def _mostrar_mensajes_feedback(self, frame):
        """Muestra los mensajes de feedback en pantalla"""
        h, w = frame.shape[:2]
        y_offset = h - 120
        
        # Mostrar últimos 3 mensajes
        mensajes_recientes = self.analizador_saltos.mensajes_feedback[-3:]
        
        for i, mensaje in enumerate(mensajes_recientes):
            if mensaje:
                self.interfaz_visual.dibujar_contenedor_moderno(
                    frame, mensaje, 20, y_offset + i * 35, 400, 30,
                    InterfazVisual.COLORS['background'], 
                    InterfazVisual.COLORS['text_primary'], 0.5
                )

    def manejar_teclas(self, key):
        """
        Maneja las teclas presionadas durante la ejecución
        
        Args:
            key: Código de la tecla presionada
            
        Returns:
            bool: False si se debe salir del programa
        """
        if key == ord('q') or key == 27:  # 'q' o ESC
            return False
            
        elif key == ord('r'):  # Reiniciar sesión
            print("\n🔄 Reiniciando sesión...")
            self.analizador_saltos.iniciar()
            self.calibrando = True
            self.calibracion_frames = 0
            self.sesion_activa = False
            logging.info("Sesión reiniciada por el usuario")
            
        elif key == ord('c'):  # Recalibrar
            print("\n🎯 Recalibrando sistema...")
            self.calibrando = True
            self.calibracion_frames = 0
            self.sesion_activa = False
            logging.info("Recalibración iniciada por el usuario")
            
        elif key == ord('h'):  # Mostrar/ocultar ayuda
            self.mostrar_ayuda = not self.mostrar_ayuda
            
        elif key == ord('1'):  # Cambiar a CMJ
            self.analizador_saltos.set_tipo_salto(TipoSalto.CMJ)
            print("🏃 Tipo de salto cambiado a CMJ")
            
        elif key == ord('2'):  # Cambiar a SQJ
            self.analizador_saltos.set_tipo_salto(TipoSalto.SQJ)
            print("🏃 Tipo de salto cambiado a SQJ")
            
        elif key == ord('3'):  # Cambiar a Abalakov
            self.analizador_saltos.set_tipo_salto(TipoSalto.ABALAKOV)
            print("🏃 Tipo de salto cambiado a Abalakov")
            
        elif key == ord('s'):  # Guardar sesión actual
            self._guardar_sesion_intermedia()
            
        return True

    def _guardar_sesion_intermedia(self):
        """Guarda el estado actual de la sesión"""
        try:
            resultados_parciales = self.analizador_saltos.finalizar()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"sesion_intermedia_{self.perfil_usuario.nombre.replace(' ', '_')}_{timestamp}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(resultados_parciales, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Sesión guardada: {filename}")
            logging.info(f"Sesión intermedia guardada: {filename}")
            
        except Exception as e:
            print(f"❌ Error al guardar sesión: {e}")
            logging.error(f"Error al guardar sesión intermedia: {e}")

    def finalizar_sesion(self):
        """Finaliza la sesión y genera el reporte completo"""
        print("\n📊 Finalizando sesión y generando reporte...")
        
        # Obtener resultados finales
        resultados_finales = self.analizador_saltos.finalizar()
        
        # Mostrar resumen en consola
        self._mostrar_resumen_consola(resultados_finales)
        
        # Guardar resultados
        self._guardar_resultados_finales(resultados_finales)
        
        # Mostrar resumen visual
        self._mostrar_resumen_visual(resultados_finales)

    def _mostrar_resumen_consola(self, resultados):
        """Muestra el resumen de la sesión en consola"""
        print("\n" + "="*70)
        print("   RESUMEN FINAL DE LA SESIÓN - ERGO SANITAS SpA")
        print("="*70)
        
        usuario = resultados.get('usuario', {})
        sesion = resultados.get('sesion', {})
        metricas = resultados.get('metricas', {})
        evaluacion = resultados.get('evaluacion', {})
        
        print(f"👤 ATLETA: {usuario.get('nombre', 'N/A')}")
        print(f"   Edad: {usuario.get('edad', 0)} años | Sexo: {usuario.get('sexo', 'N/A')}")
        print(f"   Peso: {usuario.get('peso_kg', 0)} kg | Altura: {usuario.get('altura_m', 0):.2f} m")
        print(f"   IMC: {usuario.get('imc', 0):.1f} | Nivel inicial: {usuario.get('nivel_inicial', 'N/A').capitalize()}")
        
        print(f"\n📈 RENDIMIENTO:")
        print(f"   Tipo de salto: {sesion.get('tipo_salto', 'N/A')}")
        print(f"   Duración: {sesion.get('duracion', 'N/A')}")
        print(f"   Total de saltos: {sesion.get('total', 0)}")
        print(f"   Saltos correctos: {sesion.get('correctas', 0)}")
        print(f"   Precisión técnica: {sesion.get('precision', 0):.1f}%")
        
        print(f"\n🎯 MÉTRICAS BIOMECÁNICAS:")
        print(f"   Altura promedio: {metricas.get('altura_salto_promedio', 0)*100:.1f} cm")
        print(f"   Altura máxima: {metricas.get('altura_salto_maxima', 0)*100:.1f} cm")
        print(f"   Potencia promedio: {metricas.get('potencia_promedio', 0):.0f} W")
        print(f"   Tiempo de vuelo promedio: {metricas.get('tiempo_vuelo_promedio', 0):.3f} s")
        
        print(f"\n🏆 EVALUACIÓN FINAL:")
        print(f"   Clasificación de rendimiento: {evaluacion.get('clasificacion_rendimiento', 'N/A')}")
        print(f"   Nivel del atleta: {evaluacion.get('nivel_usuario_final', 'N/A').upper()}")
        print(f"   Puntuación técnica: {evaluacion.get('puntuacion_tecnica', 0):.1f}/100")
        print(f"   Evaluación cualitativa: {evaluacion.get('evaluacion_cualitativa', 'N/A')}")
        
        print(f"\n❌ ERRORES DETECTADOS:")
        errores = resultados.get('errores', {})
        errores_encontrados = False
        for error, count in errores.items():
            if count > 0:
                error_nombre = error.replace('_', ' ').title()
                print(f"   • {error_nombre}: {count} veces")
                errores_encontrados = True
        
        if not errores_encontrados:
            print("   ✅ No se detectaron errores técnicos significativos")
        
        print(f"\n💡 RECOMENDACIONES PERSONALIZADAS:")
        recomendaciones = resultados.get('recomendaciones', [])
        for i, rec in enumerate(recomendaciones, 1):
            print(f"   {i}. {rec}")
        
        print("="*70)

    def _guardar_resultados_finales(self, resultados):
        """Guarda los resultados finales en archivo JSON"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"reporte_final_{self.perfil_usuario.nombre.replace(' ', '_')}_{timestamp}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(resultados, f, indent=2, ensure_ascii=False)
            
            print(f"\n💾 REPORTE GUARDADO: {filename}")
            logging.info(f"Reporte final guardado: {filename}")
            
        except Exception as e:
            print(f"❌ Error al guardar reporte: {e}")
            logging.error(f"Error al guardar reporte final: {e}")

    def _mostrar_resumen_visual(self, resultados):
        """Muestra el resumen visual final"""
        # Crear frame en blanco para el resumen
        frame_resumen = np.zeros((720, 1280, 3), dtype=np.uint8)
        
        # Dibujar resumen de sesión
        self.interfaz_visual.dibujar_resumen_sesion(frame_resumen, resultados)
        
        # Mostrar resumen
        cv2.imshow('Ergo SaniTas - Resumen Final', frame_resumen)
        
        print("\n📋 Presione cualquier tecla para cerrar el resumen visual...")
        cv2.waitKey(0)
        cv2.destroyWindow('Ergo SaniTas - Resumen Final')

    def ejecutar(self):
        """Método principal que ejecuta todo el sistema"""
        try:
            # 1. Mostrar bienvenida
            self.mostrar_bienvenida()
            
            # 2. Configurar perfil de usuario
            self.configurar_perfil_usuario()
            
            # 3. Inicializar analizador de saltos
            self.analizador_saltos = AnalizadorSaltos(self.perfil_usuario)
            self.analizador_saltos.iniciar()
            
            # 4. Inicializar cámara
            if not self.inicializar_camara():
                return
            
            # 5. Seleccionar tipo de salto
            if not self.seleccionar_tipo_salto():
                return
            
            print("\n🎥 Iniciando análisis en tiempo real...")
            print("   Controles disponibles:")
            print("   • Q: Salir")
            print("   • R: Reiniciar sesión")
            print("   • C: Recalibrar")
            print("   • H: Mostrar/ocultar ayuda")
            print("   • 1/2/3: Cambiar tipo de salto")
            print("   • S: Guardar sesión actual")
            
            # 6. Bucle principal de análisis
            while self.cap.isOpened():
                ret, frame = self.cap.read()
                if not ret:
                    print("❌ Error: No se pudo leer frame de la cámara")
                    break

                # Voltear frame horizontalmente para efecto espejo
                frame = cv2.flip(frame, 1)
                
                # Procesar con MediaPipe
                image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = self.pose.process(image_rgb)

                # Dibujar landmarks de pose
                lm = None
                if results.pose_landmarks:
                    mp.solutions.drawing_utils.draw_landmarks(
                        frame, results.pose_landmarks, self.mp_pose.POSE_CONNECTIONS,
                        mp.solutions.drawing_utils.DrawingSpec(color=(245,117,66), thickness=2, circle_radius=2),
                        mp.solutions.drawing_utils.DrawingSpec(color=(245,66,230), thickness=2, circle_radius=2)
                    )
                    lm = results.pose_landmarks.landmark

                # Procesar según estado del sistema
                if self.calibrando:
                    self.ejecutar_calibracion(frame, lm)
                elif self.sesion_activa:
                    self.procesar_frame_analisis(frame, lm)

                # Mostrar frame
                cv2.imshow('Ergo SaniTas - Análisis Biomecánico', frame)

                # Manejar teclas
                key = cv2.waitKey(1) & 0xFF
                if not self.manejar_teclas(key):
                    break

            # 7. Finalizar sesión
            if self.analizador_saltos.contador > 0:
                self.finalizar_sesion()
            else:
                print("\n⚠️ No se realizaron saltos durante la sesión")

        except KeyboardInterrupt:
            print("\n⚠️ Sesión interrumpida por el usuario")
        except Exception as e:
            print(f"\n❌ Error inesperado: {e}")
            logging.error(f"Error inesperado en ejecución principal: {e}")
        finally:
            # Limpieza
            if self.cap:
                self.cap.release()
            cv2.destroyAllWindows()
            print("\n👋 ¡Gracias por usar el Sistema Ergo SaniTas!")
            print("   Para más información: www.ergosanitas.cl")

def main():
    """Función principal del programa"""
    sistema = SistemaErgoSaniTas()
    sistema.ejecutar()

if __name__ == "__main__":
    main()
