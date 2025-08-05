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
            facet_col_wrap=2,  # Dois gráficos por linha
            title=None,  # Remove o título do gráfico
            labels={
                'Hora': '',  # Remove a legenda do eixo X
                'Total': '',  # Remove a legenda do eixo Y
                'Tipo_Movimento': 'Tipo'
            },
            barmode='group',
            color_discrete_map={'Entrada': 'green', 'Saída': 'red'},
            height=500,  # Altura fixa para todos os gráficos
            custom_data=['Hora', 'Total', 'Tipo_Movimento']  # Dados para o tooltip
        )
        
        # Atualizar layout
        fig.update_layout(
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            bargap=0.3,         # Espaço entre grupos de barras
            bargroupgap=0.1,    # Espaço entre barras do mesmo grupo
            margin=dict(t=50, b=50, l=50, r=50),  # Margens consistentes
            paper_bgcolor='rgba(0,0,0,0)',  # Fundo transparente
            plot_bgcolor='rgba(0,0,0,0)'    # Fundo do plot transparente
        )
        
        # Atualizar todos os subplots para mostrar todas as horas
        fig.update_xaxes(
            tickmode='array',
            ticktext=[f'{h}h' for h in range(24)],  # Adiciona 'h' após cada número
            tickvals=list(range(24)),
            dtick=1,
            showgrid=False,  # Remove as linhas de grade verticais
            title=None  # Remove o título do eixo X
        )
        
        # Atualizar eixo Y
        fig.update_yaxes(
            title='',  # Remove o título do eixo Y
            showgrid=True,  # Mostra as linhas de grade horizontais
            gridwidth=1,    # Largura das linhas de grade
            gridcolor='rgba(128, 128, 128, 0.2)',  # Cor suave para a grade
            zeroline=False  # Remove a linha do zero
        )
        
        # Configurar o tooltip personalizado
        fig.update_traces(
            hovertemplate="<b>Horário:</b> %{customdata[0]:02d}:00<br>" +
                         "<b>%{customdata[2]}:</b> %{customdata[1]:,.0f}<br>" +
                         "<extra></extra>"
        )
        
        # Simplificar os títulos dos subplots
        for annotation in fig.layout.annotations:
            if 'Linha ATO=' in annotation.text:
                annotation.text = annotation.text.replace('Linha ATO=', '')
        
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
            title=None,  # Remove o título do gráfico
            labels={
                'Dia': '',  # Remove a legenda do eixo X
                'Total': '',  # Remove a legenda do eixo Y
                'Tipo_Movimento': 'Tipo'
            },
            barmode='group',
            color_discrete_map={'Entrada': 'green', 'Saída': 'red'},
            height=500  # Mesma altura do gráfico de horas
        )
        
        # Atualizar layout
        fig.update_layout(
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            bargap=0.3,         # Mesmo espaçamento do gráfico de horas
            bargroupgap=0.1,    # Mesmo espaçamento do gráfico de horas
            margin=dict(t=50, b=50, l=50, r=50),  # Mesmas margens
            paper_bgcolor='rgba(0,0,0,0)',  # Fundo transparente
            plot_bgcolor='rgba(0,0,0,0)'    # Fundo do plot transparente
        )
        
        # Atualizar eixo X
        fig.update_xaxes(
            tickmode='linear',
            tick0=1,
            dtick=1,
            showgrid=False,  # Remove as linhas de grade verticais
            title=None  # Remove o título do eixo X
        )
        
        # Atualizar eixo Y
        fig.update_yaxes(
            title='',  # Remove o título do eixo Y
            showgrid=True,  # Mostra as linhas de grade horizontais
            gridwidth=1,    # Largura das linhas de grade
            gridcolor='rgba(128, 128, 128, 0.2)',  # Cor suave para a grade
            zeroline=False  # Remove a linha do zero
        )
        
        # Simplificar os títulos dos subplots
        for annotation in fig.layout.annotations:
            if 'Linha ATO=' in annotation.text:
                annotation.text = annotation.text.replace('Linha ATO=', '')
        
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
    
    def create_cobertura_pie_chart(self, cobertura_data):
        """Cria gráfico de pizza para níveis de cobertura"""
        # Criar cores personalizadas para cada nível
        colors = []
        
        for nivel in cobertura_data['Nível de Cobertura']:
            nivel_str = str(nivel).lower()
            if any(word in nivel_str for word in ['crítico', 'critico', 'critical']):
                colors.append('#FF0000')  # Vermelho para crítico
            elif 'baixo' in nivel_str:
                colors.append('#FFA500')  # Laranja para baixo
            elif 'excedente' in nivel_str:
                colors.append('#0000FF')  # Azul para excedente
            elif 'moderado' in nivel_str:
                colors.append('#FFFF00')  # Amarelo para moderado
            elif 'adequado' in nivel_str:
                colors.append('#008000')  # Verde para adequado
            else:
                colors.append('#808080')  # Cinza para outros casos
        
        fig = px.pie(
            cobertura_data,
            values='Quantidade',
            names='Nível de Cobertura',
            title=None,  # Remove o título do gráfico
            hover_data=['Percentual'],
            color_discrete_sequence=colors
        )
        
        fig.update_traces(
            textposition='inside',
            textinfo='percent+label',
            hovertemplate='<b>%{label}</b><br>Quantidade: %{value}<br>Percentual: %{percent}<extra></extra>'
        )
        
        fig.update_layout(
            height=500,
            showlegend=True,
            legend=dict(
                orientation="v",
                yanchor="middle",
                y=0.5,
                xanchor="left",
                x=1.01
            ),
            margin=dict(t=50, b=50, l=50, r=50),  # Margens consistentes
            paper_bgcolor='rgba(0,0,0,0)',  # Fundo transparente
            plot_bgcolor='rgba(0,0,0,0)'    # Fundo do plot transparente
        )
        
        return fig
    
    def create_critical_timeline_chart(self, critical_timeline):
        """Cria gráfico de linha temporal para itens críticos"""
        if critical_timeline.empty:
            # Criar gráfico vazio com mensagem
            fig = go.Figure()
            fig.add_annotation(
                text="Nenhum item crítico encontrado",
                xref="paper", yref="paper",
                x=0.5, y=0.5, xanchor='center', yanchor='middle',
                font=dict(size=16, color="gray")
            )
            fig.update_layout(
                height=400,
                margin=dict(t=50, b=50, l=50, r=50),  # Margens consistentes
                paper_bgcolor='rgba(0,0,0,0)',  # Fundo transparente
                plot_bgcolor='rgba(0,0,0,0)'    # Fundo do plot transparente
            )
            return fig

        # Garantir que a coluna 'Data' contenha apenas datas (sem horário)
        critical_timeline['Data'] = pd.to_datetime(critical_timeline['Data']).dt.date

        # Criar figura com dois y-axis
        fig = make_subplots(specs=[[{"secondary_y": True}]])

        # Adicionar linha de percentual
        fig.add_trace(
            go.Scatter(
                x=critical_timeline['Data'],
                y=critical_timeline['Percentual'],
                name="Percentual Crítico",
                line=dict(color='#FF0000', width=3),  # Vermelho para crítico
                mode='lines+markers',
                marker=dict(size=8, color='#FF0000'),  # Vermelho para crítico
                hovertemplate="<b>%{x}</b><br>Percentual: %{y:.2f}%<extra></extra>"
            ),
            secondary_y=True
        )

        # Adicionar linha de quantidade
        fig.add_trace(
            go.Scatter(
                x=critical_timeline['Data'],
                y=critical_timeline['Items_Criticos'],
                name="Quantidade Crítica",
                line=dict(color='#FFA500', width=3, dash='dot'),  # Laranja para quantidade
                mode='lines+markers',
                marker=dict(size=8, color='#FFA500'),  # Laranja para quantidade
                hovertemplate="<b>%{x}</b><br>Itens: %{y}<extra></extra>"
            ),
            secondary_y=False
        )

        # Atualizar layout
        fig.update_layout(
            height=400,
            hovermode='x unified',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5
            ),
            margin=dict(t=50, b=50, l=50, r=50),  # Margens consistentes
            paper_bgcolor='rgba(0,0,0,0)',  # Fundo transparente
            plot_bgcolor='rgba(0,0,0,0)'    # Fundo do plot transparente
        )

        # Atualizar eixos
        fig.update_xaxes(
            title=None,  # Remove o título do eixo X
            tickformat="%d %b",
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(128, 128, 128, 0.2)'
        )
        fig.update_yaxes(
            title=None,  # Remove o título do eixo Y
            secondary_y=False,
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(128, 128, 128, 0.2)'
        )
        fig.update_yaxes(
            title=None,  # Remove o título do eixo Y
            secondary_y=True,
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(128, 128, 128, 0.2)'
        )

        return fig
    
    def create_critical_by_line_chart(self, critical_by_line):
        """Cria gráfico de barras para itens críticos por linha"""
        if critical_by_line.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="Nenhum item crítico por linha encontrado",
                xref="paper", yref="paper",
                x=0.5, y=0.5, xanchor='center', yanchor='middle',
                font=dict(size=14, color="gray")
            )
            fig.update_layout(
                title="📊 Itens Críticos por Linha de Projeto",
                height=400
            )
            return fig
        
        fig = px.bar(
            critical_by_line.head(10),  # Top 10
            x='Quantidade_Critica',
            y='Linha de ATO',
            orientation='h',
            title='📊 Top 10 - Itens Críticos por Linha de Projeto',
            labels={
                'Quantidade_Critica': 'Quantidade de Itens Críticos',
                'Linha de ATO': 'Linha de Projeto'
            }
        )
        
        # Atualizar cor das barras para vermelho (crítico)
        fig.update_traces(marker_color='#FF0000')
        
        fig.update_layout(
            height=500,
            yaxis={'categoryorder': 'total ascending'}
        )
        
        return fig
    
    def create_simple_timeline_chart(self, df):
        """Cria gráfico de picos de entrada/saída estilo análise por hora"""
        # Agrupar dados por hora como no gráfico original
        hourly_summary = df.groupby([
            df['Data Movimento'].dt.hour,
            'Tipo_Movimento'
        ])['Quantidade'].sum().reset_index()
        
        # Separar entrada e saída
        entrada_hourly = hourly_summary[hourly_summary['Tipo_Movimento'] == 'Entrada']
        saida_hourly = hourly_summary[hourly_summary['Tipo_Movimento'] == 'Saída']
        saida_hourly = saida_hourly.copy()
        saida_hourly['Quantidade'] = abs(saida_hourly['Quantidade'])  # Valores positivos
        
        # Criar range completo de horas (0-23)
        all_hours = pd.DataFrame({'Data Movimento': range(24)})
        
        # Merge para garantir todas as horas
        entrada_complete = all_hours.merge(entrada_hourly, left_on='Data Movimento', right_on='Data Movimento', how='left')
        entrada_complete['Quantidade'] = entrada_complete['Quantidade'].fillna(0)
        entrada_complete['Tipo_Movimento'] = 'Entrada'
        
        saida_complete = all_hours.merge(saida_hourly, left_on='Data Movimento', right_on='Data Movimento', how='left')
        saida_complete['Quantidade'] = saida_complete['Quantidade'].fillna(0)
        saida_complete['Tipo_Movimento'] = 'Saída'
        
        # Criar gráfico de barras agrupadas
        fig = go.Figure()
        
        # Adicionar barras de entrada
        fig.add_trace(go.Bar(
            x=entrada_complete['Data Movimento'],
            y=entrada_complete['Quantidade'],
            name='Entrada',
            marker_color='#28a745',  # Verde
            text=entrada_complete['Quantidade'].round(0),
            textposition='outside',
            hovertemplate='<b>Entrada</b><br>Hora: %{x}h<br>Quantidade: %{y:,.0f}<extra></extra>'
        ))
        
        # Adicionar barras de saída
        fig.add_trace(go.Bar(
            x=saida_complete['Data Movimento'],
            y=saida_complete['Quantidade'],
            name='Saída',
            marker_color='#dc3545',  # Vermelho
            text=saida_complete['Quantidade'].round(0),
            textposition='outside',
            hovertemplate='<b>Saída</b><br>Hora: %{x}h<br>Quantidade: %{y:,.0f}<extra></extra>'
        ))
        
        fig.update_layout(
            title='📊 Análise de Picos de Entrada/Saída por Hora',
            xaxis_title='Hora do Dia',
            yaxis_title='Quantidade Total',
            height=500,
            barmode='group',
            hovermode='x unified',
            xaxis=dict(
                tickmode='linear',
                tick0=0,
                dtick=1,
                ticksuffix='h'
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5
            )
        )
        
        return fig
