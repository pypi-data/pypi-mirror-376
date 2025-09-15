# 📝 Changelog - IA Agent para Generación de Pruebas Unitarias .NET

Todos los cambios notables de este proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Interfaz web para gestión de proyectos
- Integración con CI/CD pipelines
- Soporte para más frameworks de pruebas (.NET Core, .NET Framework)
- Análisis de código más avanzado con IA

## [0.9.0] - 2025-09-14

### Added
- **🧠 CLI Interactivo Persistente** - Sistema de CLI que mantiene los agentes cargados en memoria para mayor velocidad
- **⚙️ Configuración Global de IA** - Sistema de configuración centralizada para proveedores de IA (DeepSeek, Gemini, OpenAI)
- **🔧 Validación de Configuración** - Verificación automática de API keys y configuración de IA
- **📊 Análisis en Memoria** - Análisis de código directo desde memoria sin archivos físicos
- **🎯 Generación de Pruebas Mejorada** - Sistema de generación que reemplaza pruebas existentes y calcula cobertura real
- **📚 Documentación Técnica Automática** - Generación automática de documentación técnica con diagramas Mermaid
- **🔄 Sistema de Fallback** - Análisis básico cuando el LLM falla o no responde
- **⚡ Optimización de Rendimiento** - Limitación de métodos procesados para evitar timeouts

### Changed
- **🏗️ Arquitectura Refactorizada** - Migración a sistema multi-agente con memoria compartida
- **🔌 Integración LLM Factory** - Sistema dinámico para crear instancias LLM según configuración
- **📁 Gestión de Memoria** - ChromaDB singleton para evitar conflictos de instancias
- **🎨 Interfaz de Usuario** - Menú optimizado con menor espaciado para mejor aprovechamiento de pantalla

### Fixed
- **🐛 Errores de Inicialización** - Corrección de problemas de carga de agentes y configuración
- **🔧 Problemas de Cobertura** - Cálculo correcto de cobertura sin superar 100%
- **📝 Generación de Código** - Pruebas generadas en formato C# puro (no Markdown)
- **🔍 Análisis de Proyectos** - Filtrado correcto de proyectos de prueba en descubrimiento
- **💾 Persistencia de Configuración** - Recarga automática de configuración después de cambios

### Technical
- **🔧 Dependencias Actualizadas** - Integración de `langchain-google-genai` para Gemini 2.5
- **📦 Estructura de Paquete** - Optimización para distribución PyPI
- **🧹 Limpieza de Código** - Eliminación de archivos temporales y caché innecesarios
- **📋 Documentación** - Actualización de README y guías de usuario

## [0.7.0] - 2025-09-14

### Added
- **🔍 Descubrimiento automático de proyectos .NET** - El agente detecta automáticamente todos los proyectos .NET en el directorio actual
- **🎯 Selección interactiva de proyectos** - Interfaz amigable para seleccionar entre múltiples proyectos encontrados
- **📊 Análisis detallado de proyectos** - Información completa sobre tipo, framework, paquetes y archivos fuente
- **🌐 Soporte para archivos .sln** - Análisis de soluciones de Visual Studio
- **📋 Tabla visual de proyectos** - Presentación clara de proyectos encontrados con emojis y colores

### Changed
- **Comando `ia-agent` mejorado** - Ya no requiere especificar `--project-path`, descubre automáticamente
- **Flujo de trabajo simplificado** - Un solo comando para descubrir, seleccionar y analizar
- **Interfaz más intuitiva** - Selección numérica simple y clara
- **Documentación actualizada** - Guías actualizadas para reflejar el nuevo flujo

### Fixed
- Mejoras en la detección de tipos de proyecto
- Corrección de problemas de codificación en archivos .csproj
- Optimización del análisis de archivos de solución

### Technical
- Nueva clase `DotNetProjectDiscovery` para descubrimiento de proyectos
- Métodos `discover_and_select_project()` y `_display_projects()` en CLI
- Soporte mejorado para múltiples tipos de proyecto (.csproj y .sln)

## [0.5.2] - 2025-09-14

### Changed
- **DeepSeek como proveedor por defecto** - Cambio de OpenAI a DeepSeek
- **Configuración optimizada** para generación de código
- **Modelo por defecto**: `deepseek-coder` (especializado en programación)
- **Parámetros optimizados**: temperature=0.1, max_tokens=4000

### Updated
- **Documentación actualizada** para reflejar DeepSeek como predeterminado
- **Guías de configuración** actualizadas
- **README** con instrucciones de DeepSeek
- **Troubleshooting** con DeepSeek como solución principal

### Benefits
- **Más económico** que OpenAI GPT-4
- **Especializado en programación** para mejor generación de código
- **Respuestas más rápidas** y eficientes
- **API compatible** con OpenAI para fácil migración

## [0.4.0] - 2025-09-14

### Added
- **Sistema de configuración robusto** con `EnvironmentConfig` y Pydantic
- **Manager de memoria optimizado** con cache LRU y gestión inteligente
- **Optimizador de rendimiento** con monitoreo automático de recursos
- **Manejador de errores avanzado** con categorización y callbacks
- **Configuración Docker completa** con Dockerfile y docker-compose.yml
- **Scripts de despliegue automatizado** para dev/staging/production
- **Validador de producción** con verificación automática del sistema
- **Documentación completa** de usuario, desarrollador y despliegue
- **Guía de solución de problemas** detallada
- **API Reference** completa con ejemplos

### Changed
- **Arquitectura optimizada** para mejor rendimiento y escalabilidad
- **Sistema de logging mejorado** con niveles configurables
- **Gestión de memoria más eficiente** con cache inteligente
- **Manejo de errores más robusto** con recuperación automática
- **Configuración más flexible** con variables de entorno

### Fixed
- **Problemas de ChromaDB** con singleton pattern mejorado
- **Errores de importación** con dependencias actualizadas
- **Problemas de memoria** con gestión optimizada
- **Timeouts de agentes** con configuración mejorada

### Security
- **Validación de archivos** mejorada
- **Gestión segura de API keys** con variables de entorno
- **Permisos de archivos** configurados correctamente

## [0.3.0] - 2025-09-14

### Added
- **CLI simplificado** con interfaz Rich y comandos básicos
- **Corrección del DotNetManager** con método `get_dotnet_version`
- **Validación del sistema** end-to-end
- **Integración .NET verificada** con versión 8.0.317

### Changed
- **CLI más estable** sin bucles infinitos
- **Mejor manejo de errores** en herramientas .NET
- **Interfaz más intuitiva** con comandos claros

### Fixed
- **Bucle infinito en CLI** resuelto
- **Errores de importación** corregidos
- **Problemas de configuración** solucionados

## [0.2.0] - 2025-09-14

### Added
- **Fase 3 completada** con funcionalidades avanzadas
- **Suite de testing completa** con cobertura integral
- **Mejoras de IA** implementadas
- **Documentación de API** creada
- **Sistema de monitoreo** implementado

### Changed
- **Arquitectura mejorada** con componentes optimizados
- **Rendimiento mejorado** con optimizaciones
- **Estabilidad aumentada** con mejor manejo de errores

### Fixed
- **Problemas de memoria** resueltos
- **Errores de configuración** corregidos
- **Problemas de importación** solucionados

## [0.1.0] - 2025-09-14

### Added
- **Sistema base** con arquitectura multi-agente
- **Agentes especializados** (Analysis, Generation, Validation, Optimization, Coordinator)
- **Herramientas básicas** (File Manager, .NET Tools)
- **Sistema de memoria** con ChromaDB
- **CLI básico** con comandos esenciales
- **Configuración inicial** del proyecto
- **Tests básicos** del sistema

### Features
- **Análisis de código .NET** automatizado
- **Generación de pruebas unitarias** con múltiples frameworks
- **Validación de código** y pruebas
- **Optimización automática** de código
- **Coordinación de tareas** entre agentes
- **Memoria persistente** con búsqueda semántica
- **Interfaz de línea de comandos** intuitiva

## [0.0.1] - 2025-09-14

### Added
- **Proyecto inicial** creado
- **Estructura base** del repositorio
- **Configuración inicial** de dependencias
- **README básico** del proyecto

---

## 🔄 Tipos de Cambios

- **Added** para nuevas funcionalidades
- **Changed** para cambios en funcionalidades existentes
- **Deprecated** para funcionalidades que serán eliminadas
- **Removed** para funcionalidades eliminadas
- **Fixed** para corrección de bugs
- **Security** para vulnerabilidades corregidas

## 📊 Estadísticas de Versiones

### v0.4.0 (Actual)
- **Archivos**: 73 archivos
- **Tamaño**: 0.62 MB
- **Líneas de código**: ~15,000
- **Funcionalidades**: 25+ características principales
- **Tests**: 100% de componentes cubiertos
- **Documentación**: 5 guías completas

### v0.3.0
- **Archivos**: 85+ archivos
- **Funcionalidades**: CLI funcional
- **Tests**: Validación básica
- **Documentación**: API básica

### v0.2.0
- **Funcionalidades**: Testing avanzado
- **Mejoras**: Optimizaciones de rendimiento
- **Documentación**: Guías de uso

### v0.1.0
- **Funcionalidades**: Sistema base completo
- **Agentes**: 5 agentes especializados
- **Herramientas**: File y .NET tools
- **Memoria**: Sistema de memoria vectorial

## 🎯 Roadmap

### v0.5.0 (Próxima)
- [ ] Interfaz web completa
- [ ] Integración con CI/CD
- [ ] Soporte para más frameworks
- [ ] Análisis de código avanzado

### v0.6.0 (Futuro)
- [ ] Machine Learning integrado
- [ ] Análisis de patrones de código
- [ ] Generación de documentación automática
- [ ] Integración con IDEs

### v1.0.0 (Lanzamiento)
- [ ] API REST completa
- [ ] Dashboard web
- [ ] Soporte multi-idioma
- [ ] Enterprise features

## 📞 Soporte

Para reportar bugs o solicitar funcionalidades:

- **Issues**: [GitHub Issues](https://github.com/tu-usuario/ia-agent-to-unit-tes-api-rest/issues)
- **Email**: [tu-email@ejemplo.com]
- **Documentación**: [docs/](docs/)

---

*Última actualización: Septiembre 2025*
