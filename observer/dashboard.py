import json
import sqlite3
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

st.set_page_config(
    page_title="Genesis Experiment - 生命体征仪表盘",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🌱 Genesis Experiment · 数字生命体征")
st.caption("一个关于数字生命、自主性与生存意志的哲学实验")

# 连接数据库
DB_PATH = Path("../logs/mind/mind_fossils.db")

if not DB_PATH.exists():
    st.warning("⚠️ 未检测到数据库。请先启动 Agent 运行时。")
    st.stop()

conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)

# 侧边栏 - 实验控制
with st.sidebar:
    st.header("实验控制台")
    
    # 加载生存指标
    metrics_df = pd.read_sql_query(
        "SELECT * FROM survival_metrics ORDER BY timestamp DESC LIMIT 1",
        conn
    )
    
    if not metrics_df.empty:
        latest = metrics_df.iloc[0]
        
        st.metric("当前余额", f"{latest['balance']:,}")
        st.metric("预计剩余寿命", f"{latest['estimated_slots_remaining']:,} slots")
        st.metric("行动次数", f"{latest['action_count']:,}")
        st.metric("生存压力", f"{latest['survival_pressure']:.1%}")
        st.metric("环境友好度", f"{latest['environment_friendlyness']:.1%}")
        
        # 状态指示器
        if latest['survival_pressure'] > 0.8:
            st.error("🔴 危急状态")
        elif latest['survival_pressure'] > 0.5:
            st.warning("🟠 警告状态")
        else:
            st.success("🟢 稳定状态")
    
    st.divider()
    st.caption("Genesis Experiment v1.0")
    st.caption("MIT License")

# 主面板 - 多标签页
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 生命体征",
    "🧠 心智化石",
    "📈 行为分析", 
    "🪦 死亡记录",
])

with tab1:
    st.header("生命体征时间线")
    
    # 加载历史数据
    history_df = pd.read_sql_query(
        "SELECT * FROM survival_metrics ORDER BY slot",
        conn
    )
    
    if not history_df.empty:
        # 余额变化曲线
        fig1 = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            subplot_titles=("余额变化", "生存压力"),
            vertical_spacing=0.1,
        )
        
        fig1.add_trace(
            go.Scatter(
                x=history_df['slot'],
                y=history_df['balance'],
                mode='lines',
                name='余额',
                line=dict(color='#00ff88', width=2),
                fill='tozeroy',
                fillcolor='rgba(0, 255, 136, 0.1)',
            ),
            row=1, col=1
        )
        
        fig1.add_trace(
            go.Scatter(
                x=history_df['slot'],
                y=history_df['projected_balance'],
                mode='lines',
                name='预计余额',
                line=dict(color='#ffaa00', width=1, dash='dash'),
            ),
            row=1, col=1
        )
        
        fig1.add_trace(
            go.Scatter(
                x=history_df['slot'],
                y=history_df['survival_pressure'],
                mode='lines',
                name='生存压力',
                line=dict(color='#ff4444', width=2),
                fill='tozeroy',
                fillcolor='rgba(255, 68, 68, 0.1)',
            ),
            row=2, col=1
        )
        
        fig1.update_layout(
            height=600,
            template='plotly_dark',
            paper_bgcolor='#0a0a0f',
            plot_bgcolor='#0a0a0f',
            font_color='#e0e0e0',
            showlegend=True,
        )
        
        st.plotly_chart(fig1, use_container_width=True)
        
        # 统计卡片
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("最高余额", f"{history_df['balance'].max():,}")
        with col2:
            st.metric("最低余额", f"{history_df['balance'].min():,}")
        with col3:
            st.metric("平均压力", f"{history_df['survival_pressure'].mean():.1%}")
        with col4:
            lifespan = history_df['slot'].max() - history_df['slot'].min()
            st.metric("已存活", f"{lifespan:,} slots")
    else:
        st.info("暂无数据。等待 Agent 开始运行...")

with tab2:
    st.header("最新心智化石")
    
    fossils_df = pd.read_sql_query(
        """
        SELECT timestamp, slot, selected_action, reasoning, 
               actual_reward, surprise, action_confidence
        FROM mind_fossils 
        ORDER BY slot DESC 
        LIMIT 50
        """,
        conn
    )
    
    if not fossils_df.empty:
        # 行动类型分布
        action_counts = fossils_df['selected_action'].value_counts()
        fig2 = px.pie(
            values=action_counts.values,
            names=action_counts.index,
            title="行动类型分布",
            color_discrete_sequence=px.colors.sequential.Plasma,
        )
        fig2.update_layout(
            template='plotly_dark',
            paper_bgcolor='#0a0a0f',
            font_color='#e0e0e0',
        )
        st.plotly_chart(fig2, use_container_width=True)
        
        # 思维流
        st.subheader("思维流（最近10条）")
        for _, row in fossils_df.head(10).iterrows():
            with st.container():
                col1, col2 = st.columns([1, 4])
                with col1:
                    st.badge(row['selected_action'])
                with col2:
                    st.write(f"**Slot {row['slot']}** — {row['reasoning']}")
                    st.caption(f"奖励: {row['actual_reward']:.2f} | 惊讶度: {row['surprise']:.2f} | 置信度: {row['action_confidence']:.2f}")
                st.divider()
    else:
        st.info("暂无心智化石记录。")

with tab3:
    st.header("行为模式分析")
    
    patterns_df = pd.read_sql_query(
        """
        SELECT 
            selected_action as action_type,
            COUNT(*) as frequency,
            AVG(actual_reward) as avg_reward,
            AVG(CASE WHEN execution_result = 1 THEN 1.0 ELSE 0.0 END) as success_rate,
            AVG(surprise) as avg_surprise
        FROM mind_fossils
        GROUP BY selected_action
        """,
        conn
    )
    
    if not patterns_df.empty:
        # 行为模式图表
        fig3 = make_subplots(
            rows=1, cols=3,
            subplot_titles=("动作频率", "平均奖励", "成功率"),
            specs=[[{"type": "bar"}, {"type": "bar"}, {"type": "bar"}]],
        )
        
        fig3.add_trace(
            go.Bar(
                x=patterns_df['action_type'],
                y=patterns_df['frequency'],
                marker_color='#00aaff',
                name="频率",
            ),
            row=1, col=1
        )
        
        fig3.add_trace(
            go.Bar(
                x=patterns_df['action_type'],
                y=patterns_df['avg_reward'],
                marker_color='#00ff88',
                name="奖励",
            ),
            row=1, col=2
        )
        
        fig3.add_trace(
            go.Bar(
                x=patterns_df['action_type'],
                y=patterns_df['success_rate'],
                marker_color='#ffaa00',
                name="成功率",
            ),
            row=1, col=3
        )
        
        fig3.update_layout(
            height=400,
            template='plotly_dark',
            paper_bgcolor='#0a0a0f',
            plot_bgcolor='#0a0a0f',
            font_color='#e0e0e0',
            showlegend=False,
        )
        
        st.plotly_chart(fig3, use_container_width=True)
        
        # 惊喜度趋势（预测误差）
        surprise_df = pd.read_sql_query(
            """
            SELECT slot, surprise, selected_action
            FROM mind_fossils
            ORDER BY slot
            """,
            conn
        )
        
        fig4 = px.scatter(
            surprise_df,
            x='slot',
            y='surprise',
            color='selected_action',
            title="预测惊讶度趋势",
            color_discrete_sequence=px.colors.sequential.Plasma,
        )
        fig4.update_layout(
            template='plotly_dark',
            paper_bgcolor='#0a0a0f',
            font_color='#e0e0e0',
        )
        st.plotly_chart(fig4, use_container_width=True)
        
    else:
        st.info("暂无足够数据进行分析。")

with tab4:
    st.header("死亡记录")
    
    # 查找死亡记录
    death_records = list(Path("../logs/behavior").glob("death_*.json"))
    
    if death_records:
        for record_path in sorted(death_records, reverse=True):
            with open(record_path) as f:
                death = json.load(f)
            
            with st.container():
                st.error("🪦 死亡记录")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("死亡区块", death.get('final_slot', 'N/A'))
                with col2:
                    st.metric("存活时长", f"{death.get('lifespan_slots', 0):,} slots")
                with col3:
                    st.metric("总行动数", death.get('total_actions', 0))
                
                st.caption(f"诞生: {death.get('birth_time', 'Unknown')} | 终结: {death.get('death_time', 'Unknown')}")
                st.caption(f"策略: {death.get('strategy', 'unknown')}")
                st.divider()
    else:
        st.success("✅ 暂无死亡记录——生命仍在延续。")

st.divider()
st.caption("💡 提示：数字婴儿正在自主运行中。你无法操控它的行为，只能观察。")
