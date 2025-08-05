import streamlit as st
import pandas as pd
from utils.data_processor import DataProcessor
from utils.visualizer import Visualizer

# Configuração da página
st.set_page_config(
    page_title="Dashboard de Análise",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def main():
    st.title("📊 Dashboard de Análise")
    
    # Carregar os dados salvos da sessão principal
    if 'df_entrada' not in st.session_state or 'df_saida' not in st.session_state:
        st.warning("⚠️ Por favor, carregue os arquivos na página principal primeiro!")
        return
    
    # Inicializar processador e visualizador
    processor = DataProcessor()
    visualizer = Visualizer()
    
    # Criar containers para organizar o layout
    header = st.container()
    metrics_row = st.container()
    charts_row1 = st.container()
    charts_row2 = st.container()
    
    with header:
        # Filtros em colunas
        col1, col2 = st.columns(2)
        
        with col1:
            # Filtro por linha de projeto
            available_projects = sorted(st.session_state.df_entrada['Linha ATO'].unique())
            selected_projects = st.multiselect(
                "Selecionar Linhas de Projeto",
                options=available_projects,
                default=available_projects[:5] if len(available_projects) > 5 else available_projects,
                help="Selecione as linhas de projeto para análise"
            )
        
        with col2:
            try:
                # Preparar dados de entrada e saída
                df_entrada = st.session_state.df_entrada.copy()
                df_saida = st.session_state.df_saida.copy()
                
                # Garantir que as datas estejam no formato correto
                df_entrada['Data Movimento'] = pd.to_datetime(df_entrada['Data Movimento'])
                df_saida['Data Movimento'] = pd.to_datetime(df_saida['Data Movimento'])
                
                # Extrair hora e dia do mês
                df_entrada['Hora'] = df_entrada['Data Movimento'].dt.hour
                df_entrada['Dia'] = df_entrada['Data Movimento'].dt.day
                df_saida['Hora'] = df_saida['Data Movimento'].dt.hour
                df_saida['Dia'] = df_saida['Data Movimento'].dt.day
                
                # Adicionar coluna de tipo de movimento
                df_entrada['Tipo_Movimento'] = 'Entrada'
                df_saida['Tipo_Movimento'] = 'Saída'
                
                # Garantir que quantidade de saída seja negativa
                df_saida['Quantidade'] = -abs(df_saida['Quantidade'])
                
                # Combinar dados
                df_combined = pd.concat([df_entrada, df_saida])
                
                # Filtro por período
                min_date = df_combined['Data Movimento'].min().date()
                max_date = df_combined['Data Movimento'].max().date()
                
                date_range = st.date_input(
                    "Período de Análise",
                    value=(min_date, max_date),
                    min_value=min_date,
                    max_value=max_date,
                    help="Selecione o período para análise"
                )
            except Exception as e:
                st.error(f"Erro ao processar datas: {str(e)}")
                return
    
    # Aplicar filtros
    if selected_projects and len(date_range) == 2:
        try:
            # Aplicar filtros
            df_filtered = processor.apply_filters(
                df_combined,
                selected_projects,
                date_range[0],
                date_range[1]
            )
            
            with metrics_row:
                
                # Processar dados de cobertura se disponível
                critical_metrics = {}
                if 'df_cobertura' in st.session_state:
                    df_cobertura_processed = processor.process_cobertura_data(st.session_state.df_cobertura)
                    critical_summary = processor.get_critical_summary(df_cobertura_processed)
                    if not critical_summary['critical_by_line'].empty:
                        critical_metrics = {
                            'total_lines': len(critical_summary['critical_by_line']),
                            'total_critical': critical_summary['critical_by_line']['Quantidade_Critica'].sum(),
                            'percent_critical': (critical_summary['total_critical'] / len(df_cobertura_processed) * 100) if len(df_cobertura_processed) > 0 else 0
                        }
                
                # Todas as métricas em uma única linha
                col1, col2, col3, col4, col5, col6, col7, col8 = st.columns(8)
                
                with col1:
                    total_records = len(df_filtered)
                    st.metric("Total de Registros", f"{total_records:,}")
                
                with col2:
                    unique_projects = df_filtered['Linha ATO'].nunique()
                    st.metric("Linhas de Projeto", unique_projects)
                
                with col3:
                    total_entrada = df_filtered[df_filtered['Tipo_Movimento'] == 'Entrada']['Quantidade'].sum()
                    st.metric("Total Entradas", f"{total_entrada:,.0f}")
                
                with col4:
                    total_saida = abs(df_filtered[df_filtered['Tipo_Movimento'] == 'Saída']['Quantidade'].sum())
                    st.metric("Total Saídas", f"{total_saida:,.0f}")
                
                with col5:
                    date_range_days = (df_filtered['Data Movimento'].max() - df_filtered['Data Movimento'].min()).days
                    st.metric("Período (dias)", date_range_days)
                
                with col6:
                    if critical_metrics:
                        st.metric("Linhas Críticas", f"{critical_metrics['total_lines']:,}")
                    else:
                        st.metric("Linhas Críticas", "N/A")
                
                with col7:
                    if critical_metrics:
                        st.metric("Itens Críticos", f"{critical_metrics['total_critical']:,}")
                    else:
                        st.metric("Itens Críticos", "N/A")
                
                with col8:
                    if critical_metrics:
                        st.metric("% Crítico", f"{critical_metrics['percent_critical']:.1f}%")
                    else:
                        st.metric("% Crítico", "N/A")
            
            with charts_row1:
                # Primeira linha de gráficos
                col1, col2 = st.columns(2)
                
                with col1:
                    st.caption("Análise por Hora do Dia")
                    hourly_data = processor.analyze_hourly_patterns_with_type(df_filtered)
                    fig_hourly = visualizer.create_hourly_entrada_saida_chart(hourly_data)
                    st.plotly_chart(fig_hourly, use_container_width=True)
                
                with col2:
                    st.caption("Análise por Dia do Mês")
                    daily_data = processor.analyze_daily_patterns_by_day_number_with_type(df_filtered)
                    fig_daily = visualizer.create_daily_number_entrada_saida_chart(daily_data)
                    st.plotly_chart(fig_daily, use_container_width=True)
            
            with charts_row2:
                # Segunda linha de gráficos
                if 'df_cobertura' in st.session_state:
                    # Primeira linha: Gráficos de cobertura e evolução
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.caption("Níveis de Cobertura")
                        df_cobertura_processed = processor.process_cobertura_data(st.session_state.df_cobertura)
                        cobertura_counts = processor.analyze_cobertura_levels(df_cobertura_processed)
                        
                        # Obter a data atual formatada
                        data_atual = df_cobertura_processed['Data_Processamento'].iloc[0]
                        data_formatada = data_atual.strftime('%d/%m/%Y')
                        st.caption(f"Data da análise: {data_formatada}")
                        
                        fig_pie = visualizer.create_cobertura_pie_chart(cobertura_counts)
                        st.plotly_chart(fig_pie, use_container_width=True)
                    
                    with col2:
                        st.caption("Evolução de Itens Críticos")
                        critical_timeline = processor.analyze_critical_items_over_time(df_cobertura_processed)
                        fig_critical = visualizer.create_critical_timeline_chart(critical_timeline)
                        st.plotly_chart(fig_critical, use_container_width=True)
                    
                    # Segunda linha: KPI de Linhas ATO com Itens Críticos
                    st.caption("Linhas ATO com Itens Críticos")
                    critical_summary = processor.get_critical_summary(df_cobertura_processed)
                    critical_materials = processor.get_critical_materials_by_line(df_cobertura_processed)
                    
                    if not critical_summary['critical_by_line'].empty:
                        # Tabela com as linhas críticas e expanders para materiais
                        for _, row in critical_summary['critical_by_line'].iterrows():
                            linha_ato = row['Linha de ATO']
                            with st.expander(f"📦 {linha_ato} - {row['Quantidade_Critica']} itens críticos"):
                                if linha_ato in critical_materials:
                                    # Criar DataFrame para melhor visualização
                                    df_materiais = pd.DataFrame(critical_materials[linha_ato])
                                    
                                    # Configurar colunas para exibição
                                    st.dataframe(
                                        df_materiais,
                                        use_container_width=True,
                                        column_config={
                                            "Material": st.column_config.TextColumn(
                                                "Material",
                                                width="medium"
                                            ),
                                            "Nível de Cobertura": st.column_config.TextColumn(
                                                "Nível de Cobertura",
                                                width="small"
                                            ),
                                            "Balance": st.column_config.NumberColumn(
                                                "Saldo",
                                                format="%.0f"
                                            ),
                                            "Necessidade": st.column_config.NumberColumn(
                                                "Necessidade",
                                                format="%.0f"
                                            ),
                                            "Cobertura %": st.column_config.NumberColumn(
                                                "Cobertura %",
                                                format="%.2f%%"
                                            )
                                        },
                                        hide_index=True
                                    )
                                else:
                                    st.info("Não foram encontrados detalhes dos materiais para esta linha.")
                    else:
                        st.info("Nenhuma linha ATO crítica encontrada.")
                
                # Tabela resumo
                st.caption("Resumo por Linha de Projeto")
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
        except Exception as e:
            st.error(f"Erro ao processar dados: {str(e)}")

if __name__ == "__main__":
    main() 