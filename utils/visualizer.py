import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

class Visualizer:
    def __init__(self):
        # Paleta de cores personalizada
        self.colors = px.colors.qualitative.Set3
    
    def create_timeline_chart(self, df):
        """Cria gráfico de linha temporal por projeto com entrada/saída"""
        # Agrupar dados por hora, projeto e tipo de movimento
        hourly_data = df.groupby([
            df['Data Movimento'].dt.floor('H'), 
            'Linha ATO',
            'Tipo_Movimento'
        ])['Quantidade'].sum().reset_index()
        
        # Criar gráfico com cores diferentes para entrada e saída
        fig = px.line(
            hourly_data,
            x='Data Movimento',
            y='Quantidade',
            color='Linha ATO',
            line_dash='Tipo_Movimento',
            title='📈 Evolução Temporal: Entrada vs Saída por Linha de Projeto',
            labels={
                'Data Movimento': 'Data e Hora',
                'Quantidade': 'Quantidade (+ Entrada, - Saída)',
                'Linha ATO': 'Linha de Projeto',
                'Tipo_Movimento': 'Tipo'
            }
        )
        
        fig.update_layout(
            height=600,
            hovermode='x unified',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        fig.update_traces(
            mode='lines+markers',
            marker=dict(size=4),
            line=dict(width=2)
        )
        
        # Adicionar linha horizontal no zero para referência
        fig.add_hline(y=0, line_dash="dot", line_color="gray", opacity=0.5)
        
        return fig
    
    def create_entrada_saida_comparison_chart(self, df):
        """Cria gráfico comparativo entre entrada e saída"""
        # Agrupar por dia e tipo de movimento
        daily_comparison = df.groupby([
            df['Data Movimento'].dt.date,
            'Linha ATO',
            'Tipo_Movimento'
        ])['Quantidade'].sum().reset_index()
        
        # Tornar valores de saída positivos para melhor visualização
        daily_comparison.loc[daily_comparison['Tipo_Movimento'] == 'Saída', 'Quantidade'] = \
            abs(daily_comparison.loc[daily_comparison['Tipo_Movimento'] == 'Saída', 'Quantidade'])
        
        fig = px.bar(
            daily_comparison,
            x='Data Movimento',
            y='Quantidade',
            color='Tipo_Movimento',
            facet_col='Linha ATO',
            facet_col_wrap=2,
            title='📊 Comparação Diária: Entrada vs Saída por Linha de Projeto',
            labels={
                'Data Movimento': 'Data',
                'Quantidade': 'Quantidade',
                'Tipo_Movimento': 'Tipo'
            },
            color_discrete_map={'Entrada': 'green', 'Saída': 'red'}
        )
        
        fig.update_layout(
            height=800,
            showlegend=True
        )
        
        return fig
    
    def create_peaks_chart(self, df, peaks_data):
        """Cria gráfico destacando os picos detectados para entrada e saída"""
        fig = go.Figure()
        
        color_idx = 0
        
        for project, data in peaks_data.items():
            color = self.colors[color_idx % len(self.colors)]
            
            # Linha de entrada
            if len(data['entrada_data']) > 0:
                fig.add_trace(go.Scatter(
                    x=data['entrada_data']['Data Movimento'],
                    y=data['entrada_data']['Quantidade'],
                    mode='lines+markers',
                    name=f'{project} - Entrada',
                    line=dict(color=color, width=2, dash='solid'),
                    marker=dict(size=4)
                ))
                
                # Picos de entrada
                if len(data['peaks_entrada']) > 0:
                    fig.add_trace(go.Scatter(
                        x=data['dates_entrada'],
                        y=data['values_entrada'],
                        mode='markers',
                        name=f'{project} - Picos Entrada',
                        marker=dict(
                            color='green',
                            size=12,
                            symbol='triangle-up',
                            line=dict(color='darkgreen', width=2)
                        ),
                        showlegend=False
                    ))
            
            # Linha de saída
            if len(data['saida_data']) > 0:
                fig.add_trace(go.Scatter(
                    x=data['saida_data']['Data Movimento'],
                    y=data['saida_data']['Quantidade'],
                    mode='lines+markers',
                    name=f'{project} - Saída',
                    line=dict(color=color, width=2, dash='dash'),
                    marker=dict(size=4)
                ))
                
                # Picos de saída
                if len(data['peaks_saida']) > 0:
                    fig.add_trace(go.Scatter(
                        x=data['dates_saida'],
                        y=data['values_saida'],
                        mode='markers',
                        name=f'{project} - Picos Saída',
                        marker=dict(
                            color='red',
                            size=12,
                            symbol='triangle-down',
                            line=dict(color='darkred', width=2)
                        ),
                        showlegend=False
                    ))
            
            color_idx += 1
        
        fig.update_layout(
            title='⚡ Picos de Entrada/Saída Detectados por Linha de Projeto',
            xaxis_title='Data e Hora',
            yaxis_title='Quantidade',
            height=600,
            hovermode='x unified',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        # Adicionar linha horizontal no zero para referência
        fig.add_hline(y=0, line_dash="dot", line_color="gray", opacity=0.5)
        
        # Adicionar anotações explicativas
        fig.add_annotation(
            x=0.02, y=0.98,
            xref="paper", yref="paper",
            text="🔺 Picos Entrada | 🔻 Picos Saída | —— Entrada | - - Saída",
            showarrow=False,
            font=dict(size=12, color="gray"),
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor="gray",
            borderwidth=1
        )
        
        return fig
    
    def create_hourly_analysis_chart(self, hourly_data):
        """Cria gráfico de análise por hora do dia"""
        fig = px.bar(
            hourly_data,
            x='Hora',
            y='Total',
            color='Linha ATO',
            title='🕐 Distribuição de Quantidade por Hora do Dia',
            labels={
                'Hora': 'Hora do Dia',
                'Total': 'Quantidade Total',
                'Linha ATO': 'Linha de Projeto'
            },
            barmode='group'
        )
        
        fig.update_layout(
            height=500,
            xaxis=dict(
                tickmode='linear',
                tick0=0,
                dtick=1,
                title='Hora do Dia (0-23)'
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        return fig
    
    def create_daily_analysis_chart(self, daily_data):
        """Cria gráfico de análise por dia da semana"""
        fig = px.bar(
            daily_data,
            x='Dia_Semana_PT',
            y='Total',
            color='Linha ATO',
            title='📅 Distribuição de Quantidade por Dia da Semana',
            labels={
                'Dia_Semana_PT': 'Dia da Semana',
                'Total': 'Quantidade Total',
                'Linha ATO': 'Linha de Projeto'
            },
            barmode='group',
            category_orders={
                'Dia_Semana_PT': ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
            }
        )
        
        fig.update_layout(
            height=500,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        return fig
    
    def create_daily_number_analysis_chart(self, daily_data):
        """Cria gráfico de análise por dia do mês (1-31)"""
        fig = px.bar(
            daily_data,
            x='Dia',
            y='Total',
            color='Linha ATO',
            title='📅 Distribuição de Quantidade por Dia do Mês',
            labels={
                'Dia': 'Dia do Mês',
                'Total': 'Quantidade Total',
                'Linha ATO': 'Linha de Projeto'
            },
            barmode='group'
        )
        
        fig.update_layout(
            height=500,
            xaxis=dict(
                tickmode='linear',
                tick0=1,
                dtick=1,
                title='Dia do Mês (1-31)'
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        return fig
    
    def create_day_hour_heatmap(self, df):
        """Cria mapa de calor combinando dia do mês e hora"""
        # Criar pivot table para heatmap
        df_pivot = df.pivot_table(
            values='Quantidade',
            index='Hora',
            columns='Dia',
            aggfunc='sum',
            fill_value=0
        )
        
        fig = go.Figure(data=go.Heatmap(
            z=df_pivot.values,
            x=df_pivot.columns,
            y=df_pivot.index,
            colorscale='Viridis',
            hoverongaps=False,
            colorbar=dict(title="Quantidade"),
            hovertemplate='Dia: %{x}<br>Hora: %{y}<br>Quantidade: %{z}<extra></extra>'
        ))
        
        fig.update_layout(
            title='🔥 Mapa de Calor: Quantidade por Dia do Mês e Hora',
            xaxis_title='Dia do Mês',
            yaxis_title='Hora do Dia',
            height=500,
            xaxis=dict(
                tickmode='linear',
                tick0=1,
                dtick=1
            ),
            yaxis=dict(
                tickmode='linear',
                tick0=0,
                dtick=1
            )
        )
        
        return fig
    
    def create_hourly_entrada_saida_chart(self, hourly_data):
        """Cria gráfico de análise por hora separando entrada e saída"""
        fig = px.bar(
            hourly_data,
            x='Hora',
            y='Total',
            color='Tipo_Movimento',
            facet_col='Linha ATO',
            facet_col_wrap=2,
            title='🕐 Distribuição por Hora: Entrada vs Saída',
            labels={
                'Hora': 'Hora do Dia',
                'Total': 'Quantidade Total',
                'Tipo_Movimento': 'Tipo'
            },
            barmode='group',
            color_discrete_map={'Entrada': 'green', 'Saída': 'red'}
        )
        
        fig.update_layout(
            height=600,
            xaxis=dict(
                tickmode='linear',
                tick0=0,
                dtick=1,
                title='Hora do Dia (0-23)'
            )
        )
        
        return fig
    
    def create_daily_number_entrada_saida_chart(self, daily_data):
        """Cria gráfico de análise por dia do mês separando entrada e saída"""
        fig = px.bar(
            daily_data,
            x='Dia',
            y='Total',
            color='Tipo_Movimento',
            facet_col='Linha ATO',
            facet_col_wrap=2,
            title='📅 Distribuição por Dia do Mês: Entrada vs Saída',
            labels={
                'Dia': 'Dia do Mês',
                'Total': 'Quantidade Total',
                'Tipo_Movimento': 'Tipo'
            },
            barmode='group',
            color_discrete_map={'Entrada': 'green', 'Saída': 'red'}
        )
        
        fig.update_layout(
            height=600,
            xaxis=dict(
                tickmode='linear',
                tick0=1,
                dtick=1,
                title='Dia do Mês (1-31)'
            )
        )
        
        return fig
    
    def create_heatmap_chart(self, df):
        """Cria mapa de calor para análise temporal"""
        # Criar pivot table para heatmap
        df_pivot = df.pivot_table(
            values='Quantidade',
            index=df['Data Movimento'].dt.hour,
            columns=df['Data Movimento'].dt.day_name(),
            aggfunc='sum',
            fill_value=0
        )
        
        # Reordenar colunas (dias da semana)
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        day_order_pt = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
        
        available_days = [day for day in day_order if day in df_pivot.columns]
        df_pivot = df_pivot[available_days]
        
        # Renomear colunas para português
        column_mapping = dict(zip(day_order, day_order_pt))
        df_pivot.columns = [column_mapping.get(col, col) for col in df_pivot.columns]
        
        fig = go.Figure(data=go.Heatmap(
            z=df_pivot.values,
            x=df_pivot.columns,
            y=df_pivot.index,
            colorscale='Viridis',
            hoverongaps=False,
            colorbar=dict(title="Quantidade")
        ))
        
        fig.update_layout(
            title='🔥 Mapa de Calor: Quantidade por Hora e Dia da Semana',
            xaxis_title='Dia da Semana',
            yaxis_title='Hora do Dia',
            height=500
        )
        
        return fig
    
    def create_comparison_chart(self, df, metric='sum'):
        """Cria gráfico de comparação entre projetos"""
        if metric == 'sum':
            agg_data = df.groupby('Linha ATO')['Quantidade'].sum().reset_index()
            title = '📊 Comparação de Quantidade Total por Linha de Projeto'
            y_label = 'Quantidade Total'
        elif metric == 'mean':
            agg_data = df.groupby('Linha ATO')['Quantidade'].mean().reset_index()
            title = '📊 Comparação de Quantidade Média por Linha de Projeto'
            y_label = 'Quantidade Média'
        else:  # count
            agg_data = df.groupby('Linha ATO')['Quantidade'].count().reset_index()
            title = '📊 Comparação de Número de Registros por Linha de Projeto'
            y_label = 'Número de Registros'
        
        # Ordenar por valor
        agg_data = agg_data.sort_values('Quantidade', ascending=False)
        
        fig = px.bar(
            agg_data,
            x='Linha ATO',
            y='Quantidade',
            title=title,
            labels={
                'Linha ATO': 'Linha de Projeto',
                'Quantidade': y_label
            },
            text='Quantidade'
        )
        
        fig.update_traces(
            texttemplate='%{text:.0f}',
            textposition='outside'
        )
        
        fig.update_layout(
            height=500,
            xaxis_tickangle=-45
        )
        
        return fig
