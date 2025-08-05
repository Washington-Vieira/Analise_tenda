import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
import streamlit as st
import os
from scipy.signal import find_peaks
import warnings
import requests
from github import Github
from base64 import b64encode, b64decode
import json
from io import BytesIO

class GitHubManager:
    def __init__(self, token=None, repo_name=None):
        """
        Inicializa o gerenciador do GitHub
        :param token: Token de acesso do GitHub
        :param repo_name: Nome do repositório no formato 'usuario/repositorio'
        """
        self.token = token or st.secrets.get("GITHUB_TOKEN")
        self.repo_name = repo_name or st.secrets.get("GITHUB_REPO")
        self._github = None
        self._repo = None
    
    @property
    def github(self):
        if not self._github:
            if not self.token:
                raise ValueError("GitHub token não configurado. Configure em .streamlit/secrets.toml")
            self._github = Github(self.token)
        return self._github
    
    @property
    def repo(self):
        if not self._repo:
            if not self.repo_name:
                raise ValueError("Nome do repositório não configurado. Configure em .streamlit/secrets.toml")
            self._repo = self.github.get_repo(self.repo_name)
        return self._repo
    
    def save_file(self, file_path, content, commit_message):
        """
        Salva ou atualiza um arquivo no GitHub
        :param file_path: Caminho do arquivo no repositório
        :param content: Conteúdo do arquivo
        :param commit_message: Mensagem do commit
        """
        try:
            # Verificar se o arquivo já existe
            try:
                file = self.repo.get_contents(file_path)
                # Atualizar arquivo existente
                self.repo.update_file(
                    file.path,
                    commit_message,
                    content,
                    file.sha
                )
                st.success(f"✅ Arquivo {file_path} atualizado no GitHub com sucesso!")
            except:
                # Criar novo arquivo
                self.repo.create_file(
                    file_path,
                    commit_message,
                    content
                )
                st.success(f"✅ Arquivo {file_path} criado no GitHub com sucesso!")
        except Exception as e:
            st.error(f"❌ Erro ao salvar arquivo no GitHub: {str(e)}")
    
    def load_file(self, file_path):
        """
        Carrega um arquivo do GitHub
        :param file_path: Caminho do arquivo no repositório
        :return: Conteúdo do arquivo
        """
        try:
            file = self.repo.get_contents(file_path)
            content = b64decode(file.content).decode('utf-8')
            return content
        except Exception as e:
            st.warning(f"⚠️ Arquivo {file_path} não encontrado no GitHub: {str(e)}")
            return None

warnings.filterwarnings('ignore')

class DataProcessor:
    def __init__(self):
        self.df = None
        self.history_file = "historico_criticos.xlsx"
        self.github = GitHubManager()
    
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
    
    def validate_cobertura_columns(self, df):
        """Validação específica e flexível para arquivo de cobertura"""
        # Colunas obrigatórias básicas
        essential_columns = ['Nível de Cobertura']
        
        # Verificar se pelo menos a coluna de nível de cobertura existe
        if 'Nível de Cobertura' not in df.columns:
            # Tentar encontrar colunas similares
            similar_columns = [col for col in df.columns if 'cobertura' in col.lower() or 'nivel' in col.lower()]
            if similar_columns:
                return {'missing': ['Nível de Cobertura'], 'suggestions': similar_columns}
            else:
                return {'missing': ['Nível de Cobertura'], 'suggestions': []}
        
        # Se tem a coluna principal, arquivo é válido
        return {'missing': [], 'suggestions': []}
    
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

        # Detectar qual coluna de data usar
        date_col = None
        if 'Data Movimento' in df_filtered.columns:
            date_col = 'Data Movimento'
        elif 'Data_Processamento' in df_filtered.columns:
            date_col = 'Data_Processamento'
        else:
            st.error("Nenhuma coluna de data encontrada para filtrar.")
            return df_filtered

        # Converter start_date e end_date para datetime.date se forem Timestamp
        if hasattr(start_date, 'date'):
            start_date = start_date.date()
        if hasattr(end_date, 'date'):
            end_date = end_date.date()

        # Converter coluna de data para datetime.date se necessário
        col_data = pd.to_datetime(df_filtered[date_col])
        col_data_date = col_data.dt.date if hasattr(col_data.dt, 'date') else col_data
        mask = (col_data_date >= start_date) & (col_data_date <= end_date)
        df_filtered = df_filtered[mask]

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
        try:
            # Garantir que temos a coluna Dia
            if 'Dia' not in df.columns:
                df = df.copy()
                df['Dia'] = df['Data Movimento'].dt.day
            
            daily_analysis = df.groupby(['Linha ATO', 'Dia', 'Tipo_Movimento']).agg({
                'Quantidade': ['sum', 'mean', 'count']
            }).reset_index()
            
            # Flatten column names
            daily_analysis.columns = ['Linha ATO', 'Dia', 'Tipo_Movimento', 'Total', 'Media', 'Contagem']
            
            # Tornar valores de saída positivos para visualização
            daily_analysis.loc[daily_analysis['Tipo_Movimento'] == 'Saída', 'Total'] = \
                abs(daily_analysis.loc[daily_analysis['Tipo_Movimento'] == 'Saída', 'Total'])
            
            return daily_analysis
        except Exception as e:
            st.error(f"Erro ao processar análise diária: {str(e)}")
            return pd.DataFrame()
    
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
            
            # Adicionar data atual para cada registro como Timestamp
            df_processed['Data_Processamento'] = pd.Timestamp(date.today())
            
            # Converter Data Alteração se existir (diferentes possibilidades de nome)
            date_columns = ['Data Alteração', 'Data_Alteracao', 'Data Alteracao', 
                          'Data de Alteração', 'Data de Alteracao', 'Data']
            
            for date_col in date_columns:
                if date_col in df_processed.columns:
                    try:
                        df_processed[date_col] = pd.to_datetime(
                            df_processed[date_col], 
                            errors='coerce',
                            dayfirst=True
                        )
                        break
                    except:
                        continue
            
            # Converter campos numéricos possíveis
            numeric_columns = ['Necessidade', 'Balance', 'Consumo(Pico)', 'Dias de Visão', 
                             'Lead Time', 'E.S (%)', 'Lote', 'Qtde. Circuitos', 
                             'Qtde. Kanbans', 'Saldo Atual', 'Concluídos', 'Em Processo',
                             'Quantidade', 'Qtd', 'Valor', 'Estoque', 'Demanda']
            
            for col in numeric_columns:
                if col in df_processed.columns:
                    try:
                        df_processed[col] = pd.to_numeric(df_processed[col], errors='coerce')
                    except:
                        continue
            
            return df_processed
        
        except Exception as e:
            st.error(f"Erro ao processar dados de cobertura: {str(e)}")
            st.error(f"Detalhes do erro: {type(e).__name__}")
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
    
    def save_critical_history(self, total_items, total_critical):
        """
        Salva o histórico de itens críticos em uma planilha local e no GitHub
        """
        today = pd.Timestamp(date.today())
        percentage = (total_critical / total_items * 100) if total_items > 0 else 0

        # Tentar carregar histórico existente do GitHub
        try:
            content = self.github.load_file(self.history_file)
            if content:
                # Salvar conteúdo em arquivo temporário
                with open("temp_history.xlsx", "wb") as f:
                    f.write(b64decode(content))
                df_history = pd.read_excel("temp_history.xlsx")
                os.remove("temp_history.xlsx")  # Limpar arquivo temporário
            else:
                df_history = pd.DataFrame(columns=['Data', 'Percentual', 'Total_Items', 'Items_Criticos'])
        except:
            # Se falhar, tentar carregar arquivo local
            if os.path.exists(self.history_file):
                df_history = pd.read_excel(self.history_file)
            else:
                df_history = pd.DataFrame(columns=['Data', 'Percentual', 'Total_Items', 'Items_Criticos'])

        # Converter coluna de data para datetime
        if not df_history.empty:
            df_history['Data'] = pd.to_datetime(df_history['Data'])

        # Verificar se já existe entrada para hoje
        if not df_history.empty:
            # Comparar apenas as datas (ignorando o horário)
            if (df_history['Data'].dt.date == today.date()).any():
                # Atualizar entrada existente
                mask = df_history['Data'].dt.date == today.date()
                df_history.loc[mask, 'Percentual'] = percentage
                df_history.loc[mask, 'Total_Items'] = total_items
                df_history.loc[mask, 'Items_Criticos'] = total_critical
            else:
                # Adicionar nova entrada
                new_row = pd.DataFrame({
                    'Data': [today],
                    'Percentual': [percentage],
                    'Total_Items': [total_items],
                    'Items_Criticos': [total_critical]
                })
                df_history = pd.concat([df_history, new_row], ignore_index=True)
        else:
            # Adicionar primeira entrada
            df_history = pd.DataFrame({
                'Data': [today],
                'Percentual': [percentage],
                'Total_Items': [total_items],
                'Items_Criticos': [total_critical]
            })

        # Ordenar por data
        df_history = df_history.sort_values('Data')

        # Salvar localmente
        df_history.to_excel(self.history_file, index=False)

        # Salvar no GitHub
        try:
            # Criar arquivo em memória
            output = BytesIO()
            df_history.to_excel(output, index=False)
            content = output.getvalue()
            
            # Salvar no GitHub
            self.github.save_file(
                self.history_file,
                content,
                f"Atualização do histórico de itens críticos - {today.strftime('%d/%m/%Y')}"
            )
        except Exception as e:
            st.warning(f"⚠️ Não foi possível salvar no GitHub: {str(e)}")
            st.info("💡 O arquivo foi salvo apenas localmente.")

        return df_history

    def analyze_critical_items_over_time(self, df):
        """Analisa itens críticos ao longo do tempo com histórico"""
        try:
            # Carregar histórico
            if os.path.exists(self.history_file):
                historical_data = pd.read_excel(self.history_file)
                if not historical_data.empty:
                    # Garantir que a coluna Data seja datetime
                    historical_data['Data'] = pd.to_datetime(historical_data['Data'])
                    return historical_data

            # Se não houver histórico, criar com dados atuais
            critical_patterns = ['crítico', 'critico', 'Crítico', 'Critico', 'CRÍTICO', 'CRITICO']

            # Criar máscara para encontrar itens críticos (excluir BAIXO)
            critical_mask = df['Nível de Cobertura'].astype(str).str.contains(
                '|'.join(critical_patterns), 
                case=False, 
                na=False
            ) & ~df['Nível de Cobertura'].str.contains('baixo', case=False, na=False)

            critical_data = df[critical_mask]
            total_items = len(df)
            total_critical = len(critical_data)

            # Salvar no histórico
            return self.save_critical_history(total_items, total_critical)

        except Exception as e:
            st.error(f"Erro ao analisar itens críticos: {str(e)}")
            return pd.DataFrame()
    
    def get_critical_summary(self, df):
        """
        Calcula e salva o sumário de itens críticos.
        """
        critical_patterns = ['crítico', 'critico', 'Crítico', 'Critico', 'CRÍTICO', 'CRITICO', 
                           'critical', 'Critical', 'CRITICAL']
        
        # Criar máscara para encontrar itens críticos
        critical_mask = df['Nível de Cobertura'].astype(str).str.contains(
            '|'.join(critical_patterns), 
            case=False, 
            na=False
        )
        
        total_critical = len(df[critical_mask])
        total_items = len(df)
        
        # Salvar no histórico
        self.save_critical_history(total_items, total_critical)
        """Cria resumo de itens críticos"""
        try:
            # Usar os mesmos padrões da função anterior
            critical_patterns = ['crítico', 'critico', 'Crítico', 'Critico', 'CRÍTICO', 'CRITICO', 
                               'critical', 'Critical', 'CRITICAL']
            
            critical_mask = df['Nível de Cobertura'].astype(str).str.contains(
                '|'.join(critical_patterns), 
                case=False, 
                na=False
            )
            
            critical_data = df[critical_mask]
            
            if len(critical_data) == 0:
                return {
                    'total_critical': 0,
                    'critical_by_line': pd.DataFrame(),
                    'critical_by_area': pd.DataFrame()
                }
            
            total_critical = len(critical_data)
            
            # Por linha ATO (verificar se coluna existe)
            line_columns = ['Linha de ATO', 'Linha ATO', 'Linha_ATO', 'Projeto', 'Line']
            line_column = None
            for col in line_columns:
                if col in critical_data.columns:
                    line_column = col
                    break
            
            if line_column:
                critical_by_line = critical_data.groupby(line_column).size().reset_index()
                critical_by_line.columns = ['Linha de ATO', 'Quantidade_Critica']
                critical_by_line = critical_by_line.sort_values('Quantidade_Critica', ascending=False)
            else:
                critical_by_line = pd.DataFrame()
            
            # Por área (verificar se coluna existe)
            area_columns = ['Área', 'Area', 'Setor', 'Departamento']
            area_column = None
            for col in area_columns:
                if col in critical_data.columns:
                    area_column = col
                    break
            
            if area_column:
                critical_by_area = critical_data.groupby(area_column).size().reset_index()
                critical_by_area.columns = ['Área', 'Quantidade_Critica']
                critical_by_area = critical_by_area.sort_values('Quantidade_Critica', ascending=False)
            else:
                critical_by_area = pd.DataFrame()
            
            return {
                'total_critical': total_critical,
                'critical_by_line': critical_by_line,
                'critical_by_area': critical_by_area
            }
        
        except Exception as e:
            st.error(f"Erro na análise de críticos: {str(e)}")
            return {
                'total_critical': 0,
                'critical_by_line': pd.DataFrame(),
                'critical_by_area': pd.DataFrame()
            }

    def get_critical_materials_by_line(self, df):
        """Obtém os materiais críticos agrupados por linha ATO"""
        try:
            critical_patterns = ['crítico', 'critico', 'Crítico', 'Critico', 'CRÍTICO', 'CRITICO', 
                               'critical', 'Critical', 'CRITICAL']
            
            # Criar máscara para encontrar itens críticos
            critical_mask = df['Nível de Cobertura'].astype(str).str.contains(
                '|'.join(critical_patterns), 
                case=False, 
                na=False
            )
            
            # Filtrar apenas itens críticos
            critical_data = df[critical_mask].copy()
            
            # Verificar se temos as colunas necessárias
            line_columns = ['Linha de ATO', 'Linha ATO', 'Linha_ATO', 'Projeto', 'Line']
            line_column = None
            for col in line_columns:
                if col in critical_data.columns:
                    line_column = col
                    break
            
            if not line_column or 'Material' not in critical_data.columns:
                return {}
            
            # Agrupar materiais críticos por linha
            critical_materials = {}
            for linha in critical_data[line_column].unique():
                linha_data = critical_data[critical_data[line_column] == linha]
                materiais = linha_data[['Material', 'Nível de Cobertura', 'Balance', 'Necessidade']].copy()
                
                # Calcular cobertura percentual
                materiais['Cobertura %'] = (materiais['Balance'] / materiais['Necessidade'] * 100).round(2)
                
                # Ordenar por nível de cobertura e material
                materiais = materiais.sort_values(['Nível de Cobertura', 'Material'])
                
                critical_materials[linha] = materiais.to_dict('records')
            
            return critical_materials
        
        except Exception as e:
            st.error(f"Erro ao processar materiais críticos: {str(e)}")
            return {}
