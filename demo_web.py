#!/usr/bin/env python3
"""
Demo Web del Sistema de Análisis Biomecánico - Ergo SaniTas SpA
Demostración interactiva del sistema para presentaciones y evaluaciones

Este script crea una demostración web simple del sistema usando Flask
para mostrar las capacidades del análisis biomecánico de saltos.
"""

import json
import os
from datetime import datetime
from flask import Flask, render_template, jsonify, request
import numpy as np

# Simulación de datos para la demo
class DemoData:
    """Clase para generar datos de demostración realistas"""
    
    @staticmethod
    def generar_perfil_demo():
        """Genera un perfil de usuario de demostración"""
        return {
            "nombre": "Atleta Demo",
            "sexo": "M",
            "edad": 25,
            "altura_cm": 175,
            "peso_kg": 70,
            "imc": 22.9,
            "nivel_actividad": "intermedio"
        }
    
    @staticmethod
    def generar_metricas_demo():
        """Genera métricas de salto realistas"""
        # Simular variabilidad realista en saltos
        alturas_base = [0.32, 0.35, 0.31, 0.36, 0.33, 0.34]  # metros
        ruido = np.random.normal(0, 0.02, len(alturas_base))
        alturas_saltos = [max(0.1, h + r) for h, r in zip(alturas_base, ruido)]
        
        return {
            "alturas_saltos": alturas_saltos,
            "altura_promedio": np.mean(alturas_saltos),
            "altura_maxima": max(alturas_saltos),
            "potencia_promedio": 2800 + np.random.normal(0, 200),
            "tiempo_vuelo_promedio": 0.45 + np.random.normal(0, 0.05),
            "precision_tecnica": 78 + np.random.normal(0, 5)
        }
    
    @staticmethod
    def generar_errores_demo():
        """Genera errores biomecánicos típicos"""
        return {
            "insufficient_cm_depth": np.random.randint(0, 3),
            "rodillas_valgo_takeoff": np.random.randint(0, 2),
            "stiff_landing": np.random.randint(0, 2),
            "insufficient_plantarflexion": np.random.randint(0, 1),
            "trunk_lean_takeoff_landing": np.random.randint(0, 1)
        }
    
    @staticmethod
    def generar_recomendaciones_demo():
        """Genera recomendaciones personalizadas"""
        recomendaciones_pool = [
            "Mejore la profundidad del contramovimiento con sentadillas profundas",
            "Fortalezca glúteos medios para mejor control de rodillas",
            "Practique aterrizajes suaves con mayor flexión articular",
            "Trabaje movilidad de cadera y tobillos diariamente",
            "Incorpore ejercicios pliométricos progresivos",
            "Fortalezca el core para mantener alineación del tronco"
        ]
        return np.random.choice(recomendaciones_pool, 3, replace=False).tolist()

# Configuración de Flask
app = Flask(__name__)
app.secret_key = 'ergo_sanitas_demo_2024'

@app.route('/')
def index():
    """Página principal de la demo"""
    return render_template('index.html')

@app.route('/api/perfil')
def get_perfil():
    """API endpoint para obtener perfil de usuario demo"""
    return jsonify(DemoData.generar_perfil_demo())

@app.route('/api/analisis')
def get_analisis():
    """API endpoint para obtener análisis de salto simulado"""
    metricas = DemoData.generar_metricas_demo()
    errores = DemoData.generar_errores_demo()
    recomendaciones = DemoData.generar_recomendaciones_demo()
    
    # Clasificar nivel basado en métricas
    altura_cm = metricas['altura_promedio'] * 100
    precision = metricas['precision_tecnica']
    
    if altura_cm >= 35 and precision >= 75:
        nivel = "avanzado"
        evaluacion = "EXCELENTE"
    elif altura_cm >= 25 and precision >= 60:
        nivel = "intermedio"
        evaluacion = "BUENO"
    else:
        nivel = "principiante"
        evaluacion = "EN DESARROLLO"
    
    return jsonify({
        "metricas": metricas,
        "errores": errores,
        "recomendaciones": recomendaciones,
        "clasificacion": {
            "nivel": nivel,
            "evaluacion": evaluacion,
            "puntuacion_tecnica": precision
        },
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/sesion', methods=['POST'])
def simular_sesion():
    """Simula una sesión completa de análisis"""
    tipo_salto = request.json.get('tipo_salto', 'CMJ')
    num_saltos = request.json.get('num_saltos', 5)
    
    # Generar datos de sesión
    perfil = DemoData.generar_perfil_demo()
    
    resultados_sesion = {
        "usuario": perfil,
        "sesion": {
            "tipo_salto": tipo_salto,
            "total": num_saltos,
            "correctas": max(1, num_saltos - np.random.randint(0, 2)),
            "duracion": f"0:0{np.random.randint(3, 8)}:00",
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        },
        "metricas": DemoData.generar_metricas_demo(),
        "errores": DemoData.generar_errores_demo(),
        "recomendaciones": DemoData.generar_recomendaciones_demo()
    }
    
    # Calcular precisión
    precision = (resultados_sesion["sesion"]["correctas"] / resultados_sesion["sesion"]["total"]) * 100
    resultados_sesion["sesion"]["precision"] = precision
    
    # Clasificación final
    altura_promedio = resultados_sesion["metricas"]["altura_promedio"]
    if altura_promedio > 0.35 and precision > 75:
        nivel_final = "avanzado"
    elif altura_promedio > 0.25 and precision > 60:
        nivel_final = "intermedio"
    else:
        nivel_final = "principiante"
    
    resultados_sesion["evaluacion"] = {
        "nivel_usuario_final": nivel_final,
        "puntuacion_tecnica": precision,
        "clasificacion_rendimiento": "Alto" if nivel_final == "avanzado" else "Medio" if nivel_final == "intermedio" else "Básico"
    }
    
    return jsonify(resultados_sesion)

# Crear templates HTML si no existen
def crear_templates():
    """Crea los templates HTML para la demo"""
    
    if not os.path.exists('templates'):
        os.makedirs('templates')
    
    # Template principal
    html_content = '''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ergo SaniTas SpA - Demo Sistema de Análisis Biomecánico</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            background: rgba(255, 255, 255, 0.95);
            padding: 30px;
            border-radius: 15px;
            text-align: center;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
        }
        
        .header h1 {
            color: #2c5aa0;
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .header p {
            color: #666;
            font-size: 1.2em;
        }
        
        .demo-section {
            background: rgba(255, 255, 255, 0.95);
            padding: 30px;
            border-radius: 15px;
            margin-bottom: 20px;
            box-shadow: 0 5px 20px rgba(0, 0, 0, 0.1);
        }
        
        .demo-section h2 {
            color: #2c5aa0;
            margin-bottom: 20px;
            font-size: 1.8em;
        }
        
        .button {
            background: linear-gradient(45deg, #2c5aa0, #3d6bb3);
            color: white;
            padding: 15px 30px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1.1em;
            margin: 10px;
            transition: all 0.3s ease;
        }
        
        .button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(44, 90, 160, 0.3);
        }
        
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        
        .metric-card {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            border-left: 4px solid #2c5aa0;
        }
        
        .metric-value {
            font-size: 2em;
            font-weight: bold;
            color: #2c5aa0;
        }
        
        .metric-label {
            color: #666;
            margin-top: 5px;
        }
        
        .error-list {
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 8px;
            padding: 15px;
            margin-top: 15px;
        }
        
        .recommendations {
            background: #d1ecf1;
            border: 1px solid #bee5eb;
            border-radius: 8px;
            padding: 15px;
            margin-top: 15px;
        }
        
        .loading {
            text-align: center;
            padding: 20px;
            color: #666;
        }
        
        .classification {
            background: linear-gradient(45deg, #28a745, #20c997);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            margin-top: 20px;
        }
        
        .classification h3 {
            font-size: 1.5em;
            margin-bottom: 10px;
        }
        
        .footer {
            text-align: center;
            padding: 20px;
            color: rgba(255, 255, 255, 0.8);
            margin-top: 30px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏥 Ergo SaniTas SpA</h1>
            <p>Sistema de Análisis Biomecánico de Saltos - Demostración Interactiva</p>
        </div>
        
        <div class="demo-section">
            <h2>🏃 Simulación de Análisis de Salto</h2>
            <p>Esta demostración muestra las capacidades del sistema de análisis biomecánico en tiempo real.</p>
            
            <div style="margin: 20px 0;">
                <label for="tipoSalto">Tipo de Salto:</label>
                <select id="tipoSalto" style="margin-left: 10px; padding: 8px;">
                    <option value="CMJ">CMJ (Counter Movement Jump)</option>
                    <option value="SQJ">SQJ (Squat Jump)</option>
                    <option value="ABALAKOV">Abalakov</option>
                </select>
            </div>
            
            <button class="button" onclick="simularAnalisis()">🚀 Iniciar Análisis Demo</button>
            <button class="button" onclick="generarSesionCompleta()">📊 Generar Sesión Completa</button>
        </div>
        
        <div id="resultados" class="demo-section" style="display: none;">
            <h2>📈 Resultados del Análisis</h2>
            <div id="contenidoResultados"></div>
        </div>
        
        <div class="demo-section">
            <h2>💡 Características del Sistema</h2>
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-value">3</div>
                    <div class="metric-label">Tipos de Salto Soportados</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">8</div>
                    <div class="metric-label">Errores Biomecánicos Detectados</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">Real-time</div>
                    <div class="metric-label">Análisis en Tiempo Real</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">3</div>
                    <div class="metric-label">Niveles de Clasificación</div>
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p>© 2024 Ergo SaniTas SpA - Medicina Deportiva | Desarrollado para la evaluación de rendimiento atlético</p>
        </div>
    </div>

    <script>
        async function simularAnalisis() {
            const resultadosDiv = document.getElementById('resultados');
            const contenidoDiv = document.getElementById('contenidoResultados');
            
            resultadosDiv.style.display = 'block';
            contenidoDiv.innerHTML = '<div class="loading">🔄 Analizando salto...</div>';
            
            try {
                const response = await fetch('/api/analisis');
                const data = await response.json();
                
                mostrarResultados(data);
            } catch (error) {
                contenidoDiv.innerHTML = '<div style="color: red;">Error al obtener datos de análisis</div>';
            }
        }
        
        async function generarSesionCompleta() {
            const tipoSalto = document.getElementById('tipoSalto').value;
            const resultadosDiv = document.getElementById('resultados');
            const contenidoDiv = document.getElementById('contenidoResultados');
            
            resultadosDiv.style.display = 'block';
            contenidoDiv.innerHTML = '<div class="loading">📊 Generando sesión completa...</div>';
            
            try {
                const response = await fetch('/api/sesion', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        tipo_salto: tipoSalto,
                        num_saltos: 5
                    })
                });
                
                const data = await response.json();
                mostrarSesionCompleta(data);
            } catch (error) {
                contenidoDiv.innerHTML = '<div style="color: red;">Error al generar sesión</div>';
            }
        }
        
        function mostrarResultados(data) {
            const contenidoDiv = document.getElementById('contenidoResultados');
            
            let html = `
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-value">${(data.metricas.altura_promedio * 100).toFixed(1)} cm</div>
                        <div class="metric-label">Altura de Salto</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">${data.metricas.potencia_promedio.toFixed(0)} W</div>
                        <div class="metric-label">Potencia Mecánica</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">${data.metricas.tiempo_vuelo_promedio.toFixed(3)} s</div>
                        <div class="metric-label">Tiempo de Vuelo</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">${data.metricas.precision_tecnica.toFixed(1)}%</div>
                        <div class="metric-label">Precisión Técnica</div>
                    </div>
                </div>
                
                <div class="classification">
                    <h3>🏆 Clasificación: ${data.clasificacion.nivel.toUpperCase()}</h3>
                    <p>Evaluación: ${data.clasificacion.evaluacion}</p>
                    <p>Puntuación Técnica: ${data.clasificacion.puntuacion_tecnica.toFixed(1)}/100</p>
                </div>
            `;
            
            // Mostrar errores si existen
            const erroresDetectados = Object.entries(data.errores).filter(([key, value]) => value > 0);
            if (erroresDetectados.length > 0) {
                html += '<div class="error-list"><h4>⚠️ Errores Detectados:</h4><ul>';
                erroresDetectados.forEach(([error, count]) => {
                    const errorName = error.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                    html += `<li>${errorName}: ${count} veces</li>`;
                });
                html += '</ul></div>';
            }
            
            // Mostrar recomendaciones
            html += '<div class="recommendations"><h4>💡 Recomendaciones:</h4><ul>';
            data.recomendaciones.forEach(rec => {
                html += `<li>${rec}</li>`;
            });
            html += '</ul></div>';
            
            contenidoDiv.innerHTML = html;
        }
        
        function mostrarSesionCompleta(data) {
            const contenidoDiv = document.getElementById('contenidoResultados');
            
            let html = `
                <h3>👤 Atleta: ${data.usuario.nombre}</h3>
                <p><strong>Tipo de Salto:</strong> ${data.sesion.tipo_salto} | 
                   <strong>Saltos Totales:</strong> ${data.sesion.total} | 
                   <strong>Correctos:</strong> ${data.sesion.correctas} | 
                   <strong>Precisión:</strong> ${data.sesion.precision.toFixed(1)}%</p>
                
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-value">${(data.metricas.altura_promedio * 100).toFixed(1)} cm</div>
                        <div class="metric-label">Altura Promedio</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">${(data.metricas.altura_maxima * 100).toFixed(1)} cm</div>
                        <div class="metric-label">Altura Máxima</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">${data.metricas.potencia_promedio.toFixed(0)} W</div>
                        <div class="metric-label">Potencia Promedio</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">${data.sesion.duracion}</div>
                        <div class="metric-label">Duración</div>
                    </div>
                </div>
                
                <div class="classification">
                    <h3>🎯 Nivel Final: ${data.evaluacion.nivel_usuario_final.toUpperCase()}</h3>
                    <p>Clasificación de Rendimiento: ${data.evaluacion.clasificacion_rendimiento}</p>
                    <p>Puntuación Técnica: ${data.evaluacion.puntuacion_tecnica.toFixed(1)}/100</p>
                </div>
            `;
            
            // Mostrar recomendaciones
            html += '<div class="recommendations"><h4>🎯 Plan de Mejora:</h4><ul>';
            data.recomendaciones.forEach((rec, index) => {
                html += `<li><strong>Recomendación ${index + 1}:</strong> ${rec}</li>`;
            });
            html += '</ul></div>';
            
            contenidoDiv.innerHTML = html;
        }
    </script>
</body>
</html>
    '''
    
    with open('templates/index.html', 'w', encoding='utf-8') as f:
        f.write(html_content)

if __name__ == '__main__':
    print("🚀 Iniciando Demo Web - Ergo SaniTas SpA")
    print("="*50)
    print("Sistema de Análisis Biomecánico de Saltos")
    print("Demostración Interactiva")
    print("="*50)
    
    # Crear templates si no existen
    crear_templates()
    
    print("📁 Templates creados exitosamente")
    print("🌐 Servidor iniciando en http://localhost:5000")
    print("⚠️  Presione Ctrl+C para detener el servidor")
    
    # Ejecutar aplicación Flask
    app.run(debug=True, host='0.0.0.0', port=5000)
