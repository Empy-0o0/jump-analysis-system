# Sistema de Análisis Biomecánico de Saltos - Ergo SaniTas SpA

## 🏥 Medicina Deportiva - Evaluación de Rendimiento Atlético

Sistema avanzado de análisis biomecánico en tiempo real para la evaluación y clasificación automática del rendimiento atlético en saltos verticales. Desarrollado específicamente para **Ergo SaniTas SpA**, empresa chilena líder en medicina deportiva.

---

## 🎯 Características Principales

### ✅ Análisis Biomecánico Completo
- **Detección automática de pose** usando MediaPipe
- **Análisis de ángulos articulares** (rodilla, cadera, tobillo, tronco)
- **Máquina de estados** para detectar fases del salto
- **Cálculo de métricas biomecánicas** (altura, potencia, tiempo de vuelo)

### 🏃 Tipos de Salto Soportados
1. **CMJ (Counter Movement Jump)** - Salto con contramovimiento
2. **SQJ (Squat Jump)** - Salto desde posición estática
3. **Abalakov** - Salto con uso activo de brazos

### 📊 Clasificación Automática de Nivel
- **Principiante**: Técnica básica, alturas menores
- **Intermedio**: Técnica moderada, rendimiento estándar
- **Avanzado**: Técnica refinada, alto rendimiento

### 🎨 Interfaz Visual Moderna
- **Diseño corporativo** con colores de Ergo SaniTas
- **Feedback visual en tiempo real**
- **Guías biomecánicas interactivas**
- **Reportes detallados de sesión**

---

## 🚀 Instalación y Configuración

### Requisitos del Sistema
- **Python 3.8+**
- **Cámara web** (resolución mínima 720p)
- **Sistema operativo**: Windows 10+, macOS 10.14+, Ubuntu 18.04+
- **RAM**: Mínimo 4GB, recomendado 8GB
- **Espacio libre**: 2GB para instalación y datos

### Instalación

1. **Clonar el repositorio**:
```bash
git clone https://github.com/ergosanitas/jump-analysis-system.git
cd jump-analysis-system
```

2. **Crear entorno virtual**:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate     # Windows
```

3. **Instalar dependencias**:
```bash
pip install -r requirements.txt
```

4. **Verificar instalación**:
```bash
python -c "import cv2, mediapipe; print('✅ Instalación exitosa')"
```

---

## 🎮 Uso del Sistema

### Ejecución Principal
```bash
python main_ergo_sanitas.py
```

### Controles Durante la Sesión
- **Q**: Salir del sistema
- **R**: Reiniciar sesión actual
- **C**: Recalibrar sistema
- **H**: Mostrar/ocultar panel de ayuda
- **1/2/3**: Cambiar tipo de salto (CMJ/SQJ/Abalakov)
- **S**: Guardar sesión intermedia

### Flujo de Trabajo

1. **Configuración de Perfil**
   - Crear nuevo perfil o cargar existente
   - Datos antropométricos (edad, sexo, altura, peso)
   - Nivel de actividad inicial

2. **Calibración del Sistema**
   - Posicionarse frente a la cámara
   - Mantener posición estable durante calibración
   - Verificación automática de landmarks

3. **Selección de Tipo de Salto**
   - Elegir entre CMJ, SQJ o Abalakov
   - Instrucciones específicas para cada tipo

4. **Análisis en Tiempo Real**
   - Feedback visual inmediato
   - Detección automática de errores
   - Métricas biomecánicas en vivo

5. **Reporte Final**
   - Clasificación automática de nivel
   - Recomendaciones personalizadas
   - Guardado automático de resultados

---

## 📁 Estructura del Proyecto

```
ergo-sanitas-jump-analysis/
├── main_ergo_sanitas.py      # Aplicación principal
├── user_profile.py           # Gestión de perfiles de usuario
├── jump_analyzer.py          # Motor de análisis biomecánico
├── visual_interface.py       # Interfaz visual moderna
├── config_Saltos.yaml        # Configuración biomecánica
├── requirements.txt          # Dependencias del proyecto
├── README.md                 # Documentación
├── TestSalto.py             # Versión original (referencia)
└── logs/                    # Archivos de registro
    ├── session_YYYYMMDD_HHMMSS.log
    └── error_logs.log
```

---

## ⚙️ Configuración Avanzada

### Parámetros Biomecánicos (`config_Saltos.yaml`)

El sistema utiliza parámetros biomecánicos validados científicamente:

```yaml
# Rangos óptimos de movimiento (ROM)
rom_optimo_salto:
  rodilla:
    flexion_objetivo_cm: 70      # Ángulo objetivo en contramovimiento
    extension_takeoff: 170       # Extensión en despegue
    flexion_landing_max: 90      # Máxima flexión en aterrizaje
  
  cadera:
    flexion_min_cm: 100          # Flexión mínima en contramovimiento
    extension_takeoff: 170       # Extensión en despegue
  
  tobillo:
    plantarflexion_takeoff: 160  # Plantiflexión en despegue
    dorsiflexion_landing: 80     # Dorsiflexión en aterrizaje

# Niveles de usuario
nivel_usuario:
  principiante:
    tolerancia_angulo: 20        # ±20° de tolerancia
    velocidad_cm_min: 0.10       # Velocidad mínima contramovimiento
    
  intermedio:
    tolerancia_angulo: 10        # ±10° de tolerancia
    velocidad_cm_min: 0.20
    
  avanzado:
    tolerancia_angulo: 5         # ±5° de tolerancia
    velocidad_cm_min: 0.30
```

### Personalización de la Interfaz

Los colores corporativos pueden modificarse en `visual_interface.py`:

```python
COLORS = {
    'ergo_blue': (200, 100, 50),    # Azul corporativo
    'ergo_green': (100, 200, 100),  # Verde corporativo
    'primary': (50, 150, 200),      # Color primario
    # ... más colores
}
```

---

## 📊 Métricas y Evaluación

### Métricas Biomecánicas Calculadas

1. **Altura de Salto** (cm)
   - Calculada mediante análisis de trayectoria de cadera
   - Compensación por antropometría individual

2. **Potencia Mecánica** (Watts)
   - Fórmula: P = (m × g × h) / t
   - Donde: m=masa, g=gravedad, h=altura, t=tiempo

3. **Tiempo de Vuelo** (segundos)
   - Detección automática de despegue y aterrizaje
   - Basado en posición de talones

4. **Índices Especializados**
   - **Índice de Elasticidad**: (CMJ - SQJ) / SQJ × 100
   - **Índice de Coordinación**: (Abalakov - CMJ) / CMJ × 100

### Criterios de Clasificación

| Nivel | Hombres (CMJ) | Mujeres (CMJ) | Precisión Técnica |
|-------|---------------|---------------|-------------------|
| **Principiante** | < 30 cm | < 22 cm | < 60% |
| **Intermedio** | 30-40 cm | 22-30 cm | 60-80% |
| **Avanzado** | > 40 cm | > 30 cm | > 80% |

---

## 🔧 Solución de Problemas

### Problemas Comunes

**❌ Error: "No se pudo acceder a la cámara"**
```bash
# Verificar cámaras disponibles
python -c "import cv2; print([i for i in range(10) if cv2.VideoCapture(i).isOpened()])"

# Cambiar índice de cámara en main_ergo_sanitas.py
self.cap = cv2.VideoCapture(1)  # Probar diferentes índices
```

**❌ Error: "Landmark no detectado"**
- Asegurar buena iluminación
- Usar ropa contrastante
- Mantener todo el cuerpo visible
- Evitar fondos complejos

**❌ Calibración fallida**
- Verificar posición estable
- Mantener pies al ancho de hombros
- Evitar movimientos durante calibración

### Optimización de Rendimiento

```python
# Reducir resolución para mejor rendimiento
self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# Ajustar confianza de detección
self.pose = self.mp_pose.Pose(
    min_detection_confidence=0.7,  # Aumentar para mayor precisión
    min_tracking_confidence=0.5    # Reducir para mejor seguimiento
)
```

---

## 📈 Casos de Uso

### 1. Evaluación Inicial de Atletas
- **Objetivo**: Clasificar nivel de entrada
- **Protocolo**: 3 saltos CMJ + 3 saltos SQJ
- **Métricas clave**: Altura promedio, precisión técnica

### 2. Seguimiento de Progreso
- **Objetivo**: Monitorear mejoras en el tiempo
- **Protocolo**: Sesiones semanales estandarizadas
- **Métricas clave**: Tendencias de altura, reducción de errores

### 3. Análisis Técnico Detallado
- **Objetivo**: Identificar deficiencias específicas
- **Protocolo**: Análisis frame-by-frame de errores
- **Métricas clave**: Patrones de error, recomendaciones

### 4. Comparación Entre Atletas
- **Objetivo**: Benchmarking y selección
- **Protocolo**: Evaluaciones estandarizadas
- **Métricas clave**: Rankings, percentiles

---

## 🔬 Validación Científica

### Fundamentos Biomecánicos

El sistema se basa en principios biomecánicos validados:

1. **Análisis Cinemático**
   - Ángulos articulares según estándares ISB
   - Velocidades angulares calculadas por diferenciación numérica

2. **Detección de Errores**
   - Valgo de rodilla: Desviación > 4cm del eje neutro
   - Aterrizaje rígido: ROM < 90° en rodilla/cadera
   - Contramovimiento insuficiente: Flexión < 70°

3. **Métricas de Potencia**
   - Basadas en ecuaciones de mecánica clásica
   - Validadas contra plataformas de fuerza

### Referencias Científicas

- Bosco, C. et al. (1983). "A simple method for measurement of mechanical power in jumping"
- Markovic, G. et al. (2004). "Reliability and factorial validity of squat and countermovement jump tests"
- Linthorne, N.P. (2001). "Analysis of standing vertical jumps using a force platform"

---

## 🚀 Desarrollo Futuro

### Funcionalidades Planificadas

1. **Análisis Avanzado**
   - Integración con plataformas de fuerza
   - Análisis de asimetría bilateral
   - Detección de fatiga neuromuscular

2. **Interfaz Web**
   - Dashboard en tiempo real
   - Gestión de múltiples atletas
   - Reportes automáticos

3. **Inteligencia Artificial**
   - Predicción de lesiones
   - Optimización de entrenamiento
   - Análisis predictivo de rendimiento

4. **Integración Clínica**
   - Historiales médicos
   - Protocolos de rehabilitación
   - Seguimiento longitudinal

---

## 👥 Equipo de Desarrollo

**Ergo SaniTas SpA - Medicina Deportiva**
- **Dr. [Nombre]** - Director Médico
- **[Nombre]** - Ingeniero Biomecánico Senior
- **[Nombre]** - Desarrollador de Software
- **[Nombre]** - Especialista en Análisis de Movimiento

---

## 📞 Soporte y Contacto

**Ergo SaniTas SpA**
- **Web**: www.ergosanitas.cl
- **Email**: soporte@ergosanitas.cl
- **Teléfono**: +56 2 XXXX XXXX
- **Dirección**: [Dirección], Santiago, Chile

**Soporte Técnico**
- **Email**: tech@ergosanitas.cl
- **Horario**: Lunes a Viernes, 9:00 - 18:00 CLT

---

## 📄 Licencia

Copyright © 2024 Ergo SaniTas SpA. Todos los derechos reservados.

Este software es propiedad de Ergo SaniTas SpA y está protegido por las leyes de derechos de autor de Chile y tratados internacionales. El uso no autorizado está prohibido.

---

## 🔄 Historial de Versiones

### v2.0.0 (2024-01-XX)
- ✅ Arquitectura modular completa
- ✅ Interfaz visual moderna
- ✅ Clasificación automática de nivel
- ✅ Recomendaciones personalizadas
- ✅ Soporte para múltiples tipos de salto

### v1.0.0 (2023-XX-XX)
- ✅ Versión inicial de prueba de concepto
- ✅ Análisis básico de saltos CMJ
- ✅ Detección de pose con MediaPipe

---

*Desarrollado con ❤️ para la comunidad deportiva chilena*
