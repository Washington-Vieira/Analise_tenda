import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
import streamlit as st
from scipy.signal import find_peaks
import warnings
warnings.filterwarnings('ignore')

class DataProcessor:
    def __init__(self):
        self.df = None
    
    def load_excel_file(self, uploaded_file):
        """Carrega arquivo Excel e retorna DataFrame"""
        try:
            # Tentar diferentes engines
            try:
                df = pd.read_excel(uploaded_file, engine='openpyxl')
            except:
                df = pd.read_excel(uploaded_file, engine='xlrd')
            
            return df
        
        except Exception as e:
            st.error(f"Erro ao carregar arquivo Excel: {str(e)}")
            return None
    
    def validate_columns(self, df, required_columns):
        """Valida se as colunas obrigatórias estão presentes"""
        missing_columns = []
        
        for col in required_columns:
            if col not in df.columns:
                missing_columns.append(col)
        
        return missing_columns
    
    def process_temporal_data(self, df):
        """Processa dados temporais e limpa o dataset"""
        try:
            df_processed = df.copy()
            
            # Converter Data Movimento para datetime - incluindo segundos
            df_processed['Data Movimento'] = pd.to_datetime(
                df_processed['Data Movimento'], 
                format='%d/%m/%Y %H:%M:%S',
                errors='coerce'
            )
            
            # Se não funcionou com segundos, tentar sem segundos
            if df_processed['Data Movimento'].isna().all():
                df_processed['Data Movimento'] = pd.to_datetime(
                    df_processed['Data Movimento'], 
                    format='%d/%m/%Y %H:%M',
                    errors='coerce'
                )
            
            # Se ainda não funcionou, tentar formato automático
            if df_processed['Data Movimento'].isna().all():
                df_processed['Data Movimento'] = pd.to_datetime(
                    df_processed['Data Movimento'], 
                    errors='coerce',
                    dayfirst=True
                )
            
            # Remover linhas com data inválida
            df_processed = df_processed.dropna(subset=['Data Movimento'])
            
            # Converter Quantidade para numérico
            df_processed['Quantidade'] = pd.to_numeric(
                df_processed['Quantidade'], 
                errors='coerce'
            )
            
            # Remover linhas com quantidade inválida
            df_processed = df_processed.dropna(subset=['Quantidade'])
            
            # Criar colunas auxiliares para análise temporal
            df_processed['Dia'] = df_processed['Data Movimento'].dt.day  # Extrair o dia (1-31)
            df_processed['Hora'] = df_processed['Data Movimento'].dt.hour  # Extrair a hora (0-23)
            df_processed['Mes'] = df_processed['Data Movimento'].dt.month  # Extrair o mês
            df_processed['Ano'] = df_processed['Data Movimento'].dt.year  # Extrair o ano
            df_processed['Dia_Semana'] = df_processed['Data Movimento'].dt.day_name()
            df_processed['Data'] = df_processed['Data Movimento'].dt.date
            
            # Criar uma chave combinada para agrupamentos mais específicos
            df_processed['Dia_Hora'] = df_processed['Dia'].astype(str) + '_' + df_processed['Hora'].astype(str)
            
            # Ordenar por data
            df_processed = df_processed.sort_values('Data Movimento')
            
            return df_processed
        
        except Exception as e:
            st.error(f"Erro ao processar dados temporais: {str(e)}")
            return None
    
    def apply_filters(self, df, selected_projects, start_date, end_date):
        """Aplica filtros de projeto e período"""
        df_filtered = df.copy()
        
        # Filtro por linha de projeto
        df_filtered = df_filtered[df_filtered['Linha ATO'].isin(selected_projects)]
        
        # Filtro por período
        df_filtered = df_filtered[
            (df_filtered['Data Movimento'].dt.date >= start_date) &
            (df_filtered['Data Movimento'].dt.date <= end_date)
        ]
        
        return df_filtered
    
    def detect_peaks_by_project(self, df):
        """Detecta picos de entrada/saída por projeto"""
        peaks_data = {}
        
        for project in df['Linha ATO'].unique():
            project_data = df[df['Linha ATO'] == project].copy()
            
            if len(project_data) < 3:  # Precisa de pelo menos 3 pontos para detectar picos
                continue
            
            # Separar entrada e saída e agrupar por hora
            entrada_data = project_data[project_data['Tipo_Movimento'] == 'Entrada'].groupby(
                project_data[project_data['Tipo_Movimento'] == 'Entrada']['Data Movimento'].dt.floor('H')
            )['Quantidade'].sum().reset_index()
            
            saida_data = project_data[project_data['Tipo_Movimento'] == 'Saída'].groupby(
                project_data[project_data['Tipo_Movimento'] == 'Saída']['Data Movimento'].dt.floor('H')
            )['Quantidade'].sum().reset_index()
            
            # Detectar picos para entrada
            if len(entrada_data) >= 3:
                entrada_quantities = entrada_data['Quantidade'].values
                peaks_entrada, _ = find_peaks(
                    entrada_quantities, 
                    height=np.percentile(entrada_quantities, 75) if len(entrada_quantities) > 0 else 0,
                    distance=2
                )
            else:
                peaks_entrada = np.array([])
            
            # Detectar picos para saída (trabalhar com valores absolutos)
            if len(saida_data) >= 3:
                saida_quantities = abs(saida_data['Quantidade'].values)
                peaks_saida, _ = find_peaks(
                    saida_quantities,
                    height=np.percentile(saida_quantities, 75) if len(saida_quantities) > 0 else 0,
                    distance=2
                )
            else:
                peaks_saida = np.array([])
            
            peaks_data[project] = {
                'entrada_data': entrada_data,
                'saida_data': saida_data,
                'peaks_entrada': peaks_entrada,
                'peaks_saida': peaks_saida,
                'values_entrada': entrada_data.iloc[peaks_entrada]['Quantidade'].values if len(peaks_entrada) > 0 and len(entrada_data) > 0 else np.array([]),
                'values_saida': saida_data.iloc[peaks_saida]['Quantidade'].values if len(peaks_saida) > 0 and len(saida_data) > 0 else np.array([]),
                'dates_entrada': entrada_data.iloc[peaks_entrada]['Data Movimento'].values if len(peaks_entrada) > 0 and len(entrada_data) > 0 else np.array([]),
                'dates_saida': saida_data.iloc[peaks_saida]['Data Movimento'].values if len(peaks_saida) > 0 and len(saida_data) > 0 else np.array([])
            }
        
        return peaks_data
    
    def create_peaks_summary(self, peaks_data):
        """Cria resumo dos picos detectados"""
        peaks_list = []
        
        for project, data in peaks_data.items():
            # Picos de entrada
            for i, (date, value) in enumerate(zip(data['dates_entrada'], data['values_entrada'])):
                peaks_list.append({
                    'Linha ATO': project,
                    'Tipo': 'Pico Entrada',
                    'Data/Hora': pd.to_datetime(date),
                    'Valor Pico': value
                })
            
            # Picos de saída
            for i, (date, value) in enumerate(zip(data['dates_saida'], data['values_saida'])):
                peaks_list.append({
                    'Linha ATO': project,
                    'Tipo': 'Pico Saída',
                    'Data/Hora': pd.to_datetime(date),
                    'Valor Pico': abs(value)  # Mostrar como valor positivo na tabela
                })
        
        if peaks_list:
            peaks_df = pd.DataFrame(peaks_list)
            peaks_df = peaks_df.sort_values('Data/Hora')
            return peaks_df
        else:
            return pd.DataFrame()
    
    def analyze_hourly_patterns(self, df):
        """Analisa padrões por hora do dia"""
        hourly_analysis = df.groupby(['Linha ATO', 'Hora']).agg({
            'Quantidade': ['sum', 'mean', 'count']
        }).reset_index()
        
        # Flatten column names
        hourly_analysis.columns = ['Linha ATO', 'Hora', 'Total', 'Media', 'Contagem']
        
        return hourly_analysis
    
    def analyze_hourly_patterns_with_type(self, df):
        """Analisa padrões por hora do dia com tipo de movimento"""
        hourly_analysis = df.groupby(['Linha ATO', 'Hora', 'Tipo_Movimento']).agg({
            'Quantidade': ['sum', 'mean', 'count']
        }).reset_index()
        
        # Flatten column names
        hourly_analysis.columns = ['Linha ATO', 'Hora', 'Tipo_Movimento', 'Total', 'Media', 'Contagem']
        
        # Tornar valores de saída positivos para visualização
        hourly_analysis.loc[hourly_analysis['Tipo_Movimento'] == 'Saída', 'Total'] = \
            abs(hourly_analysis.loc[hourly_analysis['Tipo_Movimento'] == 'Saída', 'Total'])
        
        return hourly_analysis
    
    def analyze_daily_patterns_by_day_number_with_type(self, df):
        """Analisa padrões por dia do mês com tipo de movimento"""
        daily_analysis = df.groupby(['Linha ATO', 'Dia', 'Tipo_Movimento']).agg({
            'Quantidade': ['sum', 'mean', 'count']
        }).reset_index()
        
        # Flatten column names
        daily_analysis.columns = ['Linha ATO', 'Dia', 'Tipo_Movimento', 'Total', 'Media', 'Contagem']
        
        # Tornar valores de saída positivos para visualização
        daily_analysis.loc[daily_analysis['Tipo_Movimento'] == 'Saída', 'Total'] = \
            abs(daily_analysis.loc[daily_analysis['Tipo_Movimento'] == 'Saída', 'Total'])
        
        return daily_analysis
    
    def analyze_daily_patterns(self, df):
        """Analisa padrões por dia da semana"""
        # Definir ordem dos dias da semana em português
        dias_ordem = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        dias_pt = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
        
        daily_analysis = df.groupby(['Linha ATO', 'Dia_Semana']).agg({
            'Quantidade': ['sum', 'mean', 'count']
        }).reset_index()
        
        # Flatten column names
        daily_analysis.columns = ['Linha ATO', 'Dia_Semana', 'Total', 'Media', 'Contagem']
        
        # Traduzir dias da semana
        dia_map = dict(zip(dias_ordem, dias_pt))
        daily_analysis['Dia_Semana_PT'] = daily_analysis['Dia_Semana'].map(dia_map)
        
        # Ordenar por dia da semana
        daily_analysis['Dia_Ordem'] = daily_analysis['Dia_Semana'].map(
            lambda x: dias_ordem.index(x) if x in dias_ordem else 7
        )
        daily_analysis = daily_analysis.sort_values(['Linha ATO', 'Dia_Ordem'])
        
        return daily_analysis
    
    def create_project_summary(self, df):
        """Cria resumo estatístico por projeto"""
        summary = df.groupby('Linha ATO').agg({
            'Quantidade': ['sum', 'mean', 'std', 'min', 'max', 'count'],
            'Data Movimento': ['min', 'max']
        }).reset_index()
        
        # Flatten column names
        summary.columns = [
            'Linha ATO', 'Total Quantidade', 'Média Quantidade', 'Desvio Padrão',
            'Mínimo Quantidade', 'Máximo Quantidade', 'Contagem Registros',
            'Primeira Data', 'Última Data'
        ]
        
        # Calcular período em dias
        summary['Período (dias)'] = (
            summary['Última Data'] - summary['Primeira Data']
        ).dt.days + 1
        
        # Arredondar valores numéricos
        numeric_columns = ['Total Quantidade', 'Média Quantidade', 'Desvio Padrão']
        for col in numeric_columns:
            summary[col] = summary[col].round(2)
        
        return summary
    
    def process_cobertura_data(self, df):
        """Processa dados de cobertura com data atual"""
        try:
            df_processed = df.copy()
            
            # Adicionar data atual para cada registro
            df_processed['Data_Processamento'] = date.today()
            
            # Converter Data Alteração se existir
            if 'Data Alteração' in df_processed.columns:
                df_processed['Data Alteração'] = pd.to_datetime(
                    df_processed['Data Alteração'], 
                    errors='coerce',
                    dayfirst=True
                )
            
            # Converter campos numéricos
            numeric_columns = ['Necessidade', 'Balance', 'Consumo(Pico)', 'Dias de Visão', 
                             'Lead Time', 'E.S (%)', 'Lote', 'Qtde. Circuitos', 
                             'Qtde. Kanbans', 'Saldo Atual', 'Concluídos', 'Em Processo']
            
            for col in numeric_columns:
                if col in df_processed.columns:
                    df_processed[col] = pd.to_numeric(df_processed[col], errors='coerce')
            
            return df_processed
        
        except Exception as e:
            st.error(f"Erro ao processar dados de cobertura: {str(e)}")
            return None
    
    def analyze_cobertura_levels(self, df):
        """Analisa níveis de cobertura"""
        if 'Nível de Cobertura' not in df.columns:
            return pd.DataFrame()
        
        cobertura_counts = df['Nível de Cobertura'].value_counts().reset_index()
        cobertura_counts.columns = ['Nível de Cobertura', 'Quantidade']
        
        # Calcular percentual
        total = cobertura_counts['Quantidade'].sum()
        cobertura_counts['Percentual'] = (cobertura_counts['Quantidade'] / total * 100).round(2)
        
        return cobertura_counts
    
    def analyze_critical_items_over_time(self, df):
        """Analisa itens críticos ao longo do tempo"""
        # Assumir que 'Crítico' é um dos níveis de cobertura
        critical_data = df[df['Nível de Cobertura'].str.contains('crítico|Crítico|CRÍTICO', na=False)]
        
        if len(critical_data) == 0:
            return pd.DataFrame()
        
        # Se temos Data Alteração, usar ela, senão usar Data_Processamento
        date_column = 'Data Alteração' if 'Data Alteração' in critical_data.columns else 'Data_Processamento'
        
        # Agrupar por data
        if date_column == 'Data Alteração':
            critical_timeline = critical_data.groupby(
                critical_data[date_column].dt.date
            ).size().reset_index()
            critical_timeline.columns = ['Data', 'Quantidade_Critica']
        else:
            critical_timeline = critical_data.groupby(date_column).size().reset_index()
            critical_timeline.columns = ['Data', 'Quantidade_Critica']
        
        return critical_timeline
    
    def get_critical_summary(self, df):
        """Cria resumo de itens críticos"""
        critical_data = df[df['Nível de Cobertura'].str.contains('crítico|Crítico|CRÍTICO', na=False)]
        
        if len(critical_data) == 0:
            return {
                'total_critical': 0,
                'critical_by_line': pd.DataFrame(),
                'critical_by_area': pd.DataFrame()
            }
        
        total_critical = len(critical_data)
        
        # Por linha ATO
        critical_by_line = critical_data.groupby('Linha de ATO').size().reset_index()
        critical_by_line.columns = ['Linha de ATO', 'Quantidade_Critica']
        critical_by_line = critical_by_line.sort_values('Quantidade_Critica', ascending=False)
        
        # Por área
        critical_by_area = critical_data.groupby('Área').size().reset_index()
        critical_by_area.columns = ['Área', 'Quantidade_Critica']
        critical_by_area = critical_by_area.sort_values('Quantidade_Critica', ascending=False)
        
        return {
            'total_critical': total_critical,
            'critical_by_line': critical_by_line,
            'critical_by_area': critical_by_area
        }
