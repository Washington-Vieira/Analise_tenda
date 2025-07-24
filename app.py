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
        
        # Upload dos arquivos
        st.subheader("📥 Importe os Arquivos")
        
        st.markdown("**1. Importe a Entrada:**")
        entrada_file = st.file_uploader(
            "Arquivo de Entradas",
            type=['xlsx', 'xls'],
            help="Arquivo Excel com dados de entrada (valores positivos)",
            key="entrada"
        )
        
        st.markdown("**2. Importe a Saída:**")
        saida_file = st.file_uploader(
            "Arquivo de Saídas", 
            type=['xlsx', 'xls'],
            help="Arquivo Excel com dados de saída (valores negativos ou positivos)",
            key="saida"
        )
        
        st.markdown("**3. Importe a Cobertura:**")
        cobertura_file = st.file_uploader(
            "Arquivo de Cobertura",
            type=['xlsx', 'xls'],
            help="Arquivo Excel com dados de cobertura e análise crítica",
            key="cobertura"
        )
        
        # Mostrar status dos arquivos
        if entrada_file is not None:
            st.success("✅ Arquivo de entrada carregado!")
            st.info(f"📁 **Entrada:** {entrada_file.name}")
        
        if saida_file is not None:
            st.success("✅ Arquivo de saída carregado!")
            st.info(f"📁 **Saída:** {saida_file.name}")
        
        if cobertura_file is not None:
            st.success("✅ Arquivo de cobertura carregado!")
            st.info(f"📁 **Cobertura:** {cobertura_file.name}")
    
    # Área principal
    # Análise de Cobertura (independente)
    if cobertura_file is not None:
        st.header("📊 Análise de Cobertura")
        
        try:
            with st.spinner("🔄 Processando dados de cobertura..."):
                processor = DataProcessor()
                visualizer = Visualizer()
                df_cobertura = processor.load_excel_file(cobertura_file)
                
                if df_cobertura is not None:
                    # Validar colunas para cobertura (mais flexível)
                    validation_result = processor.validate_cobertura_columns(df_cobertura)
                    
                    if validation_result['missing']:
                        st.error(f"❌ Coluna principal não encontrada: {', '.join(validation_result['missing'])}")
                        if validation_result['suggestions']:
                            st.info(f"💡 Colunas similares encontradas: {', '.join(validation_result['suggestions'])}")
                        st.info("🔍 Verificando todas as colunas do arquivo...")
                    else:
                        # Processar dados de cobertura
                        df_cobertura_processed = processor.process_cobertura_data(df_cobertura)
                        
                        if df_cobertura_processed is not None:
                            # Estatísticas de cobertura
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                total_items = len(df_cobertura_processed)
                                st.metric("Total de Itens", f"{total_items:,}")
                            
                            with col2:
                                unique_materials = df_cobertura_processed['Material'].nunique()
                                st.metric("Materiais Únicos", unique_materials)
                            
                            with col3:
                                current_date = df_cobertura_processed['Data_Processamento'].iloc[0]
                                st.metric("Data de Processamento", current_date.strftime('%d/%m/%Y'))
                            
                            # Análise dos níveis de cobertura
                            st.subheader("🥧 Distribuição dos Níveis de Cobertura")
                            
                            cobertura_counts = processor.analyze_cobertura_levels(df_cobertura_processed)
                            fig_pie = visualizer.create_cobertura_pie_chart(cobertura_counts)
                            st.plotly_chart(fig_pie, use_container_width=True)
                            
                            # Tabela de níveis de cobertura
                            st.subheader("📋 Detalhes dos Níveis de Cobertura")
                            st.dataframe(
                                cobertura_counts,
                                use_container_width=True,
                                column_config={
                                    "Quantidade": st.column_config.NumberColumn("Quantidade", format="%d"),
                                    "Percentual": st.column_config.NumberColumn("Percentual (%)", format="%.2f%%")
                                }
                            )
                            
                            # Análise de itens críticos
                            critical_summary = processor.get_critical_summary(df_cobertura_processed)
                            
                            if critical_summary['total_critical'] > 0:
                                # Apenas mostrar evolução temporal melhorada
                                st.subheader("📈 Evolução de Itens Críticos ao Longo do Tempo")
                                
                                critical_timeline = processor.analyze_critical_items_over_time(df_cobertura_processed)
                                fig_critical_timeline = visualizer.create_critical_timeline_chart(critical_timeline)
                                st.plotly_chart(fig_critical_timeline, use_container_width=True)
                                
                                # Mostrar apenas um resumo simples
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.metric("Total de Itens Críticos", critical_summary['total_critical'])
                                with col2:
                                    critical_percentage = (critical_summary['total_critical'] / total_items * 100)
                                    st.metric("Percentual Crítico", f"{critical_percentage:.1f}%")
                            
                            else:
                                st.success("✅ Nenhum item crítico encontrado!")
                        
                        else:
                            st.error("❌ Erro ao processar dados de cobertura.")
                
                else:
                    st.error("❌ Erro ao carregar arquivo de cobertura.")
        
        except Exception as e:
            st.error(f"❌ Erro ao processar arquivo de cobertura: {str(e)}")
        
        st.divider()
    
    # Análise de Entrada/Saída
    if entrada_file is not None and saida_file is not None:
        try:
            # Processar dados
            with st.spinner("🔄 Processando dados de entrada e saída..."):
                processor = DataProcessor()
                
                # Carregar arquivo de entrada
                df_entrada = processor.load_excel_file(entrada_file)
                # Carregar arquivo de saída
                df_saida = processor.load_excel_file(saida_file)
                
                if df_entrada is not None and df_saida is not None:
                    # Validar colunas obrigatórias para ambos os arquivos
                    required_columns = [
                        'Linha MAE', 'Linha ATO', 'Semiacabado', 'Quantidade',
                        'Data Movimento', 'Código Movimento', 'Movimento', 'Área'
                    ]
                    
                    missing_entrada = processor.validate_columns(df_entrada, required_columns)
                    missing_saida = processor.validate_columns(df_saida, required_columns)
                    
                    if missing_entrada or missing_saida:
                        if missing_entrada:
                            st.error(f"❌ Colunas obrigatórias não encontradas no arquivo de ENTRADA: {', '.join(missing_entrada)}")
                        if missing_saida:
                            st.error(f"❌ Colunas obrigatórias não encontradas no arquivo de SAÍDA: {', '.join(missing_saida)}")
                        return
                    
                    # Processar dados temporais
                    df_entrada_processed = processor.process_temporal_data(df_entrada)
                    df_saida_processed = processor.process_temporal_data(df_saida)
                    
                    # Garantir que quantidade de saída seja negativa
                    df_saida_processed['Quantidade'] = -abs(df_saida_processed['Quantidade'])
                    
                    # Marcar tipo de movimento
                    df_entrada_processed['Tipo_Movimento'] = 'Entrada'
                    df_saida_processed['Tipo_Movimento'] = 'Saída'
                    
                    # Combinar os dados
                    df_combined = pd.concat([df_entrada_processed, df_saida_processed], ignore_index=True)
                    df_processed = df_combined.sort_values('Data Movimento')
                    
                    if df_processed is not None and len(df_processed) > 0:
                        # Criar visualizador
                        visualizer = Visualizer()
                        
                        # Estatísticas gerais
                        st.header("📈 Resumo Geral")
                        
                        col1, col2, col3, col4, col5 = st.columns(5)
                        
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
                            total_entrada = df_processed[df_processed['Tipo_Movimento'] == 'Entrada']['Quantidade'].sum()
                            st.metric("Total Entradas", f"{total_entrada:,.0f}")
                        
                        with col5:
                            total_saida = abs(df_processed[df_processed['Tipo_Movimento'] == 'Saída']['Quantidade'].sum())
                            st.metric("Total Saídas", f"{total_saida:,.0f}")
                        
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
                                
                                # Análise por hora com entrada/saída
                                st.header("🕐 Análise por Hora do Dia")
                                
                                hourly_data = processor.analyze_hourly_patterns_with_type(df_filtered)
                                fig_hourly = visualizer.create_hourly_entrada_saida_chart(hourly_data)
                                st.plotly_chart(fig_hourly, use_container_width=True)
                                
                                # Análise por dia do mês com entrada/saída (Simplificada)
                                st.header("📅 Análise por Dia do Mês")
                                
                                daily_number_data = processor.analyze_daily_patterns_by_day_number_with_type(df_filtered)
                                fig_daily_number = visualizer.create_daily_number_entrada_saida_chart(daily_number_data)
                                st.plotly_chart(fig_daily_number, use_container_width=True)
                                
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
                                        if peaks_data and len(peaks_data) > 0:
                                            peaks_df = processor.create_peaks_summary(peaks_data)
                                            if not peaks_df.empty:
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
                    st.error("❌ Erro ao carregar os arquivos Excel.")
        
        except Exception as e:
            st.error(f"❌ Erro ao processar o arquivo: {str(e)}")
            st.info("💡 Verifique se o arquivo está no formato correto e contém todas as colunas obrigatórias.")
    
    elif entrada_file is not None or saida_file is not None or cobertura_file is not None:
        # Instruções quando apenas alguns arquivos foram carregados
        missing_files = []
        if entrada_file is None:
            missing_files.append("**ENTRADA**")
        if saida_file is None:
            missing_files.append("**SAÍDA**")
        
        if len(missing_files) > 0:
            st.warning(f"⚠️ Para análise completa, faça upload dos arquivos: {', '.join(missing_files)}")
        
        if cobertura_file is None:
            st.info("💡 Você também pode fazer upload do arquivo de **COBERTURA** para análise de criticidade")
    
    else:
        # Instruções quando nenhum arquivo foi carregado
        st.info("👈 Faça upload dos arquivos Excel para começar a análise")
        st.markdown("""
        **Arquivos disponíveis:**
        - **Entrada e Saída**: Para análise temporal de movimentação
        - **Cobertura**: Para análise de criticidade e níveis de cobertura
        """)
        
        with st.expander("📋 Colunas Obrigatórias"):
            st.markdown("""
            O arquivo Excel deve conter as seguintes colunas:
            - **Linha MAE**: Linha mãe do projeto
            - **Linha ATO**: Linha de projeto (usado para agrupamento)
            - **Semiacabado**: Identificação do semiacabado
            - **Quantidade**: Valores numéricos para análise
            - **Data Movimento**: Data e hora do movimento (formato: DD/MM/AAAA HH:MM:SS)
            - **Código Movimento**: Código do tipo de movimento
            - **Movimento**: Descrição do movimento
            - **Área**: Área responsável
            
            **Para arquivo de Cobertura:**
            - **Nível de Cobertura**: Nível do item (usado para análise de criticidade)
            - **Material**: Código ou nome do material
            - **Necessidade**: Quantidade necessária
            - **Balance**: Saldo atual
            - **Linha MAE**: Linha mãe do projeto
            - **Linha de ATO**: Linha de projeto
            - **Área**: Área responsável
            
            **Exemplo de formato da Data Movimento:** 21/07/2025 06:08:01
            
            O aplicativo extrairá automaticamente:
            - **Dia:** 21 (dia do mês)
            - **Hora:** 06 (hora arredondada)
            - **Data atual** para análise de cobertura
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
