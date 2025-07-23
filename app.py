import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime as dt
from io import BytesIO
import numpy as np
from utils.data_processor import DataProcessor
from utils.visualizer import Visualizer

# Configuração da página
st.set_page_config(
    page_title="Análise Temporal de Arquivos Excel",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    st.title("📊 Análise Temporal de Arquivos Excel")
    st.markdown("### Análise de Picos de Entrada/Saída por Linha de Projeto")
    
    # Sidebar para upload e configurações
    with st.sidebar:
        st.header("🔧 Configurações")
        
        # Upload do arquivo
        uploaded_file = st.file_uploader(
            "Selecione o arquivo Excel",
            type=['xlsx', 'xls'],
            help="Faça upload do arquivo Excel com os dados de movimento"
        )
        
        if uploaded_file is not None:
            st.success("✅ Arquivo carregado com sucesso!")
            
            # Mostrar informações do arquivo
            st.info(f"📁 **Nome:** {uploaded_file.name}")
            st.info(f"📏 **Tamanho:** {uploaded_file.size:,} bytes")
    
    # Área principal
    if uploaded_file is not None:
        try:
            # Processar dados
            with st.spinner("🔄 Processando dados..."):
                processor = DataProcessor()
                df = processor.load_excel_file(uploaded_file)
                
                if df is not None:
                    # Validar colunas obrigatórias
                    required_columns = [
                        'Linha MAE', 'Linha ATO', 'Semiacabado', 'Quantidade',
                        'Data Movimento', 'Código Movimento', 'Movimento', 'Área'
                    ]
                    
                    missing_columns = processor.validate_columns(df, required_columns)
                    
                    if missing_columns:
                        st.error(f"❌ Colunas obrigatórias não encontradas: {', '.join(missing_columns)}")
                        st.info("🔍 **Colunas encontradas no arquivo:**")
                        for col in df.columns:
                            st.write(f"• {col}")
                        return
                    
                    # Processar dados temporais
                    df_processed = processor.process_temporal_data(df)
                    
                    if df_processed is not None and len(df_processed) > 0:
                        # Criar visualizador
                        visualizer = Visualizer()
                        
                        # Estatísticas gerais
                        st.header("📈 Resumo Geral")
                        
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            total_records = len(df_processed)
                            st.metric("Total de Registros", f"{total_records:,}")
                        
                        with col2:
                            unique_projects = df_processed['Linha ATO'].nunique()
                            st.metric("Linhas de Projeto", unique_projects)
                        
                        with col3:
                            date_range = (df_processed['Data Movimento'].max() - df_processed['Data Movimento'].min()).days
                            st.metric("Período (dias)", date_range)
                        
                        with col4:
                            total_quantity = df_processed['Quantidade'].sum()
                            st.metric("Quantidade Total", f"{total_quantity:,.0f}")
                        
                        # Filtros
                        st.header("🔍 Filtros")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            # Filtro por linha de projeto
                            available_projects = sorted(df_processed['Linha ATO'].unique())
                            selected_projects = st.multiselect(
                                "Selecionar Linhas de Projeto",
                                options=available_projects,
                                default=available_projects[:5] if len(available_projects) > 5 else available_projects,
                                help="Selecione as linhas de projeto para análise"
                            )
                        
                        with col2:
                            # Filtro por período
                            min_date = df_processed['Data Movimento'].min().date()
                            max_date = df_processed['Data Movimento'].max().date()
                            
                            date_range = st.date_input(
                                "Período de Análise",
                                value=(min_date, max_date),
                                min_value=min_date,
                                max_value=max_date,
                                help="Selecione o período para análise"
                            )
                        
                        # Aplicar filtros
                        if selected_projects and len(date_range) == 2:
                            df_filtered = processor.apply_filters(
                                df_processed, 
                                selected_projects, 
                                date_range[0], 
                                date_range[1]
                            )
                            
                            if len(df_filtered) > 0:
                                # Análise temporal por linha de projeto
                                st.header("📊 Análise Temporal por Linha de Projeto")
                                
                                # Gráfico principal - séries temporais
                                fig_timeline = visualizer.create_timeline_chart(df_filtered)
                                st.plotly_chart(fig_timeline, use_container_width=True)
                                
                                # Análise de picos
                                st.header("⚡ Análise de Picos de Entrada/Saída")
                                
                                # Detectar picos por projeto
                                peaks_data = processor.detect_peaks_by_project(df_filtered)
                                
                                if peaks_data:
                                    # Gráfico de picos
                                    fig_peaks = visualizer.create_peaks_chart(df_filtered, peaks_data)
                                    st.plotly_chart(fig_peaks, use_container_width=True)
                                    
                                    # Tabela de picos
                                    st.subheader("📋 Detalhes dos Picos")
                                    peaks_df = processor.create_peaks_summary(peaks_data)
                                    st.dataframe(
                                        peaks_df,
                                        use_container_width=True,
                                        column_config={
                                            "Valor Pico": st.column_config.NumberColumn(
                                                "Valor do Pico",
                                                format="%.0f"
                                            ),
                                            "Data/Hora": st.column_config.DatetimeColumn(
                                                "Data/Hora do Pico",
                                                format="DD/MM/YYYY HH:mm"
                                            )
                                        }
                                    )
                                
                                # Análise por hora do dia
                                st.header("🕐 Análise por Hora do Dia")
                                
                                hourly_data = processor.analyze_hourly_patterns(df_filtered)
                                fig_hourly = visualizer.create_hourly_analysis_chart(hourly_data)
                                st.plotly_chart(fig_hourly, use_container_width=True)
                                
                                # Análise por dia da semana
                                st.header("📅 Análise por Dia da Semana")
                                
                                daily_data = processor.analyze_daily_patterns(df_filtered)
                                fig_daily = visualizer.create_daily_analysis_chart(daily_data)
                                st.plotly_chart(fig_daily, use_container_width=True)
                                
                                # Tabela resumo por projeto
                                st.header("📊 Resumo por Linha de Projeto")
                                
                                summary_df = processor.create_project_summary(df_filtered)
                                st.dataframe(
                                    summary_df,
                                    use_container_width=True,
                                    column_config={
                                        "Total Quantidade": st.column_config.NumberColumn(
                                            "Total Quantidade",
                                            format="%.0f"
                                        ),
                                        "Média Quantidade": st.column_config.NumberColumn(
                                            "Média Quantidade",
                                            format="%.2f"
                                        ),
                                        "Máximo Quantidade": st.column_config.NumberColumn(
                                            "Máximo Quantidade",
                                            format="%.0f"
                                        )
                                    }
                                )
                                
                                # Exportar dados processados
                                st.header("💾 Exportar Dados")
                                
                                if st.button("📥 Baixar Dados Processados (Excel)"):
                                    output = BytesIO()
                                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                                        df_filtered.to_excel(writer, sheet_name='Dados Filtrados', index=False)
                                        summary_df.to_excel(writer, sheet_name='Resumo por Projeto', index=False)
                                        if peaks_data:
                                            peaks_df.to_excel(writer, sheet_name='Picos Detectados', index=False)
                                    
                                    st.download_button(
                                        label="💾 Download Excel",
                                        data=output.getvalue(),
                                        file_name=f"analise_temporal_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                    )
                            
                            else:
                                st.warning("⚠️ Nenhum dado encontrado com os filtros aplicados.")
                        
                        else:
                            st.warning("⚠️ Selecione pelo menos uma linha de projeto e um período válido.")
                    
                    else:
                        st.error("❌ Erro ao processar os dados temporais. Verifique o formato da coluna 'Data Movimento'.")
                
                else:
                    st.error("❌ Erro ao carregar o arquivo Excel.")
        
        except Exception as e:
            st.error(f"❌ Erro ao processar o arquivo: {str(e)}")
            st.info("💡 Verifique se o arquivo está no formato correto e contém todas as colunas obrigatórias.")
    
    else:
        # Instruções quando nenhum arquivo foi carregado
        st.info("👈 Faça upload de um arquivo Excel para começar a análise")
        
        with st.expander("📋 Colunas Obrigatórias"):
            st.markdown("""
            O arquivo Excel deve conter as seguintes colunas:
            - **Linha MAE**: Linha mãe do projeto
            - **Linha ATO**: Linha de projeto (usado para agrupamento)
            - **Semiacabado**: Identificação do semiacabado
            - **Quantidade**: Valores numéricos para análise
            - **Data Movimento**: Data e hora do movimento (formato: DD/MM/AAAA HH:MM)
            - **Código Movimento**: Código do tipo de movimento
            - **Movimento**: Descrição do movimento
            - **Área**: Área responsável
            """)
        
        with st.expander("ℹ️ Como Usar"):
            st.markdown("""
            1. **Upload**: Carregue seu arquivo Excel usando o botão na barra lateral
            2. **Validação**: O sistema verificará se todas as colunas obrigatórias estão presentes
            3. **Filtros**: Use os filtros para selecionar projetos e períodos específicos
            4. **Análise**: Visualize gráficos temporais, picos e padrões
            5. **Export**: Baixe os dados processados em formato Excel
            """)

if __name__ == "__main__":
    main()
