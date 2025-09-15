"""
CLI Interactivo Persistente para el sistema de agentes
IA Agent para Generación de Pruebas Unitarias .NET

Inspirado en Gemini CLI y Claude Code - mantiene el agente en memoria
para evitar recargas costosas de dependencias.
"""

import os
import sys
import time
import signal
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path
import threading
import asyncio

# Agregar el directorio src al path para imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import click
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.syntax import Syntax
from rich.table import Table
from rich.live import Live
from rich.spinner import Spinner
from rich.text import Text
from rich.align import Align

# Imports de agentes y herramientas
from agents.analysis_agent import analysis_agent
from agents.generation_agent import generation_agent
from agents.validation_agent import validation_agent
from agents.optimization_agent import optimization_agent
from agents.coordinator_agent import coordinator_agent
from tools.file_tools import file_manager
from tools.dotnet_tools import dotnet_manager, project_discovery, ProjectInfo, ProjectType
from utils.config import get_config
from utils.logging import get_logger, setup_logging

# Importar los nuevos módulos de verificación
from utils.version_checker import check_version_update
from utils.config_validator import ConfigValidator

logger = get_logger("interactive-cli")
console = Console()


class InteractiveCLI:
    """CLI Interactivo que mantiene el agente en memoria"""
    
    def __init__(self):
        self.console = console
        self.logger = logger
        self.is_initialized = False
        self.is_running = True
        
        # Estado de la sesión
        self.current_project_path = None
        self.current_project_info = None
        self.current_session_id = None
        
        # Inicializar validador de configuración
        self.config_validator = ConfigValidator()
        self.config_valid = False
        
        # Agentes (se inicializan después)
        self.agents = {}
        self.config = None
        
        # Comandos disponibles
        self.commands = {
            'help': self._cmd_help,
            'status': self._cmd_status,
            'discover': self._cmd_discover,
            'select': self._cmd_select,
            'analyze': self._cmd_analyze,
            'generate': self._cmd_generate,
            'validate': self._cmd_validate,
            'optimize': self._cmd_optimize,
            'run': self._cmd_run,
            'config': self._cmd_config,
            'clear': self._cmd_clear,
            'exit': self._cmd_exit,
            'quit': self._cmd_exit
        }
        
        # Configurar manejo de señales para cierre limpio
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Maneja señales de cierre del sistema"""
        self.console.print("\n[yellow]🔄 Cerrando sesión de manera segura...[/yellow]")
        self.is_running = False
        sys.exit(0)
    
    async def initialize(self):
        """Inicializa el sistema de agentes (carga inicial)"""
        if self.is_initialized:
            return
        
        self.console.print(Panel.fit(
            "[bold blue]🚀 IA Agent .NET - Inicializando Sistema[/bold blue]\n"
            "[dim]Cargando dependencias y agentes...[/dim]",
            border_style="blue"
        ))
        
        # Mostrar spinner de carga
        with Live(Spinner("dots", text="Cargando agentes..."), console=self.console, refresh_per_second=10) as live:
            try:
                # Verificar versión actualizada
                live.update(Spinner("dots", text="Verificando versión actualizada..."))
                check_version_update()
                await asyncio.sleep(0.5)
                
                # Cargar configuración
                self.config = get_config()
                live.update(Spinner("dots", text="Cargando configuración..."))
                await asyncio.sleep(0.5)
                
                # Verificar configuración de API
                live.update(Spinner("dots", text="Verificando configuración de IA..."))
                config_status = self.config_validator.check_api_configuration()
                self.config_valid = config_status["config_valid"]
                self.config_validator.show_config_status(config_status)
                await asyncio.sleep(0.5)
                
                # Inicializar agentes
                live.update(Spinner("dots", text="Inicializando agentes de análisis..."))
                self.agents = {
                    'analysis': analysis_agent,
                    'generation': generation_agent,
                    'validation': validation_agent,
                    'optimization': optimization_agent,
                    'coordinator': coordinator_agent
                }
                await asyncio.sleep(0.5)
                
                # Verificar herramientas .NET
                live.update(Spinner("dots", text="Verificando herramientas .NET..."))
                dotnet_available = await self._check_dotnet_availability()
                await asyncio.sleep(0.5)
                
                # Generar ID de sesión
                self.current_session_id = f"session_{int(time.time())}"
                
                self.is_initialized = True
                
                # Mostrar mensaje de éxito
                live.update(Text("✅ Sistema inicializado correctamente", style="green"))
                await asyncio.sleep(1)
                
            except Exception as e:
                live.update(Text(f"❌ Error durante la inicialización: {e}", style="red"))
                await asyncio.sleep(2)
                raise
    
    async def _check_dotnet_availability(self) -> bool:
        """Verifica si .NET está disponible"""
        try:
            result = await dotnet_manager.check_dotnet_installation()
            return result.get('installed', False)
        except Exception:
            return False
    
    def show_welcome(self):
        """Muestra el mensaje de bienvenida"""
        welcome_text = """[bold blue]🤖 IA Agent .NET - CLI Interactivo[/bold blue]
[dim]Sistema de generación automática de pruebas unitarias para proyectos .NET[/dim]

[bold green]Comandos disponibles:[/bold green]
[cyan]discover[/cyan] - Descubrir proyectos .NET  [cyan]select <n>[/cyan] - Seleccionar proyecto  [cyan]analyze[/cyan] - Analizar proyecto
[cyan]generate[/cyan] - Generar pruebas unitarias  [cyan]validate[/cyan] - Validar pruebas  [cyan]optimize[/cyan] - Optimizar pruebas
[cyan]run[/cyan] - Ejecutar flujo completo  [cyan]config[/cyan] - Configurar IA  [cyan]status[/cyan] - Estado actual
[cyan]help[/cyan] - Ayuda  [cyan]clear[/cyan] - Limpiar pantalla  [cyan]exit[/cyan] - Salir

[dim]Escribe un comando o 'help' para más información[/dim]"""
        
        self.console.print(Panel(welcome_text, border_style="blue", padding=(0, 1)))
    
    async def run(self):
        """Ejecuta el CLI interactivo principal"""
        try:
            # Inicializar sistema
            await self.initialize()
            
            # Mostrar bienvenida
            self.show_welcome()
            
            # Bucle principal
            while self.is_running:
                try:
                    # Obtener comando del usuario
                    command_input = Prompt.ask(
                        "\n[bold cyan]ia-agent[/bold cyan]",
                        default="help"
                    ).strip()
                    
                    if not command_input:
                        continue
                    
                    # Procesar comando
                    await self._process_command(command_input)
                    
                except KeyboardInterrupt:
                    self.console.print("\n[yellow]Usa 'exit' para salir del sistema[/yellow]")
                except Exception as e:
                    self.console.print(f"[red]❌ Error: {e}[/red]")
                    self.logger.error(f"Error en comando: {e}")
        
        except Exception as e:
            self.console.print(f"[red]❌ Error crítico: {e}[/red]")
            self.logger.error(f"Error crítico en CLI: {e}")
        finally:
            self._cleanup()
    
    async def _process_command(self, command_input: str):
        """Procesa un comando del usuario"""
        parts = command_input.split()
        command = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        
        if command in self.commands:
            try:
                await self.commands[command](args)
            except Exception as e:
                self.console.print(f"[red]❌ Error ejecutando comando '{command}': {e}[/red]")
        else:
            self.console.print(f"[yellow]⚠️  Comando desconocido: '{command}'[/yellow]")
            self.console.print("[dim]Escribe 'help' para ver comandos disponibles[/dim]")
    
    # ==================== COMANDOS ====================
    
    async def _cmd_help(self, args: List[str]):
        """Muestra ayuda detallada"""
        help_text = """
[bold blue]📚 Comandos del IA Agent .NET[/bold blue]

[bold green]🔍 Descubrimiento de Proyectos:[/bold green]
  [cyan]discover[/cyan]           - Buscar proyectos .NET en directorio actual
  [cyan]select <número>[/cyan]    - Seleccionar proyecto por número de la lista

[bold green]🧠 Análisis y Generación:[/bold green]
  [cyan]analyze[/cyan]            - Analizar proyecto seleccionado
  [cyan]generate[/cyan]           - Generar pruebas unitarias
  [cyan]validate[/cyan]           - Validar pruebas generadas
  [cyan]optimize[/cyan]           - Optimizar pruebas existentes

[bold green]🚀 Flujos Completos:[/bold green]
  [cyan]run[/cyan]                - Ejecutar flujo completo (análisis → generación → validación)

[bold green]⚙️  Configuración:[/bold green]
  [cyan]config[/cyan]             - Configurar proveedor de IA (DeepSeek, Gemini, OpenAI)
  [cyan]status[/cyan]             - Mostrar estado actual del sistema

[bold green]🛠️  Utilidades:[/bold green]
  [cyan]clear[/cyan]              - Limpiar pantalla
  [cyan]help[/cyan]               - Mostrar esta ayuda
  [cyan]exit[/cyan]               - Salir del sistema

[dim]Ejemplos:[/dim]
  [cyan]discover[/cyan]           # Buscar proyectos
  [cyan]select 1[/cyan]           # Seleccionar primer proyecto
  [cyan]run[/cyan]                # Generar pruebas completas
        """
        
        self.console.print(Panel(help_text, border_style="green", padding=(1, 2)))
    
    async def _cmd_status(self, args: List[str]):
        """Muestra el estado actual del sistema"""
        status_table = Table(title="📊 Estado del Sistema", show_header=True, header_style="bold blue")
        status_table.add_column("Componente", style="cyan")
        status_table.add_column("Estado", style="green")
        status_table.add_column("Detalles", style="dim")
        
        # Estado de inicialización
        status_table.add_row(
            "Sistema",
            "✅ Inicializado" if self.is_initialized else "❌ No inicializado",
            f"Sesión: {self.current_session_id}" if self.current_session_id else "Sin sesión"
        )
        
        # Estado de proyecto
        if self.current_project_path:
            status_table.add_row(
                "Proyecto",
                "✅ Seleccionado",
                f"Ruta: {self.current_project_path}"
            )
        else:
            status_table.add_row(
                "Proyecto",
                "⚠️  No seleccionado",
                "Usa 'discover' y 'select' para elegir un proyecto"
            )
        
        # Estado de configuración
        if self.config:
            status_table.add_row(
                "Configuración",
                "✅ Cargada",
                f"Proveedor: {getattr(self.config, 'ai_provider', 'No configurado')}"
            )
        else:
            status_table.add_row(
                "Configuración",
                "❌ No cargada",
                "Error en carga de configuración"
            )
        
        # Estado de agentes
        agents_status = "✅ Disponibles" if self.agents else "❌ No disponibles"
        agents_count = len(self.agents) if self.agents else 0
        status_table.add_row(
            "Agentes",
            agents_status,
            f"{agents_count} agentes cargados"
        )
        
        self.console.print(status_table)
    
    async def _cmd_discover(self, args: List[str]):
        """Descubre proyectos .NET en el directorio actual"""
        try:
            self.console.print("🔍 Descubriendo proyectos .NET...")
            
            # Descubrir proyectos
            projects = project_discovery.discover_projects(".")
            
            if not projects:
                self.console.print("❌ No se encontraron proyectos .NET en el directorio actual")
                self.console.print("💡 Asegúrate de estar en un directorio que contenga archivos .csproj o .sln")
                return
            
            # Mostrar proyectos encontrados
            self._display_projects(projects)
            
            # Guardar proyectos para selección
            self._available_projects = projects
            
        except Exception as e:
            self.console.print(f"❌ Error al descubrir proyectos: {e}")
    
    def _check_ai_required(self, command_name: str) -> bool:
        """Verificar si un comando requiere IA y mostrar advertencia si no está configurada"""
        if not self.config_valid:
            self.console.print(f"❌ [bold red]Comando '{command_name}' requiere configuración de IA[/bold red]")
            self.console.print("💡 Ejecuta 'config' para configurar tu API key")
            self.console.print("🔧 Comandos disponibles sin IA: discover, select, status, help, clear, exit")
            return False
        return True
    
    def _reload_config(self):
        """Recargar configuración después de cambios"""
        try:
            # Recargar configuración global
            from config.global_config import global_config_manager
            global_config_manager._load_config()
            
            # Verificar configuración de API
            config_status = self.config_validator.check_api_configuration()
            self.config_valid = config_status["config_valid"]
            
            if self.config_valid:
                self.console.print("✅ Configuración recargada correctamente", style="green")
            else:
                self.console.print("⚠️ Configuración recargada, pero aún no está completa", style="yellow")
                
        except Exception as e:
            self.console.print(f"❌ Error al recargar configuración: {e}", style="red")
    
    def _display_projects(self, projects: List[ProjectInfo]):
        """Muestra los proyectos en una tabla"""
        table = Table(title="📁 Proyectos .NET Encontrados", show_header=True, header_style="bold blue")
        table.add_column("#", style="cyan", width=3)
        table.add_column("Nombre", style="green")
        table.add_column("Tipo", style="yellow")
        table.add_column("Framework", style="magenta")
        table.add_column("Ruta", style="dim")
        
        for i, project in enumerate(projects, 1):
            table.add_row(
                str(i),
                project.name,
                project.project_type.value if project.project_type else "Desconocido",
                project.target_framework or "N/A",
                project.path
            )
        
        self.console.print(table)
        self.console.print(f"\n[dim]Usa 'select <número>' para elegir un proyecto[/dim]")
    
    async def _cmd_select(self, args: List[str]):
        """Selecciona un proyecto por número"""
        if not args:
            self.console.print("❌ Debes especificar un número de proyecto")
            self.console.print("💡 Ejemplo: select 1")
            return
        
        try:
            project_number = int(args[0])
            
            if not hasattr(self, '_available_projects') or not self._available_projects:
                self.console.print("❌ No hay proyectos disponibles. Ejecuta 'discover' primero")
                return
            
            if project_number < 1 or project_number > len(self._available_projects):
                self.console.print(f"❌ Número inválido. Debe estar entre 1 y {len(self._available_projects)}")
                return
            
            # Seleccionar proyecto
            selected_project = self._available_projects[project_number - 1]
            self.current_project_path = selected_project.path
            self.current_project_info = selected_project
            
            self.console.print(f"✅ Proyecto seleccionado: [bold green]{selected_project.name}[/bold green]")
            self.console.print(f"📁 Ruta: [dim]{selected_project.path}[/dim]")
            self.console.print(f"🎯 Framework: [cyan]{selected_project.target_framework}[/cyan]")
            
        except ValueError:
            self.console.print("❌ El número debe ser un entero válido")
        except Exception as e:
            self.console.print(f"❌ Error al seleccionar proyecto: {e}")
    
    async def _cmd_analyze(self, args: List[str]):
        """Analiza el proyecto seleccionado"""
        if not self.current_project_path:
            self.console.print("❌ No hay proyecto seleccionado")
            self.console.print("💡 Usa 'discover' y 'select' para elegir un proyecto")
            return
        
        # Verificar configuración de API
        if not self._check_ai_required("analyze"):
            return
        
        try:
            self.console.print(f"🧠 Analizando proyecto: [bold]{self.current_project_info.name}[/bold]")
            
            # Leer código del proyecto para análisis
            code_content = await self._read_project_code()
            
            # Ejecutar análisis
            with Live(Spinner("dots", text="Analizando código..."), console=self.console) as live:
                result = self.agents['analysis'].analyze_code(code_content)
                live.update(Text("✅ Análisis completado", style="green"))
            
            # Mostrar resultados
            self._display_analysis_results(result)
            
        except Exception as e:
            self.console.print(f"❌ Error durante el análisis: {e}")
    
    async def _read_project_code(self) -> str:
        """Lee el código del proyecto seleccionado"""
        try:
            code_files = []
            project_path = Path(self.current_project_path)
            
            # Buscar archivos .cs
            for cs_file in project_path.rglob("*.cs"):
                try:
                    content = cs_file.read_text(encoding='utf-8')
                    code_files.append(f"// {cs_file.name}\n{content}\n")
                except Exception as e:
                    self.logger.warning(f"No se pudo leer {cs_file}: {e}")
            
            return "\n".join(code_files) if code_files else "// No se encontraron archivos .cs"
            
        except Exception as e:
            self.logger.error(f"Error leyendo código del proyecto: {e}")
            return "// Error leyendo código del proyecto"
    
    def _display_analysis_results(self, result: Any):
        """Muestra los resultados del análisis"""
        if not result:
            self.console.print("⚠️  No se obtuvieron resultados del análisis")
            return
        
        # Si el resultado es un diccionario con métricas específicas
        if isinstance(result, dict) and any(key in result for key in ['classes_found', 'methods_found', 'complexity_score']):
            # Crear tabla de resultados
            table = Table(title="📊 Resultados del Análisis", show_header=True, header_style="bold green")
            table.add_column("Métrica", style="cyan")
            table.add_column("Valor", style="green")
            
            # Agregar métricas principales
            if 'classes_found' in result:
                table.add_row("Clases encontradas", str(result['classes_found']))
            if 'methods_found' in result:
                table.add_row("Métodos encontrados", str(result['methods_found']))
            if 'complexity_score' in result:
                table.add_row("Puntuación de complejidad", str(result['complexity_score']))
            
            self.console.print(table)
        else:
            # Si el resultado es texto del agente, extraer información y mostrar resumen
            result_text = str(result)
            
            # Extraer métricas del texto del agente
            metrics = self._extract_metrics_from_analysis(result_text)
            
            # Crear tabla de resultados
            table = Table(title="📊 Resultados del Análisis", show_header=True, header_style="bold green")
            table.add_column("Métrica", style="cyan")
            table.add_column("Valor", style="green")
            
            # Agregar métricas extraídas
            for metric, value in metrics.items():
                table.add_row(metric, value)
            
            self.console.print(table)
            
            # Mostrar resumen detallado
            self.console.print("\n📋 [bold]Resumen Detallado:[/bold]")
            self.console.print(Panel(result_text, title="Análisis Completo", border_style="blue"))
    
    def _extract_metrics_from_analysis(self, analysis_text: str) -> Dict[str, str]:
        """Extrae métricas del texto de análisis del agente"""
        import re
        metrics = {}
        
        # Contar controladores - buscar diferentes patrones
        controller_count = 0
        
        # Patrón 1: **Nombre**: `WeatherController`
        controller_matches1 = re.findall(r'\*\*Nombre\*\*: `([^`]*Controller[^`]*)`', analysis_text)
        controller_count += len(controller_matches1)
        
        # Patrón 2: **Clase:** `WeatherController`
        controller_matches2 = re.findall(r'\*\*Clase\*\*: `([^`]*Controller[^`]*)`', analysis_text)
        controller_count += len(controller_matches2)
        
        # Patrón 3: Buscar por texto "Controlador"
        if "Controlador" in analysis_text or "Controller" in analysis_text:
            controller_count = max(controller_count, 1)
        
        if controller_count > 0:
            metrics["Controladores encontrados"] = str(controller_count)
        
        # Contar modelos - buscar diferentes patrones
        model_count = 0
        
        # Patrón 1: **Nombre**: `WeatherForecast`
        model_matches1 = re.findall(r'\*\*Nombre\*\*: `([^`]+)`', analysis_text)
        model_count += len([m for m in model_matches1 if any(keyword in m for keyword in ['Model', 'Forecast', 'DTO', 'Entity'])])
        
        # Patrón 2: **Clase:** `WeatherForecast`
        model_matches2 = re.findall(r'\*\*Clase\*\*: `([^`]+)`', analysis_text)
        model_count += len([m for m in model_matches2 if any(keyword in m for keyword in ['Model', 'Forecast', 'DTO', 'Entity'])])
        
        # Patrón 3: Buscar por texto "Modelo"
        if "Modelo" in analysis_text or "Model" in analysis_text:
            model_count = max(model_count, 1)
        
        if model_count > 0:
            metrics["Modelos encontrados"] = str(model_count)
        
        # Contar servicios
        service_count = 0
        
        # Patrón 1: **Nombre**: `CalculatorService`
        service_matches1 = re.findall(r'\*\*Nombre\*\*: `([^`]*Service[^`]*)`', analysis_text)
        service_count += len(service_matches1)
        
        # Patrón 2: **Clase:** `CalculatorService`
        service_matches2 = re.findall(r'\*\*Clase\*\*: `([^`]*Service[^`]*)`', analysis_text)
        service_count += len(service_matches2)
        
        # Patrón 3: Buscar por texto "Servicio"
        if "Servicio" in analysis_text or "Service" in analysis_text:
            service_count = max(service_count, 1)
        
        if service_count > 0:
            metrics["Servicios encontrados"] = str(service_count)
        
        # Contar métodos HTTP
        http_methods = (analysis_text.count("[HttpGet") + 
                       analysis_text.count("[HttpPost") + 
                       analysis_text.count("[HttpPut") + 
                       analysis_text.count("[HttpDelete"))
        if http_methods > 0:
            metrics["Métodos HTTP encontrados"] = str(http_methods)
        
        # Contar métodos totales - buscar diferentes patrones
        method_count = 0
        
        # Patrón 1: **`Get()`**
        method_matches1 = re.findall(r'\*\*`([^`]+)`\*\*', analysis_text)
        method_count += len(method_matches1)
        
        # Patrón 2: **`Get()`** (con diferentes formatos)
        method_matches2 = re.findall(r'\*\*`([^`]*\([^`]*\)[^`]*)`\*\*', analysis_text)
        method_count += len(method_matches2)
        
        if method_count > 0:
            metrics["Métodos analizados"] = str(method_count)
        
        # Contar namespaces
        namespace_matches = re.findall(r'\*\*Namespace\*\*: `([^`]+)`', analysis_text)
        if namespace_matches:
            metrics["Namespaces encontrados"] = str(len(set(namespace_matches)))
        
        # Si no se encontraron métricas específicas, mostrar información general
        if not metrics:
            metrics["Estado"] = "Análisis completado"
            metrics["Tipo de resultado"] = "Análisis detallado de código"
            metrics["Longitud del análisis"] = f"{len(analysis_text)} caracteres"
        
        return metrics
    
    async def _cmd_generate(self, args: List[str]):
        """Genera pruebas unitarias"""
        if not self.current_project_path:
            self.console.print("❌ No hay proyecto seleccionado")
            return
        
        # Verificar configuración de API
        if not self._check_ai_required("generate"):
            return
        
        try:
            self.console.print(f"⚡ Generando pruebas para: [bold]{self.current_project_info.name}[/bold]")
            
            # Leer código del proyecto
            code_content = await self._read_project_code()
            
            # Analizar primero (necesario para la generación)
            analysis = self.agents['analysis'].analyze_code(code_content)
            
            with Live(Spinner("dots", text="Generando pruebas unitarias..."), console=self.console) as live:
                result = self.agents['generation'].generate_tests(code_content, analysis, "xunit")
                live.update(Text("✅ Pruebas generadas", style="green"))
            
            # Mostrar resultado
            if result:
                syntax = Syntax(result, "csharp", theme="monokai", line_numbers=True)
                self.console.print(Panel(syntax, title="Pruebas Generadas", border_style="green"))
            else:
                self.console.print("⚠️  No se generaron pruebas")
            
        except Exception as e:
            self.console.print(f"❌ Error durante la generación: {e}")
    
    async def _cmd_validate(self, args: List[str]):
        """Valida las pruebas generadas"""
        if not self.current_project_path:
            self.console.print("❌ No hay proyecto seleccionado")
            return
        
        # Verificar configuración de API
        if not self._check_ai_required("validate"):
            return
        
        try:
            self.console.print("🔍 Validando pruebas generadas...")
            
            # Leer código del proyecto
            code_content = await self._read_project_code()
            
            with Live(Spinner("dots", text="Validando pruebas..."), console=self.console) as live:
                result = self.agents['validation'].validate_code(code_content)
                live.update(Text("✅ Validación completada", style="green"))
            
            # Mostrar resultado
            if result:
                self.console.print(Panel(result, title="Resultado de Validación", border_style="yellow"))
            else:
                self.console.print("⚠️  No se obtuvieron resultados de validación")
            
        except Exception as e:
            self.console.print(f"❌ Error durante la validación: {e}")
    
    def _display_validation_results(self, result: Dict[str, Any]):
        """Muestra los resultados de la validación"""
        if not result:
            self.console.print("⚠️  No se obtuvieron resultados de la validación")
            return
        
        table = Table(title="✅ Resultados de Validación", show_header=True, header_style="bold green")
        table.add_column("Prueba", style="cyan")
        table.add_column("Estado", style="green")
        table.add_column("Detalles", style="dim")
        
        if 'tests_passed' in result:
            table.add_row("Pruebas ejecutadas", "✅ Exitosas", str(result['tests_passed']))
        if 'tests_failed' in result:
            table.add_row("Pruebas fallidas", "❌ Fallidas", str(result['tests_failed']))
        
        self.console.print(table)
    
    async def _cmd_optimize(self, args: List[str]):
        """Optimiza las pruebas existentes"""
        if not self.current_project_path:
            self.console.print("❌ No hay proyecto seleccionado")
            return
        
        # Verificar configuración de API
        if not self._check_ai_required("optimize"):
            return
        
        try:
            self.console.print("⚡ Optimizando pruebas...")
            
            # Leer código del proyecto
            code_content = await self._read_project_code()
            
            with Live(Spinner("dots", text="Optimizando pruebas..."), console=self.console) as live:
                result = self.agents['optimization'].optimize_code(code_content)
                live.update(Text("✅ Optimización completada", style="green"))
            
            # Mostrar resultado
            if result:
                syntax = Syntax(result, "csharp", theme="monokai", line_numbers=True)
                self.console.print(Panel(syntax, title="Código Optimizado", border_style="magenta"))
            else:
                self.console.print("⚠️  No se pudo optimizar el código")
            
        except Exception as e:
            self.console.print(f"❌ Error durante la optimización: {e}")
    
    async def _cmd_run(self, args: List[str]):
        """Ejecuta el flujo completo"""
        if not self.current_project_path:
            self.console.print("❌ No hay proyecto seleccionado")
            self.console.print("💡 Usa 'discover' y 'select' para elegir un proyecto")
            return
        
        # Verificar configuración de API
        if not self._check_ai_required("run"):
            return
        
        try:
            self.console.print(f"🚀 Ejecutando flujo completo para: [bold]{self.current_project_info.name}[/bold]")
            
            # Flujo completo: análisis → generación → validación
            steps = [
                ("🧠 Análisis", self._cmd_analyze),
                ("⚡ Generación", self._cmd_generate),
                ("🔍 Validación", self._cmd_validate)
            ]
            
            for step_name, step_func in steps:
                self.console.print(f"\n{step_name}...")
                await step_func([])
                await asyncio.sleep(1)  # Pausa entre pasos
            
            self.console.print("\n🎉 ¡Flujo completo ejecutado exitosamente!")
            
        except Exception as e:
            self.console.print(f"❌ Error durante el flujo completo: {e}")
    
    async def _cmd_config(self, args: List[str]):
        """Configura el proveedor de IA"""
        self.console.print("⚙️  [bold]Configuración de proveedor de IA[/bold]")
        self.console.print()
        
        # Mostrar estado actual
        config_status = self.config_validator.check_api_configuration()
        if config_status["config_valid"]:
            provider_name = {
                "deepseek": "DeepSeek",
                "gemini": "Google Gemini",
                "openai": "OpenAI"
            }.get(config_status["provider"], config_status["provider"])
            
            self.console.print(f"✅ [green]Configuración actual:[/green] {provider_name}")
            self.console.print()
            
            if Confirm.ask("¿Deseas reconfigurar?"):
                self._run_config_tool()
            else:
                self.console.print("Configuración mantenida.")
        else:
            self.console.print("❌ [red]No hay configuración válida[/red]")
            self.console.print()
            self.console.print("💡 [bold]Para configurar tu proveedor de IA:[/bold]")
            self.console.print("   1. Selecciona tu proveedor (DeepSeek, Gemini, OpenAI)")
            self.console.print("   2. Ingresa tu API key")
            self.console.print()
            
            if Confirm.ask("¿Deseas abrir la configuración ahora?"):
                self._run_config_tool()
    
    def _run_config_tool(self):
        """Ejecuta la herramienta de configuración"""
        try:
            import subprocess
            import sys
            
            self.console.print("🔄 Abriendo herramienta de configuración...")
            
            # Usar la ruta correcta del módulo
            result = subprocess.run([sys.executable, "-m", "src.cli.config_cli"], 
                                  capture_output=False, text=True)
            
            if result.returncode == 0:
                self.console.print("✅ Configuración completada")
                # Recargar configuración
                self._reload_config()
            else:
                self.console.print("❌ Error en la configuración")
                
        except Exception as e:
            self.console.print(f"❌ Error al ejecutar configuración: {e}")
            self.console.print("💡 Ejecuta manualmente: [cyan]ia-agent-config[/cyan]")
    
    async def _cmd_clear(self, args: List[str]):
        """Limpia la pantalla"""
        self.console.clear()
        self.show_welcome()
    
    async def _cmd_exit(self, args: List[str]):
        """Sale del sistema"""
        self.console.print("👋 ¡Hasta luego!")
        self.is_running = False
    
    def _cleanup(self):
        """Limpia recursos al salir"""
        self.console.print("[dim]Limpiando recursos...[/dim]")
        # Aquí se pueden agregar tareas de limpieza si es necesario


# Función principal asíncrona para ejecutar el CLI interactivo
async def async_main():
    """Función principal asíncrona del CLI interactivo"""
    try:
        # Configurar logging
        setup_logging("INFO")
        
        # Crear y ejecutar CLI
        cli = InteractiveCLI()
        await cli.run()
        
    except KeyboardInterrupt:
        console.print("\n[yellow]👋 Sesión interrumpida por el usuario[/yellow]")
    except Exception as e:
        console.print(f"[red]❌ Error crítico: {e}[/red]")
        logger.error(f"Error crítico en CLI interactivo: {e}")


# Función principal síncrona para el entry point
def main():
    """Función principal síncrona del CLI interactivo"""
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        print("\n¡Hasta luego!")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
