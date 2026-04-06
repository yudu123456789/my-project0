import streamlit as st
import asyncio
from app.storage.database import DatabaseManager, SFTTask
from app.core.domain.enums import TaskStatus
from sqlalchemy import select

# UI 样式配置
st.set_page_config(page_title="Agent-SFT-Forge 仲裁台", layout="wide")

async def get_tasks(db_mgr):
    async with db_mgr.session_factory() as session:
        stmt = select(SFTTask).where(SFTTask.status == TaskStatus.PENDING_REVIEW).limit(5)
        res = await session.execute(stmt)
        return res.scalars().all()

# --- 主界面 ---
st.title("🛡️ 异构共识仲裁中心")
db_mgr = DatabaseManager(os.getenv("DATABASE_URL"))
tasks = asyncio.run(get_tasks(db_mgr))

if not tasks:
    st.balloons()
    st.success("所有任务均达成一致，暂无待审核项。")
else:
    for task in tasks:
        with st.container(border=True):
            st.subheader(f"任务 ID: {task.id} | 来源: {task.source}")
            
            # 渲染审计日志对比
            if task.judge_report and 'audit_log' in task.judge_report:
                for log in task.judge_report['audit_log']:
                    st.warning(f"检测到共识冲突 (分差: {log['variance']})")
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown("**模型 A (Primary)**")
                        st.metric("评分", f"{log['model_a']['score']}/10")
                        st.info(f"理由: {log['model_a']['reason']}")
                    
                    with c2:
                        st.markdown("**模型 B (Secondary)**")
                        st.metric("评分", f"{log['model_b']['score']}/10")
                        st.info(f"理由: {log['model_b']['reason']}")
            
            st.divider()
            st.markdown("**待决策语料内容:**")
            st.code(str(task.qa_pairs), language="json")
            
            # 操作区
            btn_col1, btn_col2 = st.columns(2)
            if btn_col1.button("✅ 批准入库", key=f"ok_{task.id}"):
                # 状态回写逻辑...
                st.rerun()
            if btn_col2.button("🗑️ 标记废弃", key=f"no_{task.id}"):
                # 状态回写逻辑...
                st.rerun()