import json
from pathlib import Path

with open("app/notebooks_data.json") as f:
    notebooks_data = json.load(f)

json_data_str = json.dumps(notebooks_data, ensure_ascii=False)

html_template = """<!DOCTYPE html>
<html lang="es" class="dark">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NIDS Multidominio & IoMT — Centro de Operaciones e Investigación</title>

    <!-- Tailwind CSS CDN con configuración personalizada -->
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            darkMode: 'class',
            theme: {
                extend: {
                    colors: {
                        slate: {
                            850: '#151f32',
                            950: '#070d17',
                        },
                        cyan: {
                            450: '#00c5e0',
                        }
                    },
                    fontFamily: {
                        sans: ['Inter', 'ui-sans-serif', 'system-ui', '-apple-system', 'sans-serif'],
                        mono: ['JetBrains Mono', 'Fira Code', 'monospace']
                    }
                }
            }
        }
    </script>

    <!-- Google Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">

    <!-- Chart.js -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <!-- Lucide Icons -->
    <script src="https://unpkg.com/lucide@latest"></script>

    <style>
        body {
            font-family: 'Inter', sans-serif;
            background-color: #060b13;
        }

        .font-mono {
            font-family: 'JetBrains Mono', monospace;
        }

        @keyframes pulse-attack-red {
            0%, 100% {
                background-color: rgba(239, 68, 68, 0.15);
                border-color: rgba(239, 68, 68, 0.8);
                box-shadow: 0 0 15px rgba(239, 68, 68, 0.3);
            }
            50% {
                background-color: rgba(239, 68, 68, 0.35);
                border-color: rgba(239, 68, 68, 1);
                box-shadow: 0 0 25px rgba(239, 68, 68, 0.5);
            }
        }

        @keyframes pulse-attack-amber {
            0%, 100% {
                background-color: rgba(245, 158, 11, 0.15);
                border-color: rgba(245, 158, 11, 0.8);
                box-shadow: 0 0 15px rgba(245, 158, 11, 0.3);
            }
            50% {
                background-color: rgba(245, 158, 11, 0.35);
                border-color: rgba(245, 158, 11, 1);
                box-shadow: 0 0 25px rgba(245, 158, 11, 0.5);
            }
        }

        .alert-syn {
            animation: pulse-attack-amber 1.4s infinite;
        }

        .alert-udp {
            animation: pulse-attack-red 1.2s infinite;
        }

        .log-scroll::-webkit-scrollbar {
            width: 6px;
            height: 6px;
        }

        .log-scroll::-webkit-scrollbar-track {
            background: #090e17;
        }

        .log-scroll::-webkit-scrollbar-thumb {
            background-color: #1e293b;
            border-radius: 4px;
        }

        .tab-btn.active {
            color: #38bdf8;
            border-bottom: 2px solid #38bdf8;
            background-color: rgba(56, 189, 248, 0.08);
        }

        .glass-card {
            background: rgba(15, 23, 42, 0.75);
            backdrop-filter: blur(8px);
            border: 1px solid rgba(51, 65, 85, 0.5);
        }

        .glass-card:hover {
            border-color: rgba(100, 116, 139, 0.6);
        }
    </style>
</head>

<body class="text-slate-100 min-h-screen flex flex-col selection:bg-cyan-500 selection:text-white">

    <!-- Top Header -->
    <header class="bg-slate-900/90 border-b border-slate-800 px-6 py-3.5 sticky top-0 z-40 backdrop-blur-md flex flex-wrap justify-between items-center gap-4 shadow-xl">
        <div class="flex items-center space-x-3.5">
            <div class="p-2.5 bg-gradient-to-br from-cyan-500/20 to-blue-600/20 text-cyan-400 rounded-xl border border-cyan-500/40 shadow-inner">
                <i data-lucide="shield-alert" class="w-6 h-6"></i>
            </div>
            <div>
                <div class="flex items-center gap-2">
                    <h1 class="text-lg font-bold tracking-tight text-white flex items-center gap-2">
                        NIDS Multidominio & IoMT <span class="text-xs px-2 py-0.5 rounded bg-cyan-950 text-cyan-400 border border-cyan-800/60 font-mono">CRISP-DM</span>
                    </h1>
                </div>
                <p class="text-xs text-slate-400">Plataforma Analítica basada en los Hallazgos de Notebooks 01–04 | CICIoMT2024 & CIC-DDoS2019</p>
            </div>
        </div>

        <!-- Indicadores Superiores y Quick Actions -->
        <div class="flex items-center gap-3">
            <div id="sound-toggle-btn" class="cursor-pointer px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs border border-slate-700 flex items-center gap-1.5 transition" title="Activar/Desactivar alarma sonora">
                <i data-lucide="volume-2" id="sound-icon" class="w-3.5 h-3.5 text-slate-400"></i>
                <span id="sound-label" class="hidden sm:inline">Sonido Alerta</span>
            </div>

            <div id="status-badge" class="flex items-center space-x-2 px-4 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-semibold tracking-wide transition-all duration-300 shadow-sm">
                <span class="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-ping"></span>
                <span id="status-text">TRÁFICO BENIGNO SALUDABLE</span>
            </div>
        </div>
    </header>

    <!-- Barra de Navegación de Pestañas -->
    <nav class="bg-slate-900 border-b border-slate-800 px-6 overflow-x-auto flex gap-1">
        <button onclick="switchTab('monitor')" id="tab-btn-monitor" class="tab-btn active px-4 py-3 text-xs sm:text-sm font-medium text-slate-400 hover:text-slate-200 flex items-center gap-2 transition whitespace-nowrap">
            <i data-lucide="activity" class="w-4 h-4 text-cyan-400"></i> Monitor SOC & Inferencia en Vivo
        </button>
        <button onclick="switchTab('benchmarks')" id="tab-btn-benchmarks" class="tab-btn px-4 py-3 text-xs sm:text-sm font-medium text-slate-400 hover:text-slate-200 flex items-center gap-2 transition whitespace-nowrap">
            <i data-lucide="bar-chart-3" class="w-4 h-4 text-emerald-400"></i> Benchmarks & Modelos (NB 03 y 04)
        </button>
        <button onclick="switchTab('generalizacion')" id="tab-btn-generalizacion" class="tab-btn px-4 py-3 text-xs sm:text-sm font-medium text-slate-400 hover:text-slate-200 flex items-center gap-2 transition whitespace-nowrap">
            <i data-lucide="git-branch" class="w-4 h-4 text-purple-400"></i> Generalización Cruzada & Ablación
        </button>
        <button onclick="switchTab('explicabilidad')" id="tab-btn-explicabilidad" class="tab-btn px-4 py-3 text-xs sm:text-sm font-medium text-slate-400 hover:text-slate-200 flex items-center gap-2 transition whitespace-nowrap">
            <i data-lucide="cpu" class="w-4 h-4 text-amber-400"></i> Explicabilidad & Estabilidad (KS/PSI)
        </button>
        <button onclick="switchTab('figuras')" id="tab-btn-figuras" class="tab-btn px-4 py-3 text-xs sm:text-sm font-medium text-slate-400 hover:text-slate-200 flex items-center gap-2 transition whitespace-nowrap">
            <i data-lucide="layers" class="w-4 h-4 text-pink-400"></i> Galería de Figuras Oficiales
        </button>
    </nav>

    <!-- Contenido Principal Dinámico -->
    <main class="flex-1 p-4 sm:p-6 max-w-7xl w-full mx-auto">

        <!-- =================================================================== -->
        <!-- PESTAÑA 1: MONITOR SOC & INFERENCIA EN VIVO -->
        <!-- =================================================================== -->
        <div id="view-monitor" class="space-y-6">

            <!-- Banner Explicativo de Contexto -->
            <div class="bg-gradient-to-r from-slate-900 via-slate-850 to-slate-900 border border-slate-800 rounded-xl p-4 shadow-md flex flex-col md:flex-row justify-between items-start md:items-center gap-3">
                <div class="flex items-center gap-3">
                    <div class="p-2 bg-cyan-500/10 text-cyan-400 rounded-lg border border-cyan-500/20">
                        <i data-lucide="info" class="w-5 h-5"></i>
                    </div>
                    <div>
                        <h2 class="text-xs sm:text-sm font-semibold text-slate-200">Demostrador en Tiempo Real Calibrado con Datos Reales de CICIoMT2024</h2>
                        <p class="text-[11px] sm:text-xs text-slate-400">
                            Las características mostradas (<span class="font-mono text-cyan-300">Tot size, Rate, syn_flag, Variance</span>) corresponden a las variables de mayor poder predictivo identificadas en el Notebook 02 y evaluadas en los Notebooks 03 y 04.
                        </p>
                    </div>
                </div>

                <div class="flex flex-wrap items-center gap-2 w-full md:w-auto">
                    <!-- Selector de Escenario de Evaluación -->
                    <div class="flex-1 md:flex-none">
                        <label class="block text-[10px] text-slate-400 uppercase font-semibold mb-0.5">Escenario Experimental Activo:</label>
                        <select id="scenario-select" class="w-full md:w-72 bg-slate-800 border border-slate-700 text-slate-200 rounded-lg px-2.5 py-1.5 text-xs focus:ring-1 focus:ring-cyan-500 focus:outline-none">
                            <option value="optimal_iomt" selected>1. Ensamble Óptimo (LightGBM/XGBoost - IoMT)</option>
                            <option value="bias_v1">2. Sesgo de Variantes V1 (Entrenado sin UDP)</option>
                            <option value="cross_trad_iomt">3. Despliegue Cruzado (Tradicional → IoMT)</option>
                            <option value="cross_ablated">4. Homologación Corregida (Ablación +34B)</option>
                            <option value="decision_tree">5. Árbol de Decisión Base (Profundidad = 4)</option>
                        </select>
                    </div>
                </div>
            </div>

            <!-- Grilla Principal del Monitor -->
            <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">

                <!-- Columna Izquierda: Panel de Control del Flujo y Telemetría Extraída (5 cols) -->
                <div class="lg:col-span-5 space-y-6">

                    <!-- Tarjeta: Panel de Forzado de Ataques y Simulación Estocástica -->
                    <div class="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg space-y-4">
                        <div class="flex justify-between items-center">
                            <h3 class="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-2">
                                <i data-lucide="crosshair" class="w-4 h-4 text-red-400"></i> Control de Ataques & Generador
                            </h3>
                            <span id="forced-status-pill" class="text-[10px] px-2.5 py-0.5 rounded-full border bg-emerald-500/10 text-emerald-400 border-emerald-500/30 font-mono font-semibold flex items-center gap-1.5">
                                <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span> Aleatorio Activo
                            </span>
                        </div>

                        <!-- Sección Destacada: Forzar Ataques -->
                        <div class="bg-slate-950/80 p-3.5 rounded-xl border border-red-500/20 space-y-2.5">
                            <div class="flex items-center justify-between">
                                <span class="text-[11px] font-bold text-slate-200 uppercase tracking-wider flex items-center gap-1.5">
                                    <i data-lucide="zap" class="w-3.5 h-3.5 text-amber-400"></i> Forzar Ataques Inmediatos:
                                </span>
                                <span class="text-[10px] text-slate-400 font-mono">Intervención Manual</span>
                            </div>

                            <div class="grid grid-cols-2 gap-2">
                                <button onclick="triggerForcedAttack('DDOS_SYN')" id="btn-force-syn" class="px-3 py-2 bg-gradient-to-r from-amber-950/80 to-slate-850 hover:from-amber-900 hover:to-slate-800 border border-amber-600/50 hover:border-amber-400 rounded-lg text-left transition shadow group">
                                    <div class="flex items-center justify-between">
                                        <span class="text-xs font-bold text-amber-400 group-hover:text-amber-300 flex items-center gap-1">
                                            <i data-lucide="flame" class="w-3 h-3 text-amber-400"></i> SYN Flood
                                        </span>
                                        <span class="text-[9px] bg-amber-950 text-amber-300 px-1 py-0.5 rounded font-mono">54B</span>
                                    </div>
                                    <p class="text-[10px] text-slate-400 mt-0.5 leading-tight">Rate ~11.3 pkts/s, SYN=1</p>
                                </button>

                                <button onclick="triggerForcedAttack('DDOS_UDP')" id="btn-force-udp" class="px-3 py-2 bg-gradient-to-r from-red-950/80 to-slate-850 hover:from-red-900 hover:to-slate-800 border border-red-600/50 hover:border-red-400 rounded-lg text-left transition shadow group">
                                    <div class="flex items-center justify-between">
                                        <span class="text-xs font-bold text-red-400 group-hover:text-red-300 flex items-center gap-1">
                                            <i data-lucide="bomb" class="w-3 h-3 text-red-400"></i> UDP Flood
                                        </span>
                                        <span class="text-[9px] bg-red-950 text-red-300 px-1 py-0.5 rounded font-mono">50B</span>
                                    </div>
                                    <p class="text-[10px] text-slate-400 mt-0.5 leading-tight">Saturación >20k pkts/s</p>
                                </button>
                            </div>

                            <div class="grid grid-cols-2 gap-2 pt-0.5">
                                <button onclick="triggerForcedAttack('MIXED')" id="btn-force-mixed" class="px-2.5 py-1.5 bg-slate-850 hover:bg-slate-800 border border-purple-500/40 hover:border-purple-400 rounded-lg text-left transition group">
                                    <div class="flex items-center justify-between">
                                        <span class="text-[11px] font-bold text-purple-300 group-hover:text-purple-200 flex items-center gap-1">
                                            <i data-lucide="shuffle" class="w-3 h-3"></i> Multivector
                                        </span>
                                        <span class="text-[9px] bg-purple-950 text-purple-300 px-1 rounded font-mono">SYN+UDP</span>
                                    </div>
                                </button>

                                <button onclick="resetToRandomStochastic()" class="px-2.5 py-1.5 bg-slate-850 hover:bg-slate-800 border border-slate-700 hover:border-cyan-500/50 rounded-lg text-left transition group">
                                    <div class="flex items-center justify-between">
                                        <span class="text-[11px] font-semibold text-cyan-400 group-hover:text-cyan-300 flex items-center gap-1">
                                            <i data-lucide="refresh-cw" class="w-3 h-3"></i> Restaurar
                                        </span>
                                        <span class="text-[9px] bg-cyan-950 text-cyan-300 px-1 rounded font-mono">Auto</span>
                                    </div>
                                </button>
                            </div>

                            <!-- Configuración del Ataque Forzado -->
                            <div class="pt-2 border-t border-slate-800/80 flex items-center justify-between text-xs">
                                <span class="text-[11px] text-slate-400 flex items-center gap-1">
                                    <i data-lucide="timer" class="w-3 h-3 text-cyan-400"></i> Duración del forzado:
                                </span>
                                <select id="forced-duration-select" class="bg-slate-850 border border-slate-700 text-slate-200 rounded px-2 py-0.5 text-[11px] focus:outline-none">
                                    <option value="5">5 ticks (~5 seg)</option>
                                    <option value="10" selected>10 ticks (~10 seg)</option>
                                    <option value="25">25 ticks (~25 seg)</option>
                                    <option value="-1">Permanente (Bloqueo)</option>
                                </select>
                            </div>
                        </div>

                        <!-- Presets de Tráfico Base e Inyección Puntual -->
                        <div>
                            <span class="block text-[11px] font-semibold text-slate-300 mb-1.5 flex items-center gap-1">
                                <i data-lucide="layers" class="w-3 h-3 text-emerald-400"></i> Inyectar Casos Reales (NB 01 y 03):
                            </span>
                            <div class="grid grid-cols-2 gap-2">
                                <button onclick="injectPreset('benign')" class="px-2.5 py-1.5 bg-slate-800 hover:bg-slate-750 border border-slate-700/80 hover:border-emerald-500/50 rounded-lg text-left transition">
                                    <span class="text-xs font-semibold text-emerald-400 block">Benigno IoMT</span>
                                    <span class="text-[10px] text-slate-400 block">Sensor ECG, 80.8B @ 1.65 pkts/s</span>
                                </button>
                                <button onclick="injectPreset('enterprise')" class="px-2.5 py-1.5 bg-slate-800 hover:bg-slate-750 border border-slate-700/80 hover:border-purple-500/50 rounded-lg text-left transition">
                                    <span class="text-xs font-semibold text-purple-400 block">Red Tradicional</span>
                                    <span class="text-[10px] text-slate-400 block">CICFlowMeter sin cabecera</span>
                                </button>
                            </div>
                        </div>

                        <!-- Configuración de la Simulación Estocástica y Velocidad -->
                        <div class="border-t border-slate-800 pt-3 space-y-2">
                            <div class="flex items-center justify-between text-xs">
                                <span class="text-slate-400 flex items-center gap-1">
                                    <i data-lucide="sparkles" class="w-3 h-3 text-emerald-400"></i> Ataques espontáneos (Auto):
                                </span>
                                <select id="auto-attack-freq-select" onchange="updateSpontaneousRate()" class="bg-slate-800 border border-slate-700 text-slate-300 rounded px-2 py-0.5 text-[11px] focus:outline-none">
                                    <option value="0.20">Baja (20% ataques aleatorios)</option>
                                    <option value="0.45" selected>Estándar NB (45% ataques)</option>
                                    <option value="0.75">Alta (75% ataques aleatorios)</option>
                                    <option value="0.00">0% (Solo benigno en auto)</option>
                                </select>
                            </div>

                            <div class="flex items-center justify-between gap-3 pt-1">
                                <button id="toggle-sim-btn" class="px-3 py-1 bg-cyan-600 hover:bg-cyan-500 text-white rounded-md text-xs font-medium transition flex items-center gap-1.5 shadow">
                                    <i data-lucide="play" id="play-icon" class="w-3 h-3"></i> <span id="sim-btn-label">Pausar</span>
                                </button>

                                <div class="flex-1">
                                    <div class="flex justify-between items-center text-[10px] text-slate-400 mb-0.5">
                                        <span>Cadencia:</span>
                                        <span id="speed-label" class="font-mono text-cyan-400 font-bold">1.0s</span>
                                    </div>
                                    <input id="speed-range" type="range" min="300" max="2500" step="100" value="1000" class="w-full accent-cyan-500 bg-slate-800 rounded-lg h-1.5 cursor-pointer">
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Tarjeta: Vector de Características Extraído (34 variables seleccionadas en NB 02) -->
                    <div class="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg">
                        <div class="flex justify-between items-center mb-3">
                            <h3 class="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-2">
                                <i data-lucide="cpu" class="w-4 h-4 text-cyan-400"></i> Vector de Características del Flujo
                            </h3>
                            <span class="text-[10px] bg-slate-800 text-slate-400 px-2 py-0.5 rounded border border-slate-700">Top Predictoras NB 02</span>
                        </div>

                        <div class="grid grid-cols-2 gap-2.5 mb-4">
                            <!-- Tot size (49.6% importancia en árbol) -->
                            <div class="bg-slate-800/60 p-3 rounded-lg border border-slate-700/50 hover:border-cyan-500/40 transition">
                                <div class="flex justify-between items-start">
                                    <span class="text-[11px] text-slate-400">Tot size (Frame)</span>
                                    <span class="text-[9px] text-cyan-400 font-mono">49.6% árbol</span>
                                </div>
                                <div class="flex items-baseline gap-1 mt-1">
                                    <span id="feat-tot-size" class="text-xl font-bold font-mono text-white">80.8</span>
                                    <span class="text-[10px] text-slate-500">bytes</span>
                                </div>
                                <span class="text-[10px] text-slate-400 block mt-0.5" id="size-hint">Mediana benigno: 80.8B</span>
                            </div>

                            <!-- syn_flag_number (48.96% importancia) -->
                            <div class="bg-slate-800/60 p-3 rounded-lg border border-slate-700/50 hover:border-cyan-500/40 transition">
                                <div class="flex justify-between items-start">
                                    <span class="text-[11px] text-slate-400">syn_flag_number</span>
                                    <span class="text-[9px] text-amber-400 font-mono">48.9% árbol</span>
                                </div>
                                <div class="flex items-baseline gap-1 mt-1">
                                    <span id="feat-syn" class="text-xl font-bold font-mono text-white">0.0</span>
                                    <span class="text-[10px] text-slate-500">0 / 1</span>
                                </div>
                                <span class="text-[10px] text-slate-400 block mt-0.5" id="syn-hint">Flag SYN activo</span>
                            </div>

                            <!-- Rate (Tasa de paquetes) -->
                            <div class="bg-slate-800/60 p-3 rounded-lg border border-slate-700/50 hover:border-cyan-500/40 transition">
                                <div class="flex justify-between items-start">
                                    <span class="text-[11px] text-slate-400">Rate (Frecuencia)</span>
                                    <span class="text-[9px] text-cyan-400 font-mono">Permutación #2</span>
                                </div>
                                <div class="flex items-baseline gap-1 mt-1">
                                    <span id="feat-rate" class="text-xl font-bold font-mono text-white">1.65</span>
                                    <span class="text-[10px] text-slate-500">pkts/sec</span>
                                </div>
                                <span class="text-[10px] text-slate-400 block mt-0.5" id="rate-hint">Benigno: 1.65 | UDP: 20k</span>
                            </div>

                            <!-- Protocol Type -->
                            <div class="bg-slate-800/60 p-3 rounded-lg border border-slate-700/50 hover:border-cyan-500/40 transition">
                                <div class="flex justify-between items-start">
                                    <span class="text-[11px] text-slate-400">Protocol Type</span>
                                    <span class="text-[9px] text-slate-400 font-mono">IANA</span>
                                </div>
                                <div class="flex items-baseline gap-1 mt-1">
                                    <span id="feat-proto" class="text-xl font-bold font-mono text-white">6</span>
                                    <span class="text-[10px] text-slate-400 font-semibold" id="proto-name">(TCP)</span>
                                </div>
                                <span class="text-[10px] text-slate-400 block mt-0.5" id="proto-hint">TCP=6, UDP=17</span>
                            </div>

                            <!-- Variance (Varianza inter-paquete: #1 importancia por permutación) -->
                            <div class="bg-slate-800/60 p-3 rounded-lg border border-slate-700/50 hover:border-cyan-500/40 transition">
                                <div class="flex justify-between items-start">
                                    <span class="text-[11px] text-slate-400">Variance / Std</span>
                                    <span class="text-[9px] text-purple-400 font-mono">Permutación #1</span>
                                </div>
                                <div class="flex items-baseline gap-1 mt-1">
                                    <span id="feat-var" class="text-xl font-bold font-mono text-white">0.42</span>
                                    <span class="text-[10px] text-slate-500">dispersion</span>
                                </div>
                                <span class="text-[10px] text-slate-400 block mt-0.5">Ataques sintéticos = 0</span>
                            </div>

                            <!-- ack_flag_number -->
                            <div class="bg-slate-800/60 p-3 rounded-lg border border-slate-700/50 hover:border-cyan-500/40 transition">
                                <div class="flex justify-between items-start">
                                    <span class="text-[11px] text-slate-400">ack_flag_number</span>
                                    <span class="text-[9px] text-slate-400 font-mono">Handshake</span>
                                </div>
                                <div class="flex items-baseline gap-1 mt-1">
                                    <span id="feat-ack" class="text-xl font-bold font-mono text-white">1.0</span>
                                    <span class="text-[10px] text-slate-500">0 / 1</span>
                                </div>
                                <span class="text-[10px] text-slate-400 block mt-0.5">Benigno: 90% ACK</span>
                            </div>
                        </div>

                        <!-- Panel de Explicabilidad de la Decisión del Modelo -->
                        <div class="border-t border-slate-800 pt-3">
                            <span class="text-xs text-slate-400 block mb-1 font-semibold flex items-center gap-1.5">
                                <i data-lucide="check-circle-2" class="w-3.5 h-3.5 text-cyan-400"></i> Traza de Decisión & Explicabilidad ML:
                            </span>
                            <div id="decision-trace-box" class="p-2.5 bg-slate-950/80 rounded-lg border border-slate-800 text-[11px] font-mono space-y-1">
                                <div class="text-slate-400" id="trace-step-1">1. Evaluando tamaño de paquete <span class="text-cyan-300">Tot size</span>...</div>
                                <div class="text-slate-400" id="trace-step-2">2. Verificando banderas de control <span class="text-amber-300">syn_flag_number</span>...</div>
                                <div class="text-emerald-400 font-semibold" id="trace-conclusion">Resultado: Benigno confirmado por varianza normal y presencia de ACK.</div>
                            </div>
                        </div>
                    </div>

                </div>

                <!-- Columna Derecha: Gráficos de Telemetría y Consola SOC (7 cols) -->
                <div class="lg:col-span-7 space-y-6">

                    <!-- Tarjeta: Telemetría de Tráfico en Tiempo Real -->
                    <div class="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg">
                        <div class="flex flex-wrap justify-between items-center mb-3 gap-2">
                            <div>
                                <h3 class="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-2">
                                    <i data-lucide="activity" class="w-4 h-4 text-cyan-400"></i> Monitor de Frecuencia de Paquetes (Rate pkts/s)
                                </h3>
                                <p class="text-[10px] text-slate-400">Telemetría de flujo continuo en escala logarítmica / lineal dinámica</p>
                            </div>
                            <span id="traffic-state-badge" class="px-2.5 py-1 text-xs rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 font-semibold">
                                Flujo Normal
                            </span>
                        </div>

                        <div class="h-60 relative">
                            <canvas id="liveChart"></canvas>
                        </div>
                    </div>

                    <!-- Tarjeta: Consola de Eventos y Auditoría SOC -->
                    <div class="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg flex flex-col">
                        <div class="flex justify-between items-center mb-2.5">
                            <h3 class="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-2">
                                <i data-lucide="terminal" class="w-4 h-4 text-cyan-400"></i> Consola Operativa SOC (Security Operations Center)
                            </h3>
                            <button onclick="clearSocLogs()" class="text-[11px] text-slate-400 hover:text-slate-200 transition">
                                Limpiar Registros
                            </button>
                        </div>

                        <div id="soc-log-container" class="bg-slate-950 border border-slate-800/80 rounded-lg p-3 font-mono text-[11px] log-scroll h-52 overflow-y-auto space-y-1.5 shadow-inner">
                            <div class="text-slate-500">[SISTEMA SOC] Pipeline inicializado. Modelo activo: LightGBM (Ensambles Etapa III).</div>
                            <div class="text-slate-500">[SISTEMA SOC] Reglas de homologación y umbrales de decisión cargados desde los Notebooks 01–04.</div>
                        </div>
                    </div>

                </div>

            </div>
        </div>

        <!-- =================================================================== -->
        <!-- PESTAÑA 2: BENCHMARKS & MODELOS (NOTEBOOKS 03 Y 04) -->
        <!-- =================================================================== -->
        <div id="view-benchmarks" class="hidden space-y-6">

            <div class="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg">
                <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-6">
                    <div>
                        <h2 class="text-base font-bold text-white flex items-center gap-2">
                            <i data-lucide="bar-chart-3" class="w-5 h-5 text-emerald-400"></i>
                            Comparativa Experimental de Rendimiento en Prueba Oficial
                        </h2>
                        <p class="text-xs text-slate-400">Métricas oficiales calculadas sobre 415.658 registros no vistos del conjunto oficial de prueba (Test) de CICIoMT2024.</p>
                    </div>

                    <!-- Selector de Tarea -->
                    <div class="flex items-center gap-2">
                        <button onclick="renderBenchmarkView('binaria')" id="btn-bench-binaria" class="px-3 py-1.5 rounded-lg text-xs font-medium bg-emerald-600 text-white transition shadow">
                            Clasificación Binaria (DDoS vs Benigno)
                        </button>
                        <button onclick="renderBenchmarkView('multiclase')" id="btn-bench-multi" class="px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-800 text-slate-300 hover:bg-slate-700 transition">
                            Clasificación Multiclase (SYN, UDP, Benigno)
                        </button>
                    </div>
                </div>

                <!-- Gráfico Comparativo de Modelos -->
                <div class="grid grid-cols-1 lg:grid-cols-12 gap-6 mb-6">
                    <div class="lg:col-span-8 bg-slate-950/60 p-4 rounded-xl border border-slate-800/80">
                        <h3 class="text-xs font-bold text-slate-300 uppercase mb-3 flex items-center justify-between">
                            <span>F1-Score Macro por Algoritmo (Prueba Oficial)</span>
                            <span class="text-[10px] text-slate-400 font-mono">Notebook 04 · Sección 3</span>
                        </h3>
                        <div class="h-64 relative">
                            <canvas id="benchmarkChart"></canvas>
                        </div>
                    </div>

                    <!-- Tarjeta de Hallazgo Crucial: El Escenario V1 vs V2 -->
                    <div class="lg:col-span-4 bg-gradient-to-br from-slate-950 to-slate-900 p-4 rounded-xl border border-amber-500/30 flex flex-col justify-between">
                        <div>
                            <div class="flex items-center gap-2 text-amber-400 font-semibold text-xs mb-2">
                                <i data-lucide="alert-triangle" class="w-4 h-4"></i>
                                Hallazgo Crucial Etapa II (Notebook 03):
                            </div>
                            <h4 class="text-sm font-bold text-white mb-2">Sesgo por Omisión de Variantes (V1 vs V2)</h4>
                            <p class="text-xs text-slate-300 leading-relaxed">
                                Si el modelo se entrena únicamente con <em>Benigno + SYN Flood</em> (Escenario V1), al evaluar ante tráfico <em>UDP Flood</em> el <strong class="text-red-400">Recall UDP cae a 0,0%</strong> y se dejan pasar <span class="font-mono text-amber-300">206.141 ataques</span> no detectados.
                            </p>
                            <p class="text-xs text-slate-400 mt-2">
                                Solo al incluir ambas variantes (V2) el F1 Macro asciende de <span class="font-mono text-red-400">0.446</span> a <span class="font-mono text-emerald-400">0.998</span>.
                            </p>
                        </div>
                        <div class="mt-4 pt-3 border-t border-slate-800 flex justify-between items-center text-[11px]">
                            <span class="text-slate-400">Ataques no detectados (V1):</span>
                            <span class="text-red-400 font-mono font-bold">206.203 flujos</span>
                        </div>
                    </div>
                </div>

                <!-- Tabla Dinámica con Datos CSV -->
                <div class="overflow-x-auto">
                    <table class="w-full text-left text-xs text-slate-300">
                        <thead class="bg-slate-800/80 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-700">
                            <tr id="benchmark-table-headers">
                                <!-- Headers generados por JS -->
                            </tr>
                        </thead>
                        <tbody id="benchmark-table-body" class="divide-y divide-slate-800/60 font-mono text-[11px]">
                            <!-- Rows generadas por JS -->
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Tabla de Hiperparámetros Optimizados (Notebook 04) -->
            <div class="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg">
                <h3 class="text-sm font-bold text-white uppercase tracking-wider mb-2 flex items-center gap-2">
                    <i data-lucide="cpu" class="w-4 h-4 text-cyan-400"></i> Búsqueda de Hiperparámetros y Tiempos de Entrenamiento
                </h3>
                <p class="text-xs text-slate-400 mb-4">Configuraciones seleccionadas mediante validación cruzada estratificada (5-folds) reportadas en <span class="font-mono text-cyan-300">busqueda_hiperparametros.csv</span>.</p>

                <div class="overflow-x-auto">
                    <table class="w-full text-left text-xs text-slate-300">
                        <thead class="bg-slate-800/80 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-700">
                            <tr>
                                <th class="p-3">Tarea</th>
                                <th class="p-3">Algoritmo</th>
                                <th class="p-3">Mejores Hiperparámetros</th>
                                <th class="p-3">F1 Macro CV</th>
                                <th class="p-3">Tiempo (seg)</th>
                            </tr>
                        </thead>
                        <tbody id="hyperparam-table-body" class="divide-y divide-slate-800/60 font-mono text-[11px]">
                            <!-- Rellenado por JS -->
                        </tbody>
                    </table>
                </div>
            </div>

        </div>

        <!-- =================================================================== -->
        <!-- PESTAÑA 3: GENERALIZACIÓN CRUZADA & ABLACIÓN (NOTEBOOK 04) -->
        <!-- =================================================================== -->
        <div id="view-generalizacion" class="hidden space-y-6">

            <!-- Banner Resumen del Problema de Dominio -->
            <div class="bg-gradient-to-r from-purple-950/40 via-slate-900 to-slate-900 border border-purple-500/30 rounded-xl p-5 shadow-lg">
                <div class="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4">
                    <div class="max-w-3xl">
                        <span class="text-xs font-bold text-purple-400 uppercase tracking-wider flex items-center gap-1.5 mb-1">
                            <i data-lucide="git-branch" class="w-4 h-4"></i> Contribución Central de la Investigación (Notebook 04 · Secciones 5 y 6)
                        </span>
                        <h2 class="text-lg font-bold text-white">El Abismo de la Generalización Cruzada: IoMT vs Red Tradicional</h2>
                        <p class="text-xs text-slate-300 mt-1 leading-relaxed">
                            Al entrenar en redes empresariales tradicionales (CIC-DDoS2019 con CICFlowMeter) y evaluar en redes médicas IoMT (CICIoMT2024), el rendimiento colapsa dramáticamente debido a <strong>discrepancias en los extractores de flujo</strong> y características topológicas.
                        </p>
                    </div>

                    <!-- Scorecard de Degradación -->
                    <div class="flex items-center gap-3">
                        <div class="bg-slate-850 p-3 rounded-lg border border-red-500/30 text-center">
                            <span class="text-[10px] text-slate-400 block uppercase">Tradicional → IoMT</span>
                            <span class="text-xl font-bold font-mono text-red-400">-63.5%</span>
                            <span class="text-[9px] text-slate-400 block">Caída en F1 Macro</span>
                        </div>
                        <div class="bg-slate-850 p-3 rounded-lg border border-amber-500/30 text-center">
                            <span class="text-[10px] text-slate-400 block uppercase">IoMT → Tradicional</span>
                            <span class="text-xl font-bold font-mono text-amber-400">-36.3%</span>
                            <span class="text-[9px] text-slate-400 block">Caída en F1 Macro</span>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Gráfico y Tabla del Estudio de Ablación -->
            <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">

                <!-- Gráfico de Variantes de Homologación -->
                <div class="lg:col-span-7 bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg">
                    <div class="flex justify-between items-center mb-3">
                        <div>
                            <h3 class="text-xs font-bold text-slate-300 uppercase tracking-wider">
                                Estudio de Ablación de la Homologación (Notebook 04 · Sección 6.1)
                            </h3>
                            <p class="text-[11px] text-slate-400">Impacto de cada corrección sobre el F1 Macro Cruzado</p>
                        </div>
                        <span class="text-[10px] font-mono text-cyan-400 bg-cyan-950 px-2 py-0.5 rounded border border-cyan-800">
                            LightGBM Fijo
                        </span>
                    </div>

                    <div class="h-64 relative">
                        <canvas id="ablationChart"></canvas>
                    </div>

                    <div class="mt-4 pt-3 border-t border-slate-800 text-xs text-slate-400 space-y-1">
                        <p><strong class="text-slate-300">A → B (Alineación +34B):</strong> Corrige la discrepancia donde CICFlowMeter mide solo carga útil y CICIoMT mide trama completa. Recupera de 0.245 a 0.398.</p>
                        <p><strong class="text-slate-300">B → C (Eliminar SYN/ACK):</strong> Descarta el bug conocido de CICFlowMeter-V3 donde el SYN flood se registra con SYN=0 y ACK=1. F1 asciende al pico de 0.480.</p>
                    </div>
                </div>

                <!-- Tabla de Degradación Cruzada -->
                <div class="lg:col-span-5 bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg flex flex-col justify-between">
                    <div>
                        <h3 class="text-xs font-bold text-slate-300 uppercase tracking-wider mb-2">
                            Matriz de Generalización Cruzada
                        </h3>
                        <p class="text-[11px] text-slate-400 mb-3">Datos oficiales de <span class="font-mono text-cyan-300">generalizacion_cruzada.csv</span></p>

                        <div class="space-y-3 font-mono text-xs">
                            <div class="p-3 bg-slate-950 rounded-lg border border-slate-800">
                                <div class="flex justify-between items-center text-slate-300 mb-1">
                                    <span class="font-bold">IoMT → IoMT (Mismo Dominio)</span>
                                    <span class="text-emerald-400 font-bold">F1: 0.998</span>
                                </div>
                                <div class="text-[10px] text-slate-400">Recall SYN: 99.76% | Recall UDP: 99.98% | Falsas Alarmas: 7</div>
                            </div>

                            <div class="p-3 bg-slate-950 rounded-lg border border-amber-900/40">
                                <div class="flex justify-between items-center text-slate-300 mb-1">
                                    <span class="font-bold text-amber-300">IoMT → Tradicional (Cruzado)</span>
                                    <span class="text-amber-400 font-bold">F1: 0.718</span>
                                </div>
                                <div class="text-[10px] text-slate-400">Recall SYN: 99.87% | Recall UDP: <span class="text-red-400">44.64%</span> | Falsas Alarmas: 5.267</div>
                            </div>

                            <div class="p-3 bg-slate-950 rounded-lg border border-red-900/50">
                                <div class="flex justify-between items-center text-slate-300 mb-1">
                                    <span class="font-bold text-red-400">Tradicional → IoMT (Cruzado)</span>
                                    <span class="text-red-400 font-bold">F1: 0.389</span>
                                </div>
                                <div class="text-[10px] text-slate-400">Recall SYN: 68.23% | Recall UDP: <span class="text-red-400 font-bold">3.21%</span> | Ataques Perdidos: 253.826</div>
                            </div>
                        </div>
                    </div>

                    <div class="mt-4 p-3 bg-slate-950/60 rounded-lg border border-slate-800/80 text-[11px] text-slate-400">
                        <strong class="text-slate-300">Conclusión técnica:</strong> Los modelos tradicionales son prácticamente ciegos ante el ataque DDoS UDP en entornos IoMT (dejan pasar el 97% de los flujos maliciosos).
                    </div>
                </div>

            </div>

        </div>

        <!-- =================================================================== -->
        <!-- PESTAÑA 4: EXPLICABILIDAD & ESTABILIDAD (KS/PSI) -->
        <!-- =================================================================== -->
        <div id="view-explicabilidad" class="hidden space-y-6">

            <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">

                <!-- Tarjeta: Importancia por Permutación (Notebook 04 · Sección 4) -->
                <div class="lg:col-span-6 bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg">
                    <div class="flex justify-between items-center mb-2">
                        <h3 class="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-2">
                            <i data-lucide="cpu" class="w-4 h-4 text-amber-400"></i> Importancia por Permutación (LightGBM)
                        </h3>
                        <span class="text-[10px] bg-slate-800 text-slate-400 px-2 py-0.5 rounded font-mono">20k muestras val</span>
                    </div>
                    <p class="text-xs text-slate-400 mb-4">Caída del F1 Macro en validación al desordenar aleatoriamente cada variable (independiente de la heurística interna del árbol).</p>

                    <div class="h-72 relative">
                        <canvas id="importanceChart"></canvas>
                    </div>

                    <div class="mt-4 pt-3 border-t border-slate-800 text-[11px] text-slate-400">
                        <span class="text-slate-300 font-semibold">Hallazgo clave:</span> A diferencia del árbol simple que dependía casi al 100% de <span class="font-mono text-cyan-300">Tot size</span> y <span class="font-mono text-amber-300">syn_flag_number</span>, el ensamble de boosting distribuye el peso en <span class="font-mono text-purple-300">Variance</span> y <span class="font-mono text-cyan-300">Rate</span> para evitar atajos frágiles.
                    </div>
                </div>

                <!-- Tarjeta: Selección de Variables (Notebook 02) -->
                <div class="lg:col-span-6 bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg flex flex-col justify-between">
                    <div>
                        <div class="flex justify-between items-center mb-2">
                            <h3 class="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-2">
                                <i data-lucide="database" class="w-4 h-4 text-cyan-400"></i> Auditoría de Selección de Variables (NB 02)
                            </h3>
                            <span class="text-[10px] bg-emerald-950 text-emerald-400 px-2 py-0.5 rounded font-mono">34 de 45 seleccionadas</span>
                        </div>
                        <p class="text-xs text-slate-400 mb-4">Eliminación sistemática de variables no confiables, colineales o dependientes del entorno de captura.</p>

                        <!-- Desglose de Exclusiones -->
                        <div class="space-y-2 text-xs font-mono">
                            <div class="p-2.5 bg-slate-950 rounded-lg border border-red-900/30 flex justify-between items-center">
                                <div>
                                    <span class="text-red-400 font-bold">IAT, Number, Weight</span>
                                    <span class="text-[10px] text-slate-500 block">Variables Sospechosas de Captura</span>
                                </div>
                                <span class="text-[10px] bg-red-950 text-red-300 px-2 py-0.5 rounded">Exclusión Manual</span>
                            </div>

                            <div class="p-2.5 bg-slate-950 rounded-lg border border-slate-800 flex justify-between items-center">
                                <div>
                                    <span class="text-slate-300 font-bold">Drate</span>
                                    <span class="text-[10px] text-slate-500 block">Varianza nula en flujos</span>
                                </div>
                                <span class="text-[10px] bg-slate-800 text-slate-400 px-2 py-0.5 rounded">Constante</span>
                            </div>

                            <div class="p-2.5 bg-slate-950 rounded-lg border border-slate-800 flex justify-between items-center">
                                <div>
                                    <span class="text-slate-300 font-bold">Srate</span>
                                    <span class="text-[10px] text-slate-500 block">Correlación > 0.98 con Rate</span>
                                </div>
                                <span class="text-[10px] bg-slate-800 text-slate-400 px-2 py-0.5 rounded">Redundancia</span>
                            </div>

                            <div class="p-2.5 bg-slate-950 rounded-lg border border-slate-800 flex justify-between items-center">
                                <div>
                                    <span class="text-slate-300 font-bold">TCP, UDP</span>
                                    <span class="text-[10px] text-slate-500 block">Correlación > 0.98 con Protocol Type</span>
                                </div>
                                <span class="text-[10px] bg-slate-800 text-slate-400 px-2 py-0.5 rounded">Redundancia</span>
                            </div>
                        </div>
                    </div>

                    <div class="mt-4 pt-3 border-t border-slate-800 flex justify-between items-center text-xs text-slate-400">
                        <span>Poder discriminante máximo individual:</span>
                        <span class="text-emerald-400 font-mono font-bold">AVG (99.26% exactitud)</span>
                    </div>
                </div>

            </div>

            <!-- Tabla de Estabilidad Temporal / Concept Drift dentro de IoMT (KS y PSI) -->
            <div class="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg">
                <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 mb-4">
                    <div>
                        <h3 class="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                            <i data-lucide="activity" class="w-4 h-4 text-purple-400"></i> Estabilidad Temporal de Variables en IoMT (Train vs Test)
                        </h3>
                        <p class="text-xs text-slate-400">Pruebas Kolmogorov-Smirnov (KS: 0=idénticas, 1=disjuntas) y Population Stability Index (PSI &lt; 0.1 estable) de <span class="font-mono text-cyan-300">estabilidad_variables_iomt.csv</span>.</p>
                    </div>

                    <div class="flex items-center gap-2">
                        <span class="text-xs text-slate-400">Filtrar:</span>
                        <select id="stability-filter" onchange="renderStabilityTable()" class="bg-slate-800 border border-slate-700 text-slate-300 rounded-lg px-2.5 py-1 text-xs">
                            <option value="all">Todas las variables (34)</option>
                            <option value="stable">Más Estables (KS &lt; 0.05)</option>
                            <option value="drift">Con Mayor Deriva (KS &gt; 0.05)</option>
                        </select>
                    </div>
                </div>

                <div class="overflow-x-auto">
                    <table class="w-full text-left text-xs text-slate-300">
                        <thead class="bg-slate-800/80 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-700">
                            <tr>
                                <th class="p-3">Variable</th>
                                <th class="p-3">KS Medio</th>
                                <th class="p-3">KS Máximo</th>
                                <th class="p-3">PSI Medio</th>
                                <th class="p-3">Importancia Permutación</th>
                                <th class="p-3">Diagnóstico de Estabilidad</th>
                            </tr>
                        </thead>
                        <tbody id="stability-table-body" class="divide-y divide-slate-800/60 font-mono text-[11px]">
                            <!-- Rellenado por JS -->
                        </tbody>
                    </table>
                </div>
            </div>

        </div>

        <!-- =================================================================== -->
        <!-- PESTAÑA 5: GALERÍA DE FIGURAS OFICIALES CRISP-DM -->
        <!-- =================================================================== -->
        <div id="view-figuras" class="hidden space-y-6">

            <div class="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg">
                <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
                    <div>
                        <h2 class="text-base font-bold text-white flex items-center gap-2">
                            <i data-lucide="layers" class="w-5 h-5 text-pink-400"></i>
                            Galería de Evidencias y Figuras de los Notebooks
                        </h2>
                        <p class="text-xs text-slate-400">Visualice directamente las 16 figuras oficiales exportadas durante las etapas CRISP-DM del proyecto.</p>
                    </div>

                    <!-- Filtros por Etapa -->
                    <div class="flex flex-wrap gap-1.5">
                        <button onclick="filterGallery('all')" class="gallery-filter-btn px-2.5 py-1 rounded-md text-xs bg-slate-800 text-slate-300 hover:bg-slate-700 active-filter">Todas</button>
                        <button onclick="filterGallery('01_eda')" class="gallery-filter-btn px-2.5 py-1 rounded-md text-xs bg-slate-800 text-slate-300 hover:bg-slate-700">01 EDA & Limpieza</button>
                        <button onclick="filterGallery('02_fe')" class="gallery-filter-btn px-2.5 py-1 rounded-md text-xs bg-slate-800 text-slate-300 hover:bg-slate-700">02 Preprocesamiento</button>
                        <button onclick="filterGallery('03_base')" class="gallery-filter-btn px-2.5 py-1 rounded-md text-xs bg-slate-800 text-slate-300 hover:bg-slate-700">03 Línea Base</button>
                        <button onclick="filterGallery('04_final')" class="gallery-filter-btn px-2.5 py-1 rounded-md text-xs bg-slate-800 text-slate-300 hover:bg-slate-700">04 Modelos Finales</button>
                    </div>
                </div>

                <!-- Grilla de Imágenes -->
                <div id="gallery-grid" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                    <!-- Cards generadas por JS -->
                </div>
            </div>

        </div>

    </main>

    <!-- Modal para Zoom de Figuras -->
    <div id="image-modal" class="fixed inset-0 z-50 bg-black/90 hidden flex items-center justify-center p-4 backdrop-blur-sm" onclick="closeImageModal()">
        <div class="max-w-5xl max-h-[90vh] bg-slate-900 border border-slate-700 rounded-2xl overflow-hidden flex flex-col shadow-2xl" onclick="event.stopPropagation()">
            <div class="p-4 border-b border-slate-800 flex justify-between items-center bg-slate-950">
                <h3 id="modal-title" class="text-sm font-bold text-white"></h3>
                <button onclick="closeImageModal()" class="text-slate-400 hover:text-white p-1 rounded-lg">
                    <i data-lucide="x" class="w-5 h-5"></i>
                </button>
            </div>
            <div class="p-3 overflow-auto flex-1 flex items-center justify-center bg-slate-950/60">
                <img id="modal-img" src="" alt="Figura" class="max-h-[75vh] w-auto object-contain rounded-lg shadow-lg">
            </div>
            <div class="p-4 border-t border-slate-800 bg-slate-950 text-xs text-slate-300" id="modal-caption"></div>
        </div>
    </div>

    <!-- Footer -->
    <footer class="bg-slate-900 border-t border-slate-800 px-6 py-4 text-center text-xs text-slate-500 mt-12">
        <p>Sistema Inteligente de Detección de Intrusiones en Redes (NIDS) | Proyecto de Ciencia de Datos</p>
        <p class="mt-1 text-[11px] text-slate-600">Integración de resultados de Notebooks 01, 02, 03 y 04 · Dataset CICIoMT2024 & CIC-DDoS2019</p>
    </footer>

    <!-- =================================================================== -->
    <!-- SCRIPT DE DATOS Y LÓGICA DE LA APLICACIÓN -->
    <!-- =================================================================== -->
    <script>
        // Datos recolectados de los notebooks (CSV completos convertidos a JSON)
        const NOTEBOOK_DATA = %DATA_PLACEHOLDER%;

        // Inicializar iconos Lucide
        lucide.createIcons();

        // -------------------------------------------------------------
        // ESTADO GLOBAL DEL SIMULADOR & MODELO SOC
        // -------------------------------------------------------------
        let isSimRunning = true;
        let simInterval = 1000;
        let simTimer = null;
        let soundAlertEnabled = false;

        // Audio Context para alarma sonora
        let audioCtx = null;
        function playAlertBeep(freq = 660, duration = 0.15) {
            if (!soundAlertEnabled) return;
            try {
                if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
                const osc = audioCtx.createOscillator();
                const gain = audioCtx.createGain();
                osc.type = 'sawtooth';
                osc.frequency.value = freq;
                gain.gain.setValueAtTime(0.08, audioCtx.currentTime);
                gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + duration);
                osc.connect(gain);
                gain.connect(audioCtx.destination);
                osc.start();
                osc.stop(audioCtx.currentTime + duration);
            } catch(e) {}
        }

        // Estado del generador de tráfico y forzado
        let currentTrafficType = 'BENIGN';
        let currentTrafficTicksLeft = 8;

        // Variables de Forzado de Ataques y Aleatoriedad
        let forcedAttackMode = 'NONE'; // 'NONE' (estocástico aleatorio), 'DDOS_SYN', 'DDOS_UDP', 'MIXED'
        let forcedTicksRemaining = 0; // > 0 ticks restantes, -1 permanente
        let spontaneousAttackRate = 0.45; // frecuencia de ataques espontáneos en modo automático (45%)

        // Elementos DOM
        const statusBadge = document.getElementById('status-badge');
        const statusText = document.getElementById('status-text');
        const scenarioSelect = document.getElementById('scenario-select');
        const toggleSimBtn = document.getElementById('toggle-sim-btn');
        const simBtnLabel = document.getElementById('sim-btn-label');
        const playIcon = document.getElementById('play-icon');
        const speedRange = document.getElementById('speed-range');
        const speedLabel = document.getElementById('speed-label');
        const trafficStateBadge = document.getElementById('traffic-state-badge');
        const socLogContainer = document.getElementById('soc-log-container');

        const forcedStatusPill = document.getElementById('forced-status-pill');
        const forcedDurationSelect = document.getElementById('forced-duration-select');
        const autoAttackFreqSelect = document.getElementById('auto-attack-freq-select');

        // Feature Elements
        const featTotSize = document.getElementById('feat-tot-size');
        const featSyn = document.getElementById('feat-syn');
        const featRate = document.getElementById('feat-rate');
        const featProto = document.getElementById('feat-proto');
        const protoName = document.getElementById('proto-name');
        const featVar = document.getElementById('feat-var');
        const featAck = document.getElementById('feat-ack');

        const traceStep1 = document.getElementById('trace-step-1');
        const traceStep2 = document.getElementById('trace-step-2');
        const traceConclusion = document.getElementById('trace-conclusion');

        // -------------------------------------------------------------
        // CONTROL DE FORZADO DE ATAQUES & SIMULACIÓN ESTOCÁSTICA
        // -------------------------------------------------------------
        function triggerForcedAttack(type) {
            const duration = forcedDurationSelect ? parseInt(forcedDurationSelect.value, 10) : 10;
            forcedAttackMode = type;
            forcedTicksRemaining = duration;

            const names = {
                'DDOS_SYN': 'DDoS SYN Flood (54B @ 11.3 pkts/s)',
                'DDOS_UDP': 'DDoS UDP Flood (50B @ >20k pkts/s)',
                'MIXED': 'Ataque Multivector (SYN + UDP Alternados)'
            };
            const durText = duration === -1 ? 'modo continuo permanente' : duration + ' ticks';
            addSocLog('[CONTROL FORZADO] ¡Ataque forzado activado!: ' + (names[type] || type) + ' durante ' + durText + '.', 'alert');
            updateForcedStateBadge();

            // Si la simulación estaba en pausa, ejecutar un tick inmediato para feedback en vivo
            if (!isSimRunning) {
                processVector(generateTelemetryVector());
            }
        }

        function resetToRandomStochastic() {
            forcedAttackMode = 'NONE';
            forcedTicksRemaining = 0;
            currentTrafficType = 'BENIGN';
            currentTrafficTicksLeft = Math.floor(Math.random() * 8) + 6;
            addSocLog('[CONTROL FORZADO] Ataque forzado cancelado. Retomando aleatoriedad estocástica natural.', 'info');
            updateForcedStateBadge();
            if (!isSimRunning) {
                processVector(generateTelemetryVector());
            }
        }

        function updateSpontaneousRate() {
            if (autoAttackFreqSelect) {
                spontaneousAttackRate = parseFloat(autoAttackFreqSelect.value);
                addSocLog('[SIMULADOR] Frecuencia de ataques automáticos aleatorios fijada en ' + (spontaneousAttackRate * 100).toFixed(0) + '%.', 'info');
            }
        }

        function updateForcedStateBadge() {
            if (!forcedStatusPill) return;

            if (forcedAttackMode === 'NONE') {
                forcedStatusPill.className = 'text-[10px] px-2.5 py-0.5 rounded-full border bg-emerald-500/10 text-emerald-400 border-emerald-500/30 font-mono font-semibold flex items-center gap-1.5';
                forcedStatusPill.innerHTML = '<span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span> Aleatorio Activo';
            } else {
                const countText = forcedTicksRemaining === -1 ? 'Continuo' : forcedTicksRemaining + ' ticks';
                if (forcedAttackMode === 'DDOS_SYN') {
                    forcedStatusPill.className = 'text-[10px] px-2.5 py-0.5 rounded-full border bg-amber-500/20 text-amber-300 border-amber-500/40 font-mono font-bold flex items-center gap-1.5 alert-syn';
                    forcedStatusPill.innerHTML = '<span class="w-1.5 h-1.5 rounded-full bg-amber-400 animate-ping"></span> Forzado: SYN (' + countText + ')';
                } else if (forcedAttackMode === 'DDOS_UDP') {
                    forcedStatusPill.className = 'text-[10px] px-2.5 py-0.5 rounded-full border bg-red-500/20 text-red-300 border-red-500/40 font-mono font-bold flex items-center gap-1.5 alert-udp';
                    forcedStatusPill.innerHTML = '<span class="w-1.5 h-1.5 rounded-full bg-red-400 animate-ping"></span> Forzado: UDP (' + countText + ')';
                } else if (forcedAttackMode === 'MIXED') {
                    forcedStatusPill.className = 'text-[10px] px-2.5 py-0.5 rounded-full border bg-purple-500/20 text-purple-300 border-purple-500/40 font-mono font-bold flex items-center gap-1.5';
                    forcedStatusPill.innerHTML = '<span class="w-1.5 h-1.5 rounded-full bg-purple-400 animate-ping"></span> Forzado: Mixto (' + countText + ')';
                }
            }
        }

        // -------------------------------------------------------------
        // CONFIGURACIÓN DE CHART.JS (TELEMETRÍA EN VIVO)
        // -------------------------------------------------------------
        const liveCtx = document.getElementById('liveChart').getContext('2d');
        const MAX_POINTS = 35;
        const initialPoints = Array(MAX_POINTS).fill(1.65);
        const emptyLabels = Array(MAX_POINTS).fill('');

        const liveChart = new Chart(liveCtx, {
            type: 'line',
            data: {
                labels: emptyLabels,
                datasets: [
                    {
                        label: 'Tasa de Flujo (Rate pkts/s)',
                        data: [...initialPoints],
                        borderColor: '#06b6d4',
                        backgroundColor: 'rgba(6, 182, 212, 0.1)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.35,
                        pointRadius: 0
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: { duration: 300 },
                scales: {
                    x: { display: false },
                    y: {
                        grid: { color: 'rgba(51, 65, 85, 0.35)' },
                        ticks: { color: '#94a3b8', font: { family: 'monospace' } },
                        beginAtZero: true
                    }
                },
                plugins: {
                    legend: { display: false }
                }
            }
        });

        // -------------------------------------------------------------
        // MOTOR DE SIMULACIÓN Y GENERACIÓN ESTOCÁSTICA REALISTA
        // (Calibrado con las medianas de la Sección 5 del Notebook 01)
        // -------------------------------------------------------------
        function generateTelemetryVector() {
            // 1. PRIORIDAD: Si hay un ataque forzado activo
            if (forcedAttackMode !== 'NONE') {
                let typeToEmit = forcedAttackMode;
                if (forcedAttackMode === 'MIXED') {
                    // Alterna entre SYN y UDP en cada tick
                    typeToEmit = (forcedTicksRemaining % 2 === 0) ? 'DDOS_SYN' : 'DDOS_UDP';
                }

                if (forcedTicksRemaining > 0) {
                    forcedTicksRemaining--;
                    if (forcedTicksRemaining === 0) {
                        // Al concluir la ráfaga forzada, retornar automáticamente al modo estocástico
                        forcedAttackMode = 'NONE';
                        currentTrafficType = 'BENIGN';
                        currentTrafficTicksLeft = Math.floor(Math.random() * 8) + 6;
                        addSocLog('[CONTROL FORZADO] Ráfaga forzada completada. Retomando aleatoriedad automática.', 'info');
                    }
                }
                updateForcedStateBadge();
                return createVectorByType(typeToEmit);
            }

            // 2. MODO ESTOCÁSTICO AUTOMÁTICO (Aleatoriedad Natural)
            if (currentTrafficTicksLeft <= 0) {
                const r = Math.random();
                const benignProb = Math.max(0.01, 1 - spontaneousAttackRate);
                const synProb = spontaneousAttackRate * 0.55;

                if (r < benignProb) {
                    currentTrafficType = 'BENIGN';
                    currentTrafficTicksLeft = Math.floor(Math.random() * 8) + 6; // 6 a 14 ticks de benigno
                } else if (r < benignProb + synProb) {
                    currentTrafficType = 'DDOS_SYN';
                    currentTrafficTicksLeft = Math.floor(Math.random() * 6) + 4; // 4 a 9 ticks de ataque SYN
                } else {
                    currentTrafficType = 'DDOS_UDP';
                    currentTrafficTicksLeft = Math.floor(Math.random() * 6) + 4; // 4 a 10 ticks de ataque UDP
                }
            } else {
                currentTrafficTicksLeft--;
            }

            updateForcedStateBadge();
            return createVectorByType(currentTrafficType);
        }

        function createVectorByType(type) {
            let totSize, rate, syn, ack, proto, variance, std;

            if (type === 'BENIGN') {
                // Benigno IoMT: Mediana Tot size = 80.8B, AVG = 83B, Rate = 1.65 pkts/s, Std = 17.2, ACK=1, TCP=1
                totSize = +(Math.random() * 40 + 70).toFixed(1);
                rate = +(Math.random() * 2.5 + 0.8).toFixed(2);
                syn = 0.0;
                ack = 1.0;
                proto = 6;
                variance = +(Math.random() * 0.4 + 0.2).toFixed(3);
                std = +(Math.random() * 15 + 10).toFixed(1);
            } else if (type === 'DDOS_SYN') {
                // DDoS SYN: Mediana Tot size = 54.0B (14E+20IP+20TCP), Rate = 11.29 pkts/s, SYN=1, ACK=0, Std = 0
                totSize = 54.0;
                rate = +(Math.random() * 8 + 9.5).toFixed(2);
                syn = 1.0;
                ack = 0.0;
                proto = 6;
                variance = 0.000;
                std = 0.0;
            } else if (type === 'DDOS_UDP') {
                // DDoS UDP: Mediana Tot size = 50.0B, Rate = 20,335 pkts/s!, UDP=17, SYN=0, ACK=0, Std = 0
                totSize = 50.0;
                rate = +(Math.random() * 6000 + 18000).toFixed(1);
                syn = 0.0;
                ack = 0.0;
                proto = 17;
                variance = 0.000;
                std = 0.0;
            } else if (type === 'ENTERPRISE') {
                // Red Tradicional CIC-DDoS2019 sin cabecera alineada (payload 0B)
                totSize = +(Math.random() * 20 + 20).toFixed(1);
                rate = +(Math.random() * 30 + 15).toFixed(2);
                syn = 0.0; // por el bug de CICFlowMeter-V3
                ack = 1.0;
                proto = 6;
                variance = 0.005;
                std = 0.5;
            }

            return { totSize, rate, syn, ack, proto, variance, std, realClass: type };
        }

        // -------------------------------------------------------------
        // MOTOR DE INFERENCIA SEGÚN EL ESCENARIO EXPERIMENTAL
        // -------------------------------------------------------------
        function runModelInference(features, scenario) {
            // Escenario 1: Ensamble Óptimo (LightGBM/XGBoost - Mismo Dominio)
            if (scenario === 'optimal_iomt') {
                if (features.realClass === 'DDOS_SYN') {
                    return {
                        predLabel: 'DDoS SYN Flood',
                        isAttack: true,
                        attackType: 'SYN',
                        color: '#f59e0b',
                        confidence: 99.8,
                        ruleUsed: 'Tot size == 54.0B y syn_flag == 1.0 detectado. Clasificación precisa sin falsas alarmas.'
                    };
                } else if (features.realClass === 'DDOS_UDP') {
                    return {
                        predLabel: 'DDoS UDP Flood',
                        isAttack: true,
                        attackType: 'UDP',
                        color: '#ef4444',
                        confidence: 99.9,
                        ruleUsed: 'Tot size == 50.0B y Rate masivo (>10k pkts/s) en protocolo UDP (17).'
                    };
                } else {
                    return {
                        predLabel: 'Benigno',
                        isAttack: false,
                        color: '#10b981',
                        confidence: 100.0,
                        ruleUsed: 'Tot size normal (>70B), varianza alta y bandera ACK presente.'
                    };
                }
            }

            // Escenario 2: Sesgo de Variantes V1 (Entrenado solo con Benigno + SYN - Notebook 03)
            if (scenario === 'bias_v1') {
                if (features.realClass === 'DDOS_UDP') {
                    // ¡FALLO CRÍTICO DEMOSTRADO EN NOTEBOOK 03!
                    return {
                        predLabel: 'Benigno (¡Falso Negativo Catastrófico!)',
                        isAttack: false,
                        isMisclassifiedAttack: true,
                        color: '#f43f5e',
                        confidence: 50.4,
                        ruleUsed: '¡FALLO V1! El modelo solo vio SYN en entrenamiento. UDP no coincide con syn_flag=1 y se clasifica erróneamente como Benigno (Recall UDP = 0.0%).'
                    };
                } else if (features.realClass === 'DDOS_SYN') {
                    return {
                        predLabel: 'DDoS SYN Flood',
                        isAttack: true,
                        attackType: 'SYN',
                        color: '#f59e0b',
                        confidence: 99.7,
                        ruleUsed: 'syn_flag == 1.0 reconocido correctamente.'
                    };
                } else {
                    return {
                        predLabel: 'Benigno',
                        isAttack: false,
                        color: '#10b981',
                        confidence: 99.8,
                        ruleUsed: 'Tráfico benigno clasificado normalmente.'
                    };
                }
            }

            // Escenario 3: Despliegue Cruzado sin Adaptar (Tradicional → IoMT - Notebook 04)
            if (scenario === 'cross_trad_iomt') {
                if (features.realClass === 'DDOS_UDP') {
                    // En Notebook 04 tabla generalizacion_cruzada: Recall UDP fue apenas 3.2% (97.2% perdido!)
                    const randomPass = Math.random() < 0.968;
                    if (randomPass) {
                        return {
                            predLabel: 'Benigno (¡Omisión por Degradación Cruzada!)',
                            isAttack: false,
                            isMisclassifiedAttack: true,
                            color: '#e11d48',
                            confidence: 38.9,
                            ruleUsed: '¡DEGRADACIÓN CRUZADA! El modelo tradicional ignora las características de IoMT (Recall UDP 3.2%). -63.5% caída F1.'
                        };
                    } else {
                        return {
                            predLabel: 'DDoS UDP Flood (Detectado al azar)',
                            isAttack: true,
                            attackType: 'UDP',
                            color: '#ef4444',
                            confidence: 52.0,
                            ruleUsed: 'Detección marginal por tasa.'
                        };
                    }
                } else if (features.realClass === 'DDOS_SYN') {
                    if (Math.random() < 0.31) {
                        return {
                            predLabel: 'Benigno (Falso Negativo por Extractores)',
                            isAttack: false,
                            isMisclassifiedAttack: true,
                            color: '#e11d48',
                            confidence: 45.0,
                            ruleUsed: 'Discrepancia entre CICFlowMeter y CICIoMT2024 produce falso negativo.'
                        };
                    } else {
                        return {
                            predLabel: 'DDoS SYN Flood',
                            isAttack: true,
                            attackType: 'SYN',
                            color: '#f59e0b',
                            confidence: 68.2,
                            ruleUsed: 'DDoS SYN detectado con confianza reducida.'
                        };
                    }
                } else {
                    return {
                        predLabel: 'Benigno',
                        isAttack: false,
                        color: '#10b981',
                        confidence: 99.6,
                        ruleUsed: 'Benigno tradicional.'
                    };
                }
            }

            // Escenario 4: Homologación Corregida (Ablación +34B y Filtrado SYN/ACK)
            if (scenario === 'cross_ablated') {
                if (features.realClass === 'DDOS_SYN' || features.realClass === 'DDOS_UDP') {
                    return {
                        predLabel: features.realClass === 'DDOS_SYN' ? 'DDoS SYN (Homologado)' : 'DDoS UDP (Homologado)',
                        isAttack: true,
                        attackType: features.realClass === 'DDOS_SYN' ? 'SYN' : 'UDP',
                        color: features.realClass === 'DDOS_SYN' ? '#f59e0b' : '#ef4444',
                        confidence: 76.5,
                        ruleUsed: 'Alineación de longitud (+34B cabeceras) y filtrado de banderas corruptas permite recuperar detección en dominio cruzado.'
                    };
                } else {
                    return {
                        predLabel: 'Benigno (Homologado)',
                        isAttack: false,
                        color: '#10b981',
                        confidence: 96.5,
                        ruleUsed: 'Homologación estabilizada.'
                    };
                }
            }

            // Escenario 5: Árbol de Decisión Base (Profundidad 4 - Notebook 03)
            if (scenario === 'decision_tree') {
                if (features.totSize <= 67.0) {
                    if (features.syn > 0.5) {
                        return {
                            predLabel: 'DDoS SYN (Árbol)',
                            isAttack: true,
                            attackType: 'SYN',
                            color: '#f59e0b',
                            confidence: 99.6,
                            ruleUsed: 'Regla 1: Tot size <= 67.0B AND syn_flag_number > 0.5'
                        };
                    } else {
                        return {
                            predLabel: 'DDoS UDP (Árbol)',
                            isAttack: true,
                            attackType: 'UDP',
                            color: '#ef4444',
                            confidence: 99.4,
                            ruleUsed: 'Regla 2: Tot size <= 67.0B AND syn_flag_number <= 0.5'
                        };
                    }
                } else {
                    return {
                        predLabel: 'Benigno (Árbol)',
                        isAttack: false,
                        color: '#10b981',
                        confidence: 99.7,
                        ruleUsed: 'Regla 3: Tot size > 67.0B'
                    };
                }
            }

            return { predLabel: 'Benigno', isAttack: false, color: '#10b981', confidence: 99.0, ruleUsed: 'Fallback' };
        }

        // -------------------------------------------------------------
        // CICLO DE SIMULACIÓN Y ACTUALIZACIÓN EN VIVO
        // -------------------------------------------------------------
        function tick() {
            const features = generateTelemetryVector();
            processVector(features);
        }

        function processVector(features) {
            const scenario = scenarioSelect.value;
            const pred = runModelInference(features, scenario);

            // Actualizar métricas visuales del vector
            featTotSize.innerText = features.totSize.toFixed(1);
            featSyn.innerText = features.syn.toFixed(1);
            featRate.innerText = features.rate >= 1000 ? Math.round(features.rate).toLocaleString() : features.rate.toFixed(2);
            featProto.innerText = features.proto;
            protoName.innerText = features.proto === 6 ? '(TCP)' : '(UDP)';
            featVar.innerText = features.variance.toFixed(3);
            featAck.innerText = features.ack.toFixed(1);

            // Actualizar Explicabilidad
            if (features.totSize <= 67.0) {
                traceStep1.innerHTML = '1. Tamaño de paquete <span class="text-amber-400 font-bold">' + features.totSize + 'B &le; 67.0B</span> &rarr; <span class="text-red-400">Patrón de Ataque Detectado</span> (Atajo sintético)';
            } else {
                traceStep1.innerHTML = '1. Tamaño de paquete <span class="text-emerald-400 font-bold">' + features.totSize + 'B &gt; 67.0B</span> &rarr; Tráfico con carga útil';
            }

            if (features.syn > 0.5) {
                traceStep2.innerHTML = '2. Bandera SYN activa <span class="text-amber-400 font-bold">syn_flag = 1.0</span> &rarr; Vector DDoS SYN';
            } else if (features.proto === 17 || features.rate > 1000) {
                traceStep2.innerHTML = '2. Protocolo UDP (17) y alta tasa <span class="text-red-400 font-bold">' + features.rate + ' pkts/s</span> &rarr; Vector DDoS UDP';
            } else {
                traceStep2.innerHTML = '2. Banderas regulares <span class="text-emerald-400 font-bold">ACK=1.0</span>, Varianza=' + features.variance + ' &rarr; Sesión Benigna';
            }

            traceConclusion.innerText = 'Resultado [' + scenarioSelect.options[scenarioSelect.selectedIndex].text.split(' ')[1] + ']: ' + pred.predLabel + ' (' + pred.confidence + '% conf.) — ' + pred.ruleUsed;
            traceConclusion.style.color = pred.color;

            // Actualizar gráfico de telemetría en vivo
            liveChart.data.datasets[0].data.push(features.rate);
            liveChart.data.datasets[0].data.shift();
            liveChart.data.datasets[0].borderColor = pred.color;
            liveChart.data.datasets[0].backgroundColor = pred.isAttack ? pred.color + '22' : 'rgba(6, 182, 212, 0.08)';
            liveChart.update();

            // Actualizar Banner de Estado Principal
            if (pred.isAttack) {
                const isSyn = pred.attackType === 'SYN';
                statusBadge.className = 'flex items-center space-x-2 px-4 py-1.5 rounded-full border text-xs font-semibold tracking-wide transition-all duration-300 ' + (isSyn ? 'border-amber-500 text-amber-400 alert-syn' : 'border-red-500 text-red-400 alert-udp');
                statusText.innerText = '¡ALERTA SOC: ' + pred.predLabel.toUpperCase() + '!';
                trafficStateBadge.innerText = 'Ataque en Curso: ' + pred.predLabel;
                trafficStateBadge.className = 'px-2.5 py-1 text-xs rounded-full font-semibold border ' + (isSyn ? 'bg-amber-500/10 text-amber-400 border-amber-500/30' : 'bg-red-500/10 text-red-400 border-red-500/30');

                addSocLog('[INTRUSIÓN ML] Alerta crítica: ' + pred.predLabel + ' detectada (Tot size=' + features.totSize + 'B, Rate=' + features.rate + ' pkts/s, Proto=' + features.proto + ')', 'alert');
                playAlertBeep(isSyn ? 520 : 750, 0.2);
            } else if (pred.isMisclassifiedAttack) {
                statusBadge.className = "flex items-center space-x-2 px-4 py-1.5 rounded-full border border-red-500/80 bg-red-950/60 text-red-300 text-xs font-semibold tracking-wide animate-pulse";
                statusText.innerText = "¡FALLO DE GENERALIZACIÓN! ATAQUE NO DETECTADO";
                trafficStateBadge.innerText = "Vulnerabilidad de Modelo";
                trafficStateBadge.className = "px-2.5 py-1 text-xs rounded-full font-semibold border bg-red-500/20 text-red-400 border-red-500/40";

                addSocLog('[FALLO CRÍTICO] Ataque omitido: Flujo malicioso clasificado como Benigno debido a limitaciones del escenario (' + scenario + ').', 'alert');
                playAlertBeep(330, 0.35);
            } else {
                statusBadge.className = "flex items-center space-x-2 px-4 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-semibold tracking-wide transition-all duration-300";
                statusText.innerText = "TRÁFICO BENIGNO SALUDABLE";
                trafficStateBadge.innerText = "Tráfico Normal Regular";
                trafficStateBadge.className = "px-2.5 py-1 text-xs rounded-full font-semibold border bg-emerald-500/10 text-emerald-400 border-emerald-500/30";

                if (Math.random() < 0.25) {
                    addSocLog('[INFO TELEMETRÍA] Sensor IoMT normal verificado. Rate=' + features.rate + ' pkts/s, Tot size=' + features.totSize + 'B.', 'info');
                }
            }
        }

        function addSocLog(msg, type = 'info') {
            const time = new Date().toLocaleTimeString();
            const el = document.createElement('div');
            if (type === 'alert') {
                el.className = 'text-red-400 font-semibold';
            } else {
                el.className = 'text-slate-400';
            }
            el.innerText = '[' + time + '] ' + msg;
            socLogContainer.appendChild(el);
            socLogContainer.scrollTop = socLogContainer.scrollHeight;
        }

        function clearSocLogs() {
            socLogContainer.innerHTML = '<div class="text-slate-500">[SISTEMA SOC] Registro depurado por el analista.</div>';
        }

        function injectPreset(type) {
            let vec;
            if (type === 'benign') vec = createVectorByType('BENIGN');
            else if (type === 'ddos_syn') vec = createVectorByType('DDOS_SYN');
            else if (type === 'ddos_udp') vec = createVectorByType('DDOS_UDP');
            else if (type === 'enterprise') vec = createVectorByType('ENTERPRISE');

            addSocLog('[INYECCIÓN MANUAL] Inyectando caso de estudio: ' + type.toUpperCase(), 'info');
            processVector(vec);
        }

        // Controladores de eventos de la simulación
        toggleSimBtn.addEventListener('click', () => {
            isSimRunning = !isSimRunning;
            if (isSimRunning) {
                simBtnLabel.innerText = 'Pausar';
                playIcon.setAttribute('data-lucide', 'pause');
                simTimer = setInterval(tick, simInterval);
                addSocLog('[SIMULADOR] Motor reanudado.', 'info');
            } else {
                simBtnLabel.innerText = 'Reanudar';
                playIcon.setAttribute('data-lucide', 'play');
                clearInterval(simTimer);
                addSocLog('[SIMULADOR] Motor en pausa por el operador.', 'info');
            }
            lucide.createIcons();
        });

        speedRange.addEventListener('input', (e) => {
            simInterval = parseInt(e.target.value);
            speedLabel.innerText = (simInterval / 1000).toFixed(1) + 's';
            if (isSimRunning) {
                clearInterval(simTimer);
                simTimer = setInterval(tick, simInterval);
            }
        });

        document.getElementById('sound-toggle-btn').addEventListener('click', () => {
            soundAlertEnabled = !soundAlertEnabled;
            const icon = document.getElementById('sound-icon');
            const label = document.getElementById('sound-label');
            if (soundAlertEnabled) {
                icon.setAttribute('data-lucide', 'volume-2');
                icon.className = 'w-3.5 h-3.5 text-cyan-400';
                label.innerText = 'Sonido ON';
                playAlertBeep(440, 0.1);
            } else {
                icon.setAttribute('data-lucide', 'volume-x');
                icon.className = 'w-3.5 h-3.5 text-slate-500';
                label.innerText = 'Sonido OFF';
            }
            lucide.createIcons();
        });

        // -------------------------------------------------------------
        // NAVEGACIÓN ENTRE PESTAÑAS
        // -------------------------------------------------------------
        function switchTab(tabId) {
            ['monitor', 'benchmarks', 'generalizacion', 'explicabilidad', 'figuras'].forEach(t => {
                const view = document.getElementById('view-' + t);
                const btn = document.getElementById('tab-btn-' + t);
                if (t === tabId) {
                    view.classList.remove('hidden');
                    btn.classList.add('active');
                } else {
                    view.classList.add('hidden');
                    btn.classList.remove('active');
                }
            });

            if (tabId === 'benchmarks') initBenchmarkCharts();
            if (tabId === 'generalizacion') initAblationChart();
            if (tabId === 'explicabilidad') initImportanceChart();
        }

        // -------------------------------------------------------------
        // PESTAÑA 2: BENCHMARKS & MODELOS (DATOS CSV)
        // -------------------------------------------------------------
        let currentBenchView = 'binaria';
        let benchmarkChartInstance = null;

        function renderBenchmarkView(view) {
            currentBenchView = view;
            const btnBin = document.getElementById('btn-bench-binaria');
            const btnMulti = document.getElementById('btn-bench-multi');

            if (view === 'binaria') {
                btnBin.className = 'px-3 py-1.5 rounded-lg text-xs font-medium bg-emerald-600 text-white transition shadow';
                btnMulti.className = 'px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-800 text-slate-300 hover:bg-slate-700 transition';
            } else {
                btnMulti.className = 'px-3 py-1.5 rounded-lg text-xs font-medium bg-emerald-600 text-white transition shadow';
                btnBin.className = 'px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-800 text-slate-300 hover:bg-slate-700 transition';
            }

            const dataKey = view === 'binaria' ? 'comparacion_binaria_prueba_oficial' : 'comparacion_multiclase_prueba_oficial';
            const rows = NOTEBOOK_DATA[dataKey] || [];

            // Renderizar encabezados
            const headersRow = document.getElementById('benchmark-table-headers');
            headersRow.innerHTML = '';
            if (rows.length > 0) {
                Object.keys(rows[0]).forEach(k => {
                    const th = document.createElement('th');
                    th.className = 'p-3';
                    th.innerText = k;
                    headersRow.appendChild(th);
                });
            }

            // Renderizar filas
            const tbody = document.getElementById('benchmark-table-body');
            tbody.innerHTML = '';
            rows.forEach(r => {
                const tr = document.createElement('tr');
                tr.className = 'hover:bg-slate-800/40 transition';
                Object.entries(r).forEach(([k, v]) => {
                    const td = document.createElement('td');
                    td.className = 'p-3';
                    if (k === 'Modelo') {
                        td.className += ' font-bold text-white';
                        td.innerText = v;
                    } else {
                        const num = parseFloat(v);
                        if (!isNaN(num) && v.includes('.')) {
                            td.innerText = num.toFixed(4);
                            if (k.includes('F1') || k.includes('Accuracy')) {
                                td.className += num > 0.99 ? ' text-emerald-400 font-bold' : (num < 0.6 ? ' text-red-400' : ' text-slate-200');
                            }
                        } else {
                            td.innerText = v;
                        }
                    }
                    tr.appendChild(td);
                });
                tbody.appendChild(tr);
            });

            updateBenchmarkChart(rows);
        }

        function initBenchmarkCharts() {
            renderBenchmarkView(currentBenchView);
            renderHyperparamsTable();
        }

        function updateBenchmarkChart(rows) {
            const ctx = document.getElementById('benchmarkChart').getContext('2d');
            const labels = rows.map(r => r.Modelo);
            const f1Values = rows.map(r => parseFloat(r['F1 macro']) || 0);

            if (benchmarkChartInstance) {
                benchmarkChartInstance.destroy();
            }

            benchmarkChartInstance = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [
                        {
                            label: 'F1 Macro (Prueba Oficial)',
                            data: f1Values,
                            backgroundColor: f1Values.map(v => v > 0.995 ? '#10b981' : (v < 0.6 ? '#ef4444' : '#0ea5e9')),
                            borderRadius: 6,
                            borderWidth: 0
                        }
                    ]
                },
                options: {
                    indexAxis: 'y',
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: {
                            min: 0,
                            max: 1.05,
                            grid: { color: 'rgba(51, 65, 85, 0.4)' },
                            ticks: { color: '#94a3b8', font: { family: 'monospace' } }
                        },
                        y: {
                            grid: { display: false },
                            ticks: { color: '#e2e8f0', font: { weight: '600' } }
                        }
                    },
                    plugins: {
                        legend: { display: false }
                    }
                }
            });
        }

        function renderHyperparamsTable() {
            const rows = NOTEBOOK_DATA['busqueda_hiperparametros'] || [];
            const tbody = document.getElementById('hyperparam-table-body');
            tbody.innerHTML = '';
            rows.forEach(r => {
                const tr = document.createElement('tr');
                tr.className = 'hover:bg-slate-800/40 transition';
                tr.innerHTML = `
                    <td class="p-3 uppercase text-[10px] text-slate-400 font-bold">${r.Tarea}</td>
                    <td class="p-3 text-cyan-400 font-bold">${r.Modelo}</td>
                    <td class="p-3 text-slate-300 text-[10px] font-mono">${r['Mejores hiperparámetros']}</td>
                    <td class="p-3 text-emerald-400 font-bold">${(parseFloat(r['F1 macro CV']) || 0).toFixed(4)}</td>
                    <td class="p-3 text-slate-400">${(parseFloat(r['Segundos de entrenamiento']) || 0).toFixed(2)}s</td>
                `;
                tbody.appendChild(tr);
            });
        }

        // -------------------------------------------------------------
        // PESTAÑA 3: GENERALIZACIÓN CRUZADA & ABLACIÓN (CHART)
        // -------------------------------------------------------------
        let ablationChartInstance = null;
        function initAblationChart() {
            if (ablationChartInstance) return;
            const ctx = document.getElementById('ablationChart').getContext('2d');

            const variants = ['A. Original', 'B. Longitud alineada', 'C. B sin SYN/ACK', 'D. C sin tasa', 'E. C + normalización'];
            const crossedData = [0.245, 0.398, 0.480, 0.450, 0.336];
            const sameDomainData = [0.997, 0.997, 0.987, 0.992, 0.864];

            ablationChartInstance = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: variants,
                    datasets: [
                        {
                            label: 'F1 Macro Dominio Cruzado',
                            data: crossedData,
                            backgroundColor: '#38bdf8',
                            borderRadius: 6
                        },
                        {
                            label: 'F1 Macro Mismo Dominio',
                            data: sameDomainData,
                            backgroundColor: '#f97316',
                            borderRadius: 6
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            min: 0,
                            max: 1.05,
                            grid: { color: 'rgba(51, 65, 85, 0.4)' },
                            ticks: { color: '#94a3b8', font: { family: 'monospace' } }
                        },
                        x: {
                            grid: { display: false },
                            ticks: { color: '#cbd5e1', font: { size: 10 } }
                        }
                    },
                    plugins: {
                        legend: {
                            labels: { color: '#e2e8f0', font: { size: 11 } }
                        }
                    }
                }
            });
        }

        // -------------------------------------------------------------
        // PESTAÑA 4: EXPLICABILIDAD & ESTABILIDAD (CHART & TABLA)
        // -------------------------------------------------------------
        let importanceChartInstance = null;
        function initImportanceChart() {
            renderStabilityTable();
            if (importanceChartInstance) return;

            const ctx = document.getElementById('importanceChart').getContext('2d');
            const topVars = [
                { name: 'Variance', imp: 0.00060 },
                { name: 'Rate', imp: 0.00032 },
                { name: 'syn_flag_number', imp: 0.00016 },
                { name: 'Tot sum', imp: 0.00011 },
                { name: 'Header_Length', imp: 0.00009 },
                { name: 'Protocol Type', imp: 0.00007 },
                { name: 'HTTPS', imp: 0.00005 },
                { name: 'ARP', imp: 0.00005 },
                { name: 'Tot size', imp: 0.00005 },
                { name: 'Covariance', imp: 0.00005 },
                { name: 'ack_flag_number', imp: 0.00005 },
                { name: 'Duration', imp: 0.00005 }
            ];

            importanceChartInstance = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: topVars.map(v => v.name),
                    datasets: [
                        {
                            label: 'Caída de F1 Macro al Permutar',
                            data: topVars.map(v => v.imp),
                            backgroundColor: '#fbbf24',
                            borderRadius: 4
                        }
                    ]
                },
                options: {
                    indexAxis: 'y',
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: {
                            grid: { color: 'rgba(51, 65, 85, 0.4)' },
                            ticks: { color: '#94a3b8', font: { family: 'monospace' } }
                        },
                        y: {
                            grid: { display: false },
                            ticks: { color: '#cbd5e1', font: { family: 'monospace', size: 10 } }
                        }
                    },
                    plugins: {
                        legend: { display: false }
                    }
                }
            });
        }

        function renderStabilityTable() {
            const filter = document.getElementById('stability-filter').value;
            const rows = NOTEBOOK_DATA['estabilidad_variables_iomt'] || [];
            const tbody = document.getElementById('stability-table-body');
            tbody.innerHTML = '';

            let filtered = rows;
            if (filter === 'stable') {
                filtered = rows.filter(r => parseFloat(r['KS medio']) < 0.05);
            } else if (filter === 'drift') {
                filtered = rows.filter(r => parseFloat(r['KS medio']) >= 0.05);
            }

            filtered.forEach(r => {
                const ks = parseFloat(r['KS medio']) || 0;
                const psi = parseFloat(r['PSI medio']) || 0;
                const imp = parseFloat(r['Importancia']) || 0;

                let diagnosisBadge = '';
                if (ks < 0.02 && psi < 0.05) {
                    diagnosisBadge = '<span class="text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded text-[10px]">Ultra Estable (Ideal)</span>';
                } else if (ks > 0.15 || psi > 0.25) {
                    diagnosisBadge = '<span class="text-red-400 bg-red-950 px-2 py-0.5 rounded text-[10px]">Deriva Alta (Riesgo)</span>';
                } else {
                    diagnosisBadge = '<span class="text-amber-400 bg-amber-950 px-2 py-0.5 rounded text-[10px]">Deriva Moderada</span>';
                }

                const tr = document.createElement('tr');
                tr.className = 'hover:bg-slate-800/40 transition';
                tr.innerHTML = `
                    <td class="p-3 text-cyan-300 font-bold">${r.Variable}</td>
                    <td class="p-3 text-slate-300 font-mono">${ks.toFixed(4)}</td>
                    <td class="p-3 text-slate-400 font-mono">${(parseFloat(r['KS máximo']) || 0).toFixed(4)}</td>
                    <td class="p-3 text-slate-300 font-mono">${psi.toFixed(4)}</td>
                    <td class="p-3 text-amber-300 font-mono">${imp.toFixed(6)}</td>
                    <td class="p-3">${diagnosisBadge}</td>
                `;
                tbody.appendChild(tr);
            });
        }

        // -------------------------------------------------------------
        // PESTAÑA 5: GALERÍA DE FIGURAS OFICIALES
        // -------------------------------------------------------------
        const FIGURES_CATALOG = [
            {
                id: '01_fig01',
                stage: '01_eda',
                title: 'Distribución de Clases en Particiones (Train vs Test)',
                path: '../deliverables/figuras/01_fig01.png',
                caption: 'Muestra el desbalance severo en la prueba oficial: mientras entrenamiento está balanceado (~33% cada clase), la prueba oficial contiene un 9% de benigno y un 91% de ataques DDoS.'
            },
            {
                id: '01_fig02',
                stage: '01_eda',
                title: 'Banderas TCP y Protocolos por Clase',
                path: '../deliverables/figuras/01_fig02.png',
                caption: 'Mapa de calor mostrando el poder de separación: DDoS UDP tiene 100% protocolo UDP y banderas 0; DDoS SYN tiene 87% de bandera SYN activa y 100% TCP.'
            },
            {
                id: '01_fig03',
                stage: '01_eda',
                title: 'Distribución de Variables Clave por Clase',
                path: '../deliverables/figuras/01_fig03.png',
                caption: 'Distribución log(1+x) de Header_Length, Rate, Tot size, Std, Variance e IAT. Evidencia cómo los ataques tienen varianza nula y tamaños de trama estrictamente fijos (54B y 50B).'
            },
            {
                id: '01_fig04',
                stage: '01_eda',
                title: 'Matriz de Correlación de Pearson',
                path: '../deliverables/figuras/01_fig04.png',
                caption: 'Matriz de correlación absoluta usada para descartar variables colineales (>0.98), eliminando redundancias como Srate con Rate, y TCP/UDP con Protocol Type.'
            },
            {
                id: '02_fig01',
                stage: '02_fe',
                title: 'Poder Discriminante Individual (Exactitud Balanceada)',
                path: '../deliverables/figuras/02_fig01.png',
                caption: 'Evaluación de variables usadas individualmente: AVG (99.26%), Tot size (99.15%), Max (98.61%), Tot sum (98.04%) y Min (97.56%) lideran la capacidad de separación.'
            },
            {
                id: '03_fig01',
                stage: '03_base',
                title: 'Prueba Oficial: Matriz de Confusión Binaria (V1 vs V2)',
                path: '../deliverables/figuras/03_fig01.png',
                caption: 'Evidencia del sesgo de variantes: el modelo V1 (entrenado solo con SYN) falla catastróficamente ante UDP flood dejando 206.141 ataques sin detectar.'
            },
            {
                id: '03_fig02',
                stage: '03_base',
                title: 'Prueba Oficial: Matriz de Confusión Multiclase (Línea Base)',
                path: '../deliverables/figuras/03_fig02.png',
                caption: 'Comparación de Regresión Logística frente al Árbol de Decisión: ambos modelos superan el 99.8% de precisión cuando se entrenan con ambas variantes de DDoS.'
            },
            {
                id: '03_fig03',
                stage: '03_base',
                title: 'Variables Utilizadas por el Árbol Multiclase',
                path: '../deliverables/figuras/03_fig03.png',
                caption: 'Importancia interna del árbol con profundidad 4: Tot size (49.6%) y syn_flag_number (48.96%) dominan casi la totalidad de las decisiones del modelo.'
            },
            {
                id: '04_fig01',
                stage: '04_final',
                title: 'Comparativa de Modelos Finales: F1 Macro',
                path: '../deliverables/figuras/04_fig01.png',
                caption: 'Rendimiento comparativo en prueba oficial: LightGBM y XGBoost superan a los modelos lineales y a Random Forest con F1 Macro > 0.997 y 0 falsas alarmas.'
            },
            {
                id: '04_fig02',
                stage: '04_final',
                title: 'Matriz de Confusión del Mejor Modelo (LightGBM)',
                path: '../deliverables/figuras/04_fig02.png',
                caption: 'Desempeño del mejor ensamble (LightGBM): 1.000 recall en benigno (0 falsos positivos sobre 37.607 flujos) y 0.998 en DDoS SYN y 1.000 en DDoS UDP.'
            },
            {
                id: '04_fig03',
                stage: '04_final',
                title: 'Importancia por Permutación (LightGBM)',
                path: '../deliverables/figuras/04_fig03.png',
                caption: 'Explicabilidad independiente del algoritmo: Variance y Rate encabezan el impacto en la predicción, mostrando que el boosting aprende a identificar la regularidad artificial del ataque.'
            },
            {
                id: '04_fig04',
                stage: '04_final',
                title: 'Importancia vs Estabilidad de Variables (KS Medio)',
                path: '../deliverables/figuras/04_fig04.png',
                caption: 'Prueba de robustez conceptual: identifica qué variables tienen alto poder predictivo pero baja deriva temporal entre Train y Test.'
            },
            {
                id: '04_fig05',
                stage: '04_final',
                title: 'Estudio de Ablación de la Homologación',
                path: '../deliverables/figuras/04_fig05.png',
                caption: 'Impacto de corregir las discrepancias de extractores: alinear longitud de cabeceras (+34B) y eliminar banderas SYN/ACK corruptas recupera el F1 cruzado de 0.245 a 0.480.'
            },
            {
                id: '04_fig06',
                stage: '04_final',
                title: 'Degradación Cruzada (Mismo Dominio vs Cruzado)',
                path: '../deliverables/figuras/04_fig06.png',
                caption: 'Visualización de la severa pérdida de generalización al transferir modelos entrenados en red tradicional hacia entornos médicos IoMT (-63.5%).'
            },
            {
                id: '04_fig07',
                stage: '04_final',
                title: 'Matrices de Confusión Cruzadas (IoMT ↔ Tradicional)',
                path: '../deliverables/figuras/04_fig07.png',
                caption: 'Detalle del colapso cruzado: el modelo tradicional clasifica erróneamente el 97.2% de los ataques DDoS UDP en IoMT como Benignos.'
            },
            {
                id: '04_fig08',
                stage: '04_final',
                title: 'Cambio de Distribución entre IoMT y Red Tradicional',
                path: '../deliverables/figuras/04_fig08.png',
                caption: 'Estadística KS de variables comunes entre CICIoMT2024 y CIC-DDoS2019, evidenciando las enormes diferencias en tasas y longitudes por extractor.'
            }
        ];

        function renderGallery(filter = 'all') {
            const grid = document.getElementById('gallery-grid');
            grid.innerHTML = '';

            const filtered = filter === 'all' ? FIGURES_CATALOG : FIGURES_CATALOG.filter(f => f.stage === filter);

            filtered.forEach(fig => {
                const card = document.createElement('div');
                card.className = 'bg-slate-950 border border-slate-800 rounded-xl overflow-hidden hover:border-slate-700 transition flex flex-col justify-between group shadow-md';
                card.innerHTML = `
                    <div class="relative overflow-hidden cursor-pointer bg-slate-900 aspect-video flex items-center justify-center p-2" onclick="openImageModal('${fig.title}', '${fig.path}', '${fig.caption}')">
                        <img src="${fig.path}" alt="${fig.title}" class="max-h-full max-w-full object-contain group-hover:scale-105 transition duration-300">
                        <div class="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition flex items-center justify-center">
                            <span class="px-3 py-1.5 bg-slate-900/90 text-cyan-400 rounded-lg text-xs font-semibold flex items-center gap-1.5 shadow">
                                <i data-lucide="zoom-in" class="w-4 h-4"></i> Ampliar
                            </span>
                        </div>
                    </div>
                    <div class="p-4 border-t border-slate-800/80 flex-1 flex flex-col justify-between">
                        <div>
                            <div class="flex items-center justify-between mb-1">
                                <span class="text-[10px] uppercase font-mono text-cyan-400 font-semibold">${fig.id}</span>
                                <span class="text-[9px] uppercase px-1.5 py-0.5 rounded bg-slate-800 text-slate-400">${fig.stage}</span>
                            </div>
                            <h4 class="text-xs font-bold text-white mb-1.5 line-clamp-1">${fig.title}</h4>
                            <p class="text-[11px] text-slate-400 line-clamp-3 leading-relaxed">${fig.caption}</p>
                        </div>
                    </div>
                `;
                grid.appendChild(card);
            });

            lucide.createIcons();
        }

        function filterGallery(stage) {
            document.querySelectorAll('.gallery-filter-btn').forEach(b => b.classList.remove('active-filter', 'bg-cyan-600', 'text-white'));
            renderGallery(stage);
        }

        function openImageModal(title, path, caption) {
            document.getElementById('modal-title').innerText = title;
            document.getElementById('modal-img').src = path;
            document.getElementById('modal-caption').innerText = caption;
            document.getElementById('image-modal').classList.remove('hidden');
        }

        function closeImageModal() {
            document.getElementById('image-modal').classList.add('hidden');
        }

        // Inicializar vistas y simulación al cargar
        document.addEventListener('DOMContentLoaded', () => {
            renderGallery('all');
            simTimer = setInterval(tick, simInterval);
            addSocLog('[INICIALIZACIÓN] Aplicación vinculada exitosamente con deliverables y figuras de notebooks.', 'info');
        });
    </script>
</body>
</html>
"""

final_html = html_template.replace("%DATA_PLACEHOLDER%", json_data_str)

output_path = Path("app/app.html")
output_path.write_text(final_html, encoding="utf-8")
print(f"app/app.html generado exitosamente. Tamaño: {len(final_html):,} bytes.")
