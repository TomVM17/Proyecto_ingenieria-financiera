"""
Aplicativo Web de Tabla de Amortización con Streamlit
Interfaz moderna y visual para el proyecto de Ingeniería Financiera
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
import io
import base64

# Importar nuestras clases del proyecto
from proyecto import (
    ConversionTasas, CalculadoraAmortizacion, ManejoAbonos, 
    ExportadorDatos, ValidadorDatos
)

# Configuración de la página
st.set_page_config(
    page_title="Tabla de Amortización - Ingeniería Financiera",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado para mejorar la apariencia
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: bold;
    }
    .metric-container {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .stAlert {
        margin: 1rem 0;
    }
    .success-metric {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

class AplicativoWeb:
    """
    Clase principal para la aplicación web de Streamlit
    """
    
    def __init__(self):
        """
        Inicializa la aplicación web
        """
        if 'calculadora' not in st.session_state:
            st.session_state.calculadora = None
        if 'manejo_abonos' not in st.session_state:
            st.session_state.manejo_abonos = None
        if 'datos_credito' not in st.session_state:
            st.session_state.datos_credito = {}
        if 'tabla_basica' not in st.session_state:
            st.session_state.tabla_basica = None
        if 'tabla_con_abonos' not in st.session_state:
            st.session_state.tabla_con_abonos = None
    
    def mostrar_header(self):
        """
        Muestra el encabezado principal de la aplicación
        """
        st.markdown('<h1 class="main-header">🏦 Aplicativo de Tabla de Amortización</h1>', 
                   unsafe_allow_html=True)
        st.markdown("### 📚 Proyecto de Ingeniería Financiera")
        st.markdown("---")
    
    def sidebar_configuracion_credito(self):
        """
        Sidebar para configurar los parámetros del crédito
        """
        st.sidebar.header("🔧 Configuración del Crédito")
        
        with st.sidebar.form("configuracion_credito"):
            st.subheader("Parámetros Principales")
            
            # Monto del crédito
            monto = st.number_input(
                "💰 Monto del Crédito ($)",
                min_value=1.0,
                value=100000.0,
                step=1000.0,
                format="%.2f",
                help="Ingrese cualquier monto de crédito (sin límite máximo)"
            )
            
            # Configuración de tasa
            st.subheader("📊 Configuración de Tasa")
            
            col1, col2 = st.columns(2)
            with col1:
                tipo_tasa = st.selectbox(
                    "Tipo de Tasa",
                    ["Nominal", "Efectiva"],
                    help="Seleccione si la tasa ingresada es nominal o efectiva"
                )
            
            with col2:
                modalidad = st.selectbox(
                    "Modalidad",
                    ["Vencida", "Anticipada"],
                    help="Seleccione si la tasa es vencida o anticipada"
                )
            
            tasa_anual = st.number_input(
                "📈 Tasa Anual (%)",
                min_value=0.1,
                max_value=100.0,
                value=12.0,
                step=0.1,
                format="%.2f"
            ) / 100
            
            # Frecuencia de pago
            st.subheader("📅 Frecuencia de Pago")
            frecuencia_dict = {
                "Mensual": 12,
                "Bimestral": 6,
                "Trimestral": 4,
                "Semestral": 2,
                "Anual": 1
            }
            
            frecuencia_texto = st.selectbox(
                "Frecuencia",
                list(frecuencia_dict.keys()),
                help="Frecuencia de los pagos"
            )
            frecuencia = frecuencia_dict[frecuencia_texto]
            
            # Plazo
            num_pagos = st.number_input(
                "📆 Número de Pagos",
                min_value=1,
                max_value=600,
                value=24,
                step=1,
                help="Número total de pagos del crédito"
            )
            
            # Fecha de inicio
            fecha_inicio = st.date_input(
                "📅 Fecha de Inicio",
                value=datetime.now().date(),
                help="Fecha de inicio del crédito"
            )
            
            submitted = st.form_submit_button("✅ Configurar Crédito", type="primary")
            
            if submitted:
                try:
                    # Procesar tasa
                    tasa_procesada = self.procesar_tasa(tasa_anual, tipo_tasa, modalidad, frecuencia)
                    
                    # Crear calculadora
                    fecha_inicio_dt = datetime.combine(fecha_inicio, datetime.min.time())
                    st.session_state.calculadora = CalculadoraAmortizacion(
                        monto=monto,
                        tasa_periodo=tasa_procesada,
                        num_pagos=num_pagos,
                        fecha_inicio=fecha_inicio_dt
                    )
                    
                    st.session_state.manejo_abonos = ManejoAbonos(st.session_state.calculadora)
                    
                    # Guardar datos para mostrar
                    st.session_state.datos_credito = {
                        'monto': monto,
                        'tasa_anual_original': tasa_anual * 100,
                        'tipo_tasa': tipo_tasa,
                        'modalidad': modalidad,
                        'frecuencia': frecuencia,
                        'frecuencia_texto': frecuencia_texto,
                        'num_pagos': num_pagos,
                        'fecha_inicio': fecha_inicio_dt.strftime('%Y-%m-%d'),
                        'tasa_periodo': tasa_procesada * 100,
                        'cuota_fija': st.session_state.calculadora.cuota_fija
                    }
                    
                    st.session_state.tabla_basica = None
                    st.session_state.tabla_con_abonos = None
                    
                    st.sidebar.success("✅ Crédito configurado exitosamente!")
                    
                except Exception as e:
                    st.sidebar.error(f"❌ Error: {str(e)}")
    
    def procesar_tasa(self, tasa_anual, tipo_tasa, modalidad, frecuencia):
        """
        Procesa la tasa según el tipo y modalidad
        """
        # Convertir a efectiva si es nominal
        if tipo_tasa == "Nominal":
            tasa_efectiva = ConversionTasas.nominal_a_efectiva(tasa_anual, frecuencia)
        else:
            tasa_efectiva = tasa_anual
        
        # Convertir de anticipada a vencida si es necesario
        if modalidad == "Anticipada":
            tasa_efectiva = ConversionTasas.anticipada_a_vencida(tasa_efectiva)
        
        # Calcular tasa por período
        tasa_periodo = ConversionTasas.tasa_equivalente(tasa_efectiva, 1, frecuencia)
        
        return tasa_periodo
    
    def mostrar_resumen_credito(self):
        """
        Muestra el resumen del crédito configurado
        """
        if st.session_state.datos_credito:
            st.subheader("📋 Resumen del Crédito Configurado")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    label="💰 Monto del Crédito",
                    value=f"${st.session_state.datos_credito['monto']:,.2f}"
                )
            
            with col2:
                st.metric(
                    label="📊 Tasa Original",
                    value=f"{st.session_state.datos_credito['tasa_anual_original']:.2f}%",
                    help=f"{st.session_state.datos_credito['tipo_tasa']} {st.session_state.datos_credito['modalidad']}"
                )
            
            with col3:
                st.metric(
                    label="📅 Frecuencia",
                    value=st.session_state.datos_credito['frecuencia_texto'],
                    help=f"{st.session_state.datos_credito['num_pagos']} pagos totales"
                )
            
            with col4:
                st.metric(
                    label="💳 Cuota Fija",
                    value=f"${st.session_state.datos_credito['cuota_fija']:,.2f}",
                    help=f"Tasa por período: {st.session_state.datos_credito['tasa_periodo']:.4f}%"
                )
    
    def configurar_abonos(self):
        """
        Sección para configurar abonos extras
        """
        if not st.session_state.calculadora:
            st.warning("⚠️ Primero debe configurar un crédito en la barra lateral")
            return
        
        st.subheader("💰 Configuración de Abonos Extras")
        
        tab1, tab2, tab3 = st.tabs(["🔄 Abonos Programados", "📅 Abonos Ad-hoc", "📋 Resumen"])
        
        with tab1:
            st.write("Configurar abonos que se aplican automáticamente cada cierto período")
            
            with st.form("abono_programado"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    periodo_inicio = st.number_input(
                        "Período de Inicio",
                        min_value=1,
                        max_value=st.session_state.datos_credito['num_pagos'],
                        value=6,
                        help="Período donde comienza el abono programado"
                    )
                
                with col2:
                    monto_abono = st.number_input(
                        "Monto del Abono ($)",
                        min_value=1.0,
                        value=1000.0,
                        step=100.0,
                        format="%.2f",
                        help="Cualquier monto de abono programado"
                    )
                
                with col3:
                    frecuencia_abono = st.number_input(
                        "Cada cuántos períodos",
                        min_value=1,
                        max_value=12,
                        value=6,
                        help="Frecuencia del abono programado"
                    )
                
                if st.form_submit_button("➕ Agregar Abono Programado"):
                    st.session_state.manejo_abonos.agregar_abono_programado(
                        periodo_inicio, monto_abono, frecuencia_abono
                    )
                    st.success(f"✅ Abono programado agregado: ${monto_abono:,.2f} cada {frecuencia_abono} período(s)")
        
        with tab2:
            st.write("Configurar abonos únicos en períodos específicos")
            
            with st.form("abono_adhoc"):
                col1, col2 = st.columns(2)
                
                with col1:
                    periodo_adhoc = st.number_input(
                        "Período del Abono",
                        min_value=1,
                        max_value=st.session_state.datos_credito['num_pagos'],
                        value=12,
                        help="Período específico donde se aplica el abono"
                    )
                
                with col2:
                    monto_adhoc = st.number_input(
                        "Monto del Abono ($)",
                        min_value=1.0,
                        value=5000.0,
                        step=100.0,
                        format="%.2f",
                        help="Cualquier monto de abono ad-hoc"
                    )
                
                if st.form_submit_button("➕ Agregar Abono Ad-hoc"):
                    st.session_state.manejo_abonos.agregar_abono_adhoc(periodo_adhoc, monto_adhoc)
                    st.success(f"✅ Abono ad-hoc agregado: ${monto_adhoc:,.2f} en período {periodo_adhoc}")
        
        with tab3:
            self.mostrar_abonos_configurados()
    
    def mostrar_abonos_configurados(self):
        """
        Muestra los abonos configurados
        """
        if not st.session_state.manejo_abonos:
            return
        
        st.write("**Abonos Configurados:**")
        
        if (not st.session_state.manejo_abonos.abonos_programados and 
            not st.session_state.manejo_abonos.abonos_adhoc):
            st.info("No hay abonos configurados")
            return
        
        if st.session_state.manejo_abonos.abonos_programados:
            st.write("**🔄 Abonos Programados:**")
            for i, abono in enumerate(st.session_state.manejo_abonos.abonos_programados, 1):
                st.write(f"   {i}. ${abono['monto']:,.2f} cada {abono['frecuencia']} período(s) desde período {abono['periodo_inicio']}")
        
        if st.session_state.manejo_abonos.abonos_adhoc:
            st.write("**📅 Abonos Ad-hoc:**")
            for i, abono in enumerate(st.session_state.manejo_abonos.abonos_adhoc, 1):
                st.write(f"   {i}. ${abono['monto']:,.2f} en período {abono['periodo']}")
    
    def generar_y_mostrar_tablas(self):
        """
        Genera y muestra las tablas de amortización
        """
        if not st.session_state.calculadora:
            st.warning("⚠️ Primero debe configurar un crédito")
            return
        
        st.subheader("📊 Tablas de Amortización")
        
        # Botones para generar tablas
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📋 Generar Tabla Básica", type="primary"):
                st.session_state.tabla_basica = st.session_state.calculadora.generar_tabla_basica()
        
        with col2:
            if st.button("💰 Generar Tabla con Abonos", type="primary"):
                if (st.session_state.manejo_abonos.abonos_programados or 
                    st.session_state.manejo_abonos.abonos_adhoc):
                    st.session_state.tabla_con_abonos = st.session_state.manejo_abonos.generar_tabla_con_abonos()
                else:
                    st.warning("⚠️ No hay abonos configurados. La tabla será igual a la básica.")
                    st.session_state.tabla_con_abonos = st.session_state.calculadora.generar_tabla_basica()
        
        # Mostrar tablas en tabs
        if st.session_state.tabla_basica is not None or st.session_state.tabla_con_abonos is not None:
            tab1, tab2, tab3 = st.tabs(["📋 Tabla Básica", "💰 Tabla con Abonos", "📊 Comparación"])
            
            with tab1:
                if st.session_state.tabla_basica is not None:
                    self.mostrar_tabla_interactiva(st.session_state.tabla_basica, "Básica")
                else:
                    st.info("👆 Haga clic en 'Generar Tabla Básica' para ver los resultados")
            
            with tab2:
                if st.session_state.tabla_con_abonos is not None:
                    self.mostrar_tabla_interactiva(st.session_state.tabla_con_abonos, "Con Abonos")
                else:
                    st.info("👆 Haga clic en 'Generar Tabla con Abonos' para ver los resultados")
            
            with tab3:
                self.mostrar_comparacion()
    
    def mostrar_tabla_interactiva(self, tabla, tipo):
        """
        Muestra una tabla de amortización con formato interactivo
        """
        st.write(f"**Tabla de Amortización {tipo}**")
        
        # Métricas resumen
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("🗓️ Períodos", len(tabla))
        with col2:
            st.metric("💰 Total Cuotas", f"${tabla['Cuota'].sum():,.2f}")
        with col3:
            st.metric("💸 Total Intereses", f"${tabla['Interés'].sum():,.2f}")
        with col4:
            if 'Abono_Extra' in tabla.columns:
                st.metric("💵 Total Abonos", f"${tabla['Abono_Extra'].sum():,.2f}")
        
        # Gráfico de evolución del saldo
        self.crear_grafico_saldo(tabla, tipo)
        
        # Tabla interactiva
        st.write("**Detalle de Pagos:**")
        
        # Opción para mostrar tabla completa o resumida
        mostrar_completa = st.checkbox(f"Mostrar tabla completa ({tipo})", value=False)
        
        if mostrar_completa:
            st.dataframe(
                tabla.style.format({
                    'Saldo_Inicial': '${:,.2f}',
                    'Cuota': '${:,.2f}',
                    'Interés': '${:,.2f}',
                    'Capital': '${:,.2f}',
                    'Abono_Extra': '${:,.2f}',
                    'Saldo_Final': '${:,.2f}'
                }),
                use_container_width=True
            )
        else:
            # Mostrar solo primeros y últimos períodos
            st.write("**Primeros 10 períodos:**")
            st.dataframe(
                tabla.head(10).style.format({
                    'Saldo_Inicial': '${:,.2f}',
                    'Cuota': '${:,.2f}',
                    'Interés': '${:,.2f}',
                    'Capital': '${:,.2f}',
                    'Abono_Extra': '${:,.2f}',
                    'Saldo_Final': '${:,.2f}'
                }),
                use_container_width=True
            )
            
            if len(tabla) > 10:
                st.write("**Últimos 5 períodos:**")
                st.dataframe(
                    tabla.tail(5).style.format({
                        'Saldo_Inicial': '${:,.2f}',
                        'Cuota': '${:,.2f}',
                        'Interés': '${:,.2f}',
                        'Capital': '${:,.2f}',
                        'Abono_Extra': '${:,.2f}',
                        'Saldo_Final': '${:,.2f}'
                    }),
                    use_container_width=True
                )
    
    def crear_grafico_saldo(self, tabla, tipo):
        """
        Crea gráfico de evolución del saldo
        """
        fig = go.Figure()
        
        # Línea de saldo
        fig.add_trace(go.Scatter(
            x=tabla['Período'],
            y=tabla['Saldo_Final'],
            mode='lines+markers',
            name='Saldo Pendiente',
            line=dict(color='#1f77b4', width=3),
            marker=dict(size=6)
        ))
        
        # Barras de cuota (si hay espacio)
        if len(tabla) <= 60:  # Solo mostrar barras si no hay muchos períodos
            fig.add_trace(go.Bar(
                x=tabla['Período'],
                y=tabla['Cuota'],
                name='Cuota',
                opacity=0.6,
                yaxis='y2'
            ))
        
        fig.update_layout(
            title=f'Evolución del Saldo - {tipo}',
            xaxis_title='Período',
            yaxis_title='Saldo Pendiente ($)',
            yaxis2=dict(
                title='Cuota ($)',
                overlaying='y',
                side='right'
            ),
            hovermode='x unified',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def mostrar_comparacion(self):
        """
        Muestra comparación entre tabla básica y con abonos
        """
        if st.session_state.tabla_basica is None or st.session_state.tabla_con_abonos is None:
            st.info("📊 Genere ambas tablas para ver la comparación")
            return
        
        st.write("**📊 Comparación de Resultados**")
        
        # Métricas de comparación
        tabla_basica = st.session_state.tabla_basica
        tabla_abonos = st.session_state.tabla_con_abonos
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            periodos_sin = len(tabla_basica)
            periodos_con = len(tabla_abonos)
            ahorro_tiempo = periodos_sin - periodos_con
            
            st.metric(
                "⏰ Ahorro en Tiempo",
                f"{ahorro_tiempo} períodos",
                delta=f"-{(ahorro_tiempo/periodos_sin)*100:.1f}%"
            )
        
        with col2:
            intereses_sin = tabla_basica['Interés'].sum()
            intereses_con = tabla_abonos['Interés'].sum()
            ahorro_intereses = intereses_sin - intereses_con
            
            st.metric(
                "💰 Ahorro en Intereses",
                f"${ahorro_intereses:,.2f}",
                delta=f"-{(ahorro_intereses/intereses_sin)*100:.1f}%"
            )
        
        with col3:
            total_abonos = tabla_abonos['Abono_Extra'].sum()
            roi = (ahorro_intereses / total_abonos) * 100 if total_abonos > 0 else 0
            
            st.metric(
                "📈 ROI de Abonos",
                f"{roi:.1f}%",
                help="Retorno sobre inversión de los abonos extras"
            )
        
        # Gráfico comparativo
        self.crear_grafico_comparativo(tabla_basica, tabla_abonos)
        
        # Tabla resumen
        st.write("**📋 Resumen Comparativo**")
        
        resumen_data = {
            'Concepto': [
                'Períodos Totales',
                'Total Cuotas',
                'Total Intereses',
                'Total Abonos',
                'Total Pagado'
            ],
            'Sin Abonos': [
                len(tabla_basica),
                f"${tabla_basica['Cuota'].sum():,.2f}",
                f"${tabla_basica['Interés'].sum():,.2f}",
                "$0.00",
                f"${tabla_basica['Cuota'].sum():,.2f}"
            ],
            'Con Abonos': [
                len(tabla_abonos),
                f"${tabla_abonos['Cuota'].sum():,.2f}",
                f"${tabla_abonos['Interés'].sum():,.2f}",
                f"${tabla_abonos['Abono_Extra'].sum():,.2f}",
                f"${tabla_abonos['Cuota'].sum() + tabla_abonos['Abono_Extra'].sum():,.2f}"
            ],
            'Diferencia': [
                f"{ahorro_tiempo} menos",
                f"${tabla_basica['Cuota'].sum() - tabla_abonos['Cuota'].sum():,.2f}",
                f"${ahorro_intereses:,.2f}",
                f"${tabla_abonos['Abono_Extra'].sum():,.2f}",
                f"${(tabla_basica['Cuota'].sum()) - (tabla_abonos['Cuota'].sum() + tabla_abonos['Abono_Extra'].sum()):,.2f}"
            ]
        }
        
        resumen_df = pd.DataFrame(resumen_data)
        st.dataframe(resumen_df, use_container_width=True)
    
    def crear_grafico_comparativo(self, tabla_basica, tabla_abonos):
        """
        Crea gráfico comparativo entre ambas tablas
        """
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Evolución del Saldo', 'Intereses por Período', 
                          'Capital vs Interés Acumulado', 'Distribución de Pagos'),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"type": "pie"}]]
        )
        
        # Gráfico 1: Evolución del saldo
        fig.add_trace(
            go.Scatter(x=tabla_basica['Período'], y=tabla_basica['Saldo_Final'],
                      name='Sin Abonos', line=dict(color='red', dash='dash')),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(x=tabla_abonos['Período'], y=tabla_abonos['Saldo_Final'],
                      name='Con Abonos', line=dict(color='green')),
            row=1, col=1
        )
        
        # Gráfico 2: Intereses por período (primeros 20 períodos)
        periodos_mostrar = min(20, len(tabla_basica), len(tabla_abonos))
        
        fig.add_trace(
            go.Bar(x=tabla_basica['Período'][:periodos_mostrar], 
                  y=tabla_basica['Interés'][:periodos_mostrar],
                  name='Intereses Sin Abonos', opacity=0.7),
            row=1, col=2
        )
        
        fig.add_trace(
            go.Bar(x=tabla_abonos['Período'][:periodos_mostrar], 
                  y=tabla_abonos['Interés'][:periodos_mostrar],
                  name='Intereses Con Abonos', opacity=0.7),
            row=1, col=2
        )
        
        # Gráfico 3: Capital vs Interés acumulado
        capital_acum_basica = tabla_basica['Capital'].cumsum()
        interes_acum_basica = tabla_basica['Interés'].cumsum()
        
        fig.add_trace(
            go.Scatter(x=tabla_basica['Período'], y=capital_acum_basica,
                      name='Capital Acum. Sin Abonos', line=dict(color='blue')),
            row=2, col=1
        )
        
        fig.add_trace(
            go.Scatter(x=tabla_basica['Período'], y=interes_acum_basica,
                      name='Interés Acum. Sin Abonos', line=dict(color='red')),
            row=2, col=1
        )
        
        # Gráfico 4: Distribución de pagos (pie chart)
        intereses_sin = tabla_basica['Interés'].sum()
        capital_total = tabla_basica['Capital'].sum()
        abonos_total = tabla_abonos['Abono_Extra'].sum()
        
        fig.add_trace(
            go.Pie(labels=['Capital', 'Intereses', 'Abonos Extra'],
                   values=[capital_total, tabla_abonos['Interés'].sum(), abonos_total],
                   name="Distribución"),
            row=2, col=2
        )
        
        fig.update_layout(height=800, showlegend=True, title_text="Análisis Comparativo Completo")
        st.plotly_chart(fig, use_container_width=True)
    
    def seccion_descargas(self):
        """
        Sección para descargar archivos
        """
        if (st.session_state.tabla_basica is None and 
            st.session_state.tabla_con_abonos is None):
            st.info("📥 Genere una tabla de amortización para habilitar las descargas")
            return
        
        st.subheader("📥 Descargar Resultados")
        
        # Descarga de reporte completo si hay ambas tablas
        if (st.session_state.tabla_basica is not None and 
            st.session_state.tabla_con_abonos is not None):
            
            st.write("**📊 Reporte Completo (Comparativo)**")
            col_reporte1, col_reporte2 = st.columns(2)
            
            with col_reporte1:
                # Reporte CSV completo
                csv_completo = self.generar_reporte_completo_csv()
                st.download_button(
                    label="📋 Descargar Reporte CSV Completo",
                    data=csv_completo,
                    file_name=f"reporte_completo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    help="Incluye tabla básica, con abonos y comparación"
                )
            
            with col_reporte2:
                # Reporte Excel completo
                excel_completo = self.generar_reporte_completo_excel()
                st.download_button(
                    label="📊 Descargar Reporte Excel Completo",
                    data=excel_completo,
                    file_name=f"reporte_completo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    help="Excel con múltiples hojas: tabla básica, con abonos, comparación y resumen"
                )
            
            st.markdown("---")
        
        # Descargas individuales
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**📋 Tabla Básica**")
            if st.session_state.tabla_basica is not None:
                # CSV
                csv_basica = self.convertir_a_csv(st.session_state.tabla_basica)
                st.download_button(
                    label="📄 Descargar CSV",
                    data=csv_basica,
                    file_name=f"tabla_basica_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
                
                # Excel
                excel_basica = self.convertir_a_excel(
                    st.session_state.tabla_basica, 
                    "Tabla Básica"
                )
                st.download_button(
                    label="📊 Descargar Excel",
                    data=excel_basica,
                    file_name=f"tabla_basica_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.info("Genere la tabla básica primero")
        
        with col2:
            st.write("**💰 Tabla con Abonos**")
            if st.session_state.tabla_con_abonos is not None:
                # CSV
                csv_abonos = self.convertir_a_csv(st.session_state.tabla_con_abonos)
                st.download_button(
                    label="📄 Descargar CSV",
                    data=csv_abonos,
                    file_name=f"tabla_con_abonos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
                
                # Excel
                excel_abonos = self.convertir_a_excel(
                    st.session_state.tabla_con_abonos, 
                    "Tabla con Abonos"
                )
                st.download_button(
                    label="📊 Descargar Excel",
                    data=excel_abonos,
                    file_name=f"tabla_con_abonos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.info("Genere la tabla con abonos primero")
    
    def convertir_a_csv(self, tabla):
        """
        Convierte tabla a CSV para descarga
        """
        output = io.StringIO()
        tabla.to_csv(output, index=False)
        return output.getvalue()
    
    def convertir_a_excel(self, tabla, nombre_hoja):
        """
        Convierte tabla a Excel para descarga
        """
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            tabla.to_excel(writer, sheet_name=nombre_hoja, index=False)
            
            # Agregar hoja de resumen si hay datos del crédito
            if st.session_state.datos_credito:
                resumen_data = {
                    'Concepto': [
                        'Monto del Crédito',
                        'Tasa Original',
                        'Tipo de Tasa',
                        'Modalidad',
                        'Frecuencia',
                        'Número de Pagos',
                        'Fecha de Inicio',
                        'Cuota Fija',
                        'Total Intereses',
                        'Total a Pagar'
                    ],
                    'Valor': [
                        f"${st.session_state.datos_credito['monto']:,.2f}",
                        f"{st.session_state.datos_credito['tasa_anual_original']:.2f}%",
                        st.session_state.datos_credito['tipo_tasa'],
                        st.session_state.datos_credito['modalidad'],
                        st.session_state.datos_credito['frecuencia_texto'],
                        st.session_state.datos_credito['num_pagos'],
                        st.session_state.datos_credito['fecha_inicio'],
                        f"${st.session_state.datos_credito['cuota_fija']:,.2f}",
                        f"${tabla['Interés'].sum():,.2f}",
                        f"${tabla['Cuota'].sum():,.2f}"
                    ]
                }
                
                resumen_df = pd.DataFrame(resumen_data)
                resumen_df.to_excel(writer, sheet_name='Resumen', index=False)
        
        return output.getvalue()
    
    def generar_reporte_completo_csv(self):
        """
        Genera un reporte CSV completo con ambas tablas y comparación
        """
        output = io.StringIO()
        
        # Encabezado del reporte
        output.write("REPORTE COMPLETO DE AMORTIZACIÓN\n")
        output.write("=" * 50 + "\n")
        output.write(f"Generado el: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Información del crédito
        if st.session_state.datos_credito:
            output.write("INFORMACIÓN DEL CRÉDITO\n")
            output.write("-" * 30 + "\n")
            output.write(f"Monto: ${st.session_state.datos_credito['monto']:,.2f}\n")
            output.write(f"Tasa: {st.session_state.datos_credito['tasa_anual_original']:.2f}% ({st.session_state.datos_credito['tipo_tasa']} {st.session_state.datos_credito['modalidad']})\n")
            output.write(f"Frecuencia: {st.session_state.datos_credito['frecuencia_texto']}\n")
            output.write(f"Plazo: {st.session_state.datos_credito['num_pagos']} pagos\n")
            output.write(f"Cuota Fija: ${st.session_state.datos_credito['cuota_fija']:,.2f}\n\n")
        
        # Resumen comparativo
        if (st.session_state.tabla_basica is not None and 
            st.session_state.tabla_con_abonos is not None):
            
            tabla_basica = st.session_state.tabla_basica
            tabla_abonos = st.session_state.tabla_con_abonos
            
            output.write("RESUMEN COMPARATIVO\n")
            output.write("-" * 30 + "\n")
            output.write(f"Sin abonos - Períodos: {len(tabla_basica)}, Intereses: ${tabla_basica['Interés'].sum():,.2f}\n")
            output.write(f"Con abonos - Períodos: {len(tabla_abonos)}, Intereses: ${tabla_abonos['Interés'].sum():,.2f}\n")
            output.write(f"Ahorro en intereses: ${tabla_basica['Interés'].sum() - tabla_abonos['Interés'].sum():,.2f}\n")
            output.write(f"Ahorro en tiempo: {len(tabla_basica) - len(tabla_abonos)} períodos\n\n")
        
        # Tabla básica
        output.write("TABLA BÁSICA\n")
        output.write("-" * 20 + "\n")
        if st.session_state.tabla_basica is not None:
            st.session_state.tabla_basica.to_csv(output, index=False)
        
        output.write("\n\nTABLA CON ABONOS\n")
        output.write("-" * 20 + "\n")
        if st.session_state.tabla_con_abonos is not None:
            st.session_state.tabla_con_abonos.to_csv(output, index=False)
        
        return output.getvalue()
    
    def generar_reporte_completo_excel(self):
        """
        Genera un reporte Excel completo con múltiples hojas
        """
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Hoja de resumen
            if st.session_state.datos_credito:
                resumen_credito = {
                    'Concepto': [
                        'Monto del Crédito',
                        'Tasa Original',
                        'Tipo de Tasa',
                        'Modalidad',
                        'Frecuencia',
                        'Número de Pagos',
                        'Fecha de Inicio',
                        'Cuota Fija'
                    ],
                    'Valor': [
                        f"${st.session_state.datos_credito['monto']:,.2f}",
                        f"{st.session_state.datos_credito['tasa_anual_original']:.2f}%",
                        st.session_state.datos_credito['tipo_tasa'],
                        st.session_state.datos_credito['modalidad'],
                        st.session_state.datos_credito['frecuencia_texto'],
                        st.session_state.datos_credito['num_pagos'],
                        st.session_state.datos_credito['fecha_inicio'],
                        f"${st.session_state.datos_credito['cuota_fija']:,.2f}"
                    ]
                }
                resumen_df = pd.DataFrame(resumen_credito)
                resumen_df.to_excel(writer, sheet_name='1_Resumen_Credito', index=False)
            
            # Hoja de comparación
            if (st.session_state.tabla_basica is not None and 
                st.session_state.tabla_con_abonos is not None):
                
                tabla_basica = st.session_state.tabla_basica
                tabla_abonos = st.session_state.tabla_con_abonos
                
                comparacion_data = {
                    'Concepto': [
                        'Períodos Totales',
                        'Total Cuotas',
                        'Total Intereses',
                        'Total Abonos Extra',
                        'Total Pagado',
                        'Ahorro en Intereses',
                        'Ahorro en Tiempo (períodos)',
                        'Porcentaje de Ahorro'
                    ],
                    'Sin Abonos': [
                        len(tabla_basica),
                        f"${tabla_basica['Cuota'].sum():,.2f}",
                        f"${tabla_basica['Interés'].sum():,.2f}",
                        "$0.00",
                        f"${tabla_basica['Cuota'].sum():,.2f}",
                        "-",
                        "-",
                        "-"
                    ],
                    'Con Abonos': [
                        len(tabla_abonos),
                        f"${tabla_abonos['Cuota'].sum():,.2f}",
                        f"${tabla_abonos['Interés'].sum():,.2f}",
                        f"${tabla_abonos['Abono_Extra'].sum():,.2f}",
                        f"${tabla_abonos['Cuota'].sum() + tabla_abonos['Abono_Extra'].sum():,.2f}",
                        f"${tabla_basica['Interés'].sum() - tabla_abonos['Interés'].sum():,.2f}",
                        f"{len(tabla_basica) - len(tabla_abonos)}",
                        f"{((tabla_basica['Interés'].sum() - tabla_abonos['Interés'].sum()) / tabla_basica['Interés'].sum()) * 100:.1f}%"
                    ]
                }
                comparacion_df = pd.DataFrame(comparacion_data)
                comparacion_df.to_excel(writer, sheet_name='2_Comparacion', index=False)
            
            # Hoja tabla básica
            if st.session_state.tabla_basica is not None:
                st.session_state.tabla_basica.to_excel(writer, sheet_name='3_Tabla_Basica', index=False)
            
            # Hoja tabla con abonos
            if st.session_state.tabla_con_abonos is not None:
                st.session_state.tabla_con_abonos.to_excel(writer, sheet_name='4_Tabla_con_Abonos', index=False)
            
            # Hoja de abonos configurados
            if st.session_state.manejo_abonos:
                abonos_data = {
                    'Tipo': [],
                    'Período': [],
                    'Monto': [],
                    'Frecuencia': [],
                    'Descripción': []
                }
                
                # Abonos programados
                for abono in st.session_state.manejo_abonos.abonos_programados:
                    abonos_data['Tipo'].append('Programado')
                    abonos_data['Período'].append(abono['periodo_inicio'])
                    abonos_data['Monto'].append(f"${abono['monto']:,.2f}")
                    abonos_data['Frecuencia'].append(f"Cada {abono['frecuencia']} períodos")
                    abonos_data['Descripción'].append(f"Desde período {abono['periodo_inicio']}")
                
                # Abonos ad-hoc
                for abono in st.session_state.manejo_abonos.abonos_adhoc:
                    abonos_data['Tipo'].append('Ad-hoc')
                    abonos_data['Período'].append(abono['periodo'])
                    abonos_data['Monto'].append(f"${abono['monto']:,.2f}")
                    abonos_data['Frecuencia'].append('Una vez')
                    abonos_data['Descripción'].append(f"Solo en período {abono['periodo']}")
                
                if abonos_data['Tipo']:  # Solo si hay abonos
                    abonos_df = pd.DataFrame(abonos_data)
                    abonos_df.to_excel(writer, sheet_name='5_Abonos_Configurados', index=False)
        
        return output.getvalue()
    
    def calculadora_tasas(self):
        """
        Calculadora independiente de conversión de tasas
        """
        st.subheader("🧮 Calculadora de Conversión de Tasas")
        
        tab1, tab2, tab3, tab4 = st.tabs([
            "Nominal ↔ Efectiva", 
            "Anticipada ↔ Vencida", 
            "Tasas Equivalentes",
            "Calculadora Completa"
        ])
        
        with tab1:
            st.write("**Conversión entre Tasa Nominal y Efectiva**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Nominal → Efectiva**")
                nom_to_ef_nominal = st.number_input("Tasa Nominal (%)", value=12.0, key="nom1") / 100
                nom_to_ef_freq = st.number_input("Períodos por año", value=12, min_value=1, key="freq1")
                
                if st.button("Convertir N→E", key="btn1"):
                    resultado = ConversionTasas.nominal_a_efectiva(nom_to_ef_nominal, nom_to_ef_freq)
                    st.success(f"Tasa Efectiva: **{resultado*100:.4f}%**")
            
            with col2:
                st.write("**Efectiva → Nominal**")
                ef_to_nom_efectiva = st.number_input("Tasa Efectiva (%)", value=12.68, key="ef1") / 100
                ef_to_nom_freq = st.number_input("Períodos por año", value=12, min_value=1, key="freq2")
                
                if st.button("Convertir E→N", key="btn2"):
                    resultado = ConversionTasas.efectiva_a_nominal(ef_to_nom_efectiva, ef_to_nom_freq)
                    st.success(f"Tasa Nominal: **{resultado*100:.4f}%**")
        
        with tab2:
            st.write("**Conversión entre Tasa Anticipada y Vencida**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Anticipada → Vencida**")
                ant_to_ven = st.number_input("Tasa Anticipada (%)", value=15.0, key="ant1") / 100
                
                if st.button("Convertir A→V", key="btn3"):
                    resultado = ConversionTasas.anticipada_a_vencida(ant_to_ven)
                    st.success(f"Tasa Vencida: **{resultado*100:.4f}%**")
            
            with col2:
                st.write("**Vencida → Anticipada**")
                ven_to_ant = st.number_input("Tasa Vencida (%)", value=17.65, key="ven1") / 100
                
                if st.button("Convertir V→A", key="btn4"):
                    resultado = ConversionTasas.vencida_a_anticipada(ven_to_ant)
                    st.success(f"Tasa Anticipada: **{resultado*100:.4f}%**")
        
        with tab3:
            st.write("**Cálculo de Tasas Equivalentes**")
            
            tasa_base = st.number_input("Tasa Base Anual (%)", value=20.0) / 100
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("💰 Calcular Equivalentes"):
                    st.write("**Tasas Equivalentes:**")
                    
                    equivalentes = {
                        "Anual": tasa_base * 100,
                        "Semestral": ConversionTasas.tasa_equivalente(tasa_base, 1, 2) * 100,
                        "Trimestral": ConversionTasas.tasa_equivalente(tasa_base, 1, 4) * 100,
                        "Mensual": ConversionTasas.tasa_equivalente(tasa_base, 1, 12) * 100,
                        "Quincenal": ConversionTasas.tasa_equivalente(tasa_base, 1, 24) * 100,
                        "Semanal": ConversionTasas.tasa_equivalente(tasa_base, 1, 52) * 100,
                        "Diaria": ConversionTasas.tasa_equivalente(tasa_base, 1, 365) * 100
                    }
                    
                    for periodo, tasa in equivalentes.items():
                        st.metric(periodo, f"{tasa:.4f}%")
        
        with tab4:
            st.write("**Calculadora Completa de Tasas**")
            
            with st.form("calculadora_completa"):
                col1, col2 = st.columns(2)
                
                with col1:
                    tasa_entrada = st.number_input("Tasa de Entrada (%)", value=18.0) / 100
                    tipo_entrada = st.selectbox("Tipo de Entrada", ["Nominal", "Efectiva"])
                    modalidad_entrada = st.selectbox("Modalidad de Entrada", ["Vencida", "Anticipada"])
                    freq_entrada = st.number_input("Frecuencia de Entrada (períodos/año)", value=12, min_value=1)
                
                with col2:
                    tipo_salida = st.selectbox("Tipo de Salida", ["Nominal", "Efectiva"])
                    modalidad_salida = st.selectbox("Modalidad de Salida", ["Vencida", "Anticipada"])
                    freq_salida = st.number_input("Frecuencia de Salida (períodos/año)", value=4, min_value=1)
                
                if st.form_submit_button("🧮 Calcular Conversión Completa"):
                    try:
                        # Proceso de conversión completo
                        tasa_trabajo = tasa_entrada
                        
                        # Paso 1: Convertir a efectiva si es nominal
                        if tipo_entrada == "Nominal":
                            tasa_trabajo = ConversionTasas.nominal_a_efectiva(tasa_trabajo, freq_entrada)
                            st.info(f"Paso 1: Nominal → Efectiva = {tasa_trabajo*100:.4f}%")
                        
                        # Paso 2: Convertir de anticipada a vencida si es necesario
                        if modalidad_entrada == "Anticipada" and modalidad_salida == "Vencida":
                            tasa_trabajo = ConversionTasas.anticipada_a_vencida(tasa_trabajo)
                            st.info(f"Paso 2: Anticipada → Vencida = {tasa_trabajo*100:.4f}%")
                        elif modalidad_entrada == "Vencida" and modalidad_salida == "Anticipada":
                            tasa_trabajo = ConversionTasas.vencida_a_anticipada(tasa_trabajo)
                            st.info(f"Paso 2: Vencida → Anticipada = {tasa_trabajo*100:.4f}%")
                        
                        # Paso 3: Convertir a la frecuencia deseada
                        if freq_entrada != freq_salida:
                            tasa_trabajo = ConversionTasas.tasa_equivalente(tasa_trabajo, 1, freq_salida)
                            st.info(f"Paso 3: Cambio de frecuencia = {tasa_trabajo*100:.4f}%")
                        
                        # Paso 4: Convertir a nominal si es necesario
                        if tipo_salida == "Nominal":
                            tasa_trabajo = ConversionTasas.efectiva_a_nominal(tasa_trabajo, freq_salida)
                            st.info(f"Paso 4: Efectiva → Nominal = {tasa_trabajo*100:.4f}%")
                        
                        st.success(f"🎯 **Resultado Final: {tasa_trabajo*100:.4f}%**")
                        
                    except Exception as e:
                        st.error(f"Error en el cálculo: {str(e)}")
    
    def ejecutar(self):
        """
        Ejecuta la aplicación principal
        """
        # Header
        self.mostrar_header()
        
        # Sidebar
        self.sidebar_configuracion_credito()
        
        # Contenido principal
        if st.session_state.datos_credito:
            # Mostrar resumen del crédito
            self.mostrar_resumen_credito()
            st.markdown("---")
            
            # Tabs principales
            tab1, tab2, tab3, tab4, tab5 = st.tabs([
                "💰 Abonos Extras", 
                "📊 Tablas de Amortización", 
                "📥 Descargas", 
                "🧮 Calculadora de Tasas",
                "📖 Ayuda"
            ])
            
            with tab1:
                self.configurar_abonos()
            
            with tab2:
                self.generar_y_mostrar_tablas()
            
            with tab3:
                self.seccion_descargas()
            
            with tab4:
                self.calculadora_tasas()
            
            with tab5:
                self.mostrar_ayuda()
        
        else:
            # Mensaje de bienvenida
            st.info("👈 Configure los parámetros del crédito en la barra lateral para comenzar")
            
            # Mostrar calculadora de tasas como preview
            with st.expander("🧮 Calculadora de Tasas (Vista Previa)", expanded=True):
                self.calculadora_tasas()
    
    def mostrar_ayuda(self):
        """
        Muestra la sección de ayuda
        """
        st.subheader("📖 Ayuda y Documentación")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**🚀 Cómo usar la aplicación:**")
            st.markdown("""
            1. **Configure el crédito** en la barra lateral:
               - Ingrese monto, tasa, plazo y frecuencia
               - Seleccione tipo y modalidad de tasa
               - Haga clic en "Configurar Crédito"
            
            2. **Agregue abonos extras** (opcional):
               - Abonos programados: se repiten automáticamente
               - Abonos ad-hoc: una sola vez en período específico
            
            3. **Genere las tablas**:
               - Tabla básica: sin abonos extras
               - Tabla con abonos: incluye todos los abonos
            
            4. **Analice los resultados**:
               - Compare ambas tablas
               - Vea gráficos interactivos
               - Descargue archivos CSV/Excel
            """)
        
        with col2:
            st.write("**💡 Conceptos Financieros:**")
            st.markdown("""
            **Tipos de Tasa:**
            - **Nominal**: Tasa anunciada, no incluye capitalización
            - **Efectiva**: Tasa real considerando capitalización
            
            **Modalidades:**
            - **Vencida**: Intereses se pagan al final del período
            - **Anticipada**: Intereses se pagan al inicio del período
            
            **Abonos Extras:**
            - **Programados**: Se aplican automáticamente cada X períodos
            - **Ad-hoc**: Se aplican una sola vez en período específico
            
            **Beneficios de Abonos:**
            - Reducen tiempo de pago
            - Disminuyen intereses totales
            - Mejoran flujo de caja
            """)
        
        st.markdown("---")
        
        st.write("**🎯 Características de la Aplicación:**")
        
        features_col1, features_col2, features_col3 = st.columns(3)
        
        with features_col1:
            st.markdown("""
            **🧮 Cálculos Precisos**
            - Fórmulas financieras exactas
            - Redondeo apropiado
            - Validación de datos
            """)
        
        with features_col2:
            st.markdown("""
            **📊 Visualizaciones**
            - Gráficos interactivos
            - Comparaciones visuales
            - Análisis detallado
            """)
        
        with features_col3:
            st.markdown("""
            **💾 Exportación**
            - Archivos CSV y Excel
            - Resúmenes incluidos
            - Formato profesional
            """)
        
        st.markdown("---")
        st.info("🏦 **Aplicativo desarrollado para Ingeniería Financiera** - Proyecto académico 2025")


def main():
    """
    Función principal para ejecutar la aplicación Streamlit
    """
    app = AplicativoWeb()
    app.ejecutar()


if __name__ == "__main__":
    main()