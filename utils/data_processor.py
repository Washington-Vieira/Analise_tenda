import pandas as pd
import numpy as np
from datetime import datetime, timedelta
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
            
            # Agrupar por hora para suavizar os dados
            hourly_data = project_data.groupby(
                project_data['Data Movimento'].dt.floor('H')
            )['Quantidade'].sum().reset_index()
            
            if len(hourly_data) < 3:
                continue
            
            # Detectar picos usando scipy
            quantities = hourly_data['Quantidade'].values
            
            # Picos positivos (máximos locais)
            peaks_pos, properties_pos = find_peaks(
                quantities, 
                height=np.percentile(quantities, 75),  # Apenas picos acima do 75º percentil
                distance=2  # Distância mínima entre picos
            )
            
            # Picos negativos (mínimos locais) - invertemos os valores
            peaks_neg, properties_neg = find_peaks(
                -quantities,
                height=-np.percentile(quantities, 25),  # Apenas vales abaixo do 25º percentil
                distance=2
            )
            
            peaks_data[project] = {
                'data': hourly_data,
                'peaks_high': peaks_pos,
                'peaks_low': peaks_neg,
                'values_high': quantities[peaks_pos] if len(peaks_pos) > 0 else np.array([]),
                'values_low': quantities[peaks_neg] if len(peaks_neg) > 0 else np.array([]),
                'dates_high': hourly_data.iloc[peaks_pos]['Data Movimento'].values if len(peaks_pos) > 0 else np.array([]),
                'dates_low': hourly_data.iloc[peaks_neg]['Data Movimento'].values if len(peaks_neg) > 0 else np.array([])
            }
        
        return peaks_data
    
    def create_peaks_summary(self, peaks_data):
        """Cria resumo dos picos detectados"""
        peaks_list = []
        
        for project, data in peaks_data.items():
            # Picos altos
            for i, (date, value) in enumerate(zip(data['dates_high'], data['values_high'])):
                peaks_list.append({
                    'Linha ATO': project,
                    'Tipo': 'Pico Alto',
                    'Data/Hora': pd.to_datetime(date),
                    'Valor Pico': value
                })
            
            # Picos baixos
            for i, (date, value) in enumerate(zip(data['dates_low'], data['values_low'])):
                peaks_list.append({
                    'Linha ATO': project,
                    'Tipo': 'Pico Baixo',
                    'Data/Hora': pd.to_datetime(date),
                    'Valor Pico': value
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
    
    def analyze_daily_patterns_by_day_number(self, df):
        """Analisa padrões por dia do mês (1-31)"""
        daily_analysis = df.groupby(['Linha ATO', 'Dia']).agg({
            'Quantidade': ['sum', 'mean', 'count']
        }).reset_index()
        
        # Flatten column names
        daily_analysis.columns = ['Linha ATO', 'Dia', 'Total', 'Media', 'Contagem']
        
        return daily_analysis
    
    def analyze_day_hour_patterns(self, df):
        """Analisa padrões combinando dia do mês e hora"""
        day_hour_analysis = df.groupby(['Linha ATO', 'Dia', 'Hora']).agg({
            'Quantidade': ['sum', 'mean', 'count']
        }).reset_index()
        
        # Flatten column names
        day_hour_analysis.columns = ['Linha ATO', 'Dia', 'Hora', 'Total', 'Media', 'Contagem']
        
        # Criar coluna combinada para visualização
        day_hour_analysis['Dia_Hora'] = day_hour_analysis['Dia'].astype(str) + 'h' + day_hour_analysis['Hora'].astype(str).str.zfill(2)
        
        return day_hour_analysis
    
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
