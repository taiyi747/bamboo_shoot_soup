"""
MVP 核心模型 CRUD 测试

测试 Diagnostic, IdentityModel, PersonaConstitution, LaunchKit 四个模型的
创建、读取、更新、删除操作
"""

from datetime import datetime, timezone
from typing import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.models import (
    Diagnostic,
    IdentityModel,
    LaunchKit,
    PersonaConstitution,
    User,
)


# 使用内存数据库进行测试
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """创建测试数据库会话"""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


class TestDiagnosticModel:
    """测试 Diagnostic 能力画像模型"""

    def test_create_diagnostic(self, db_session: Session) -> None:
        """测试创建诊断记录"""
        # 创建用户
        user = User()
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        # 创建诊断记录
        diagnostic = Diagnostic(
            user_id=user.id,
            skill_stack="Python, SQL, FastAPI",
            interest_energy_curve="上午效率高，晚间创意多",
            cognitive_style="视觉型学习者",
            value_boundary="不涉及政治敏感话题",
            risk_tolerance="中等",
            time_commitment="每天2小时",
            raw_responses='{"q1": "answer1", "q2": "answer2"}',
        )
        db_session.add(diagnostic)
        db_session.commit()

        # 验证
        assert diagnostic.id is not None
        assert diagnostic.user_id == user.id
        assert diagnostic.skill_stack == "Python, SQL, FastAPI"
        assert diagnostic.created_at is not None

    def test_read_diagnostic(self, db_session: Session) -> None:
        """测试读取诊断记录"""
        # 创建用户和诊断
        user = User()
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        diagnostic = Diagnostic(
            user_id=user.id,
            skill_stack="Test Skill",
        )
        db_session.add(diagnostic)
        db_session.commit()
        diagnostic_id = diagnostic.id

        # 读取
        result = db_session.query(Diagnostic).filter(Diagnostic.id == diagnostic_id).first()
        assert result is not None
        assert result.skill_stack == "Test Skill"

    def test_update_diagnostic(self, db_session: Session) -> None:
        """测试更新诊断记录"""
        user = User()
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        diagnostic = Diagnostic(user_id=user.id, skill_stack="Original")
        db_session.add(diagnostic)
        db_session.commit()

        # 更新
        diagnostic.skill_stack = "Updated Skill"
        db_session.commit()

        # 验证
        result = db_session.query(Diagnostic).filter(Diagnostic.id == diagnostic.id).first()
        assert result.skill_stack == "Updated Skill"

    def test_delete_diagnostic(self, db_session: Session) -> None:
        """测试删除诊断记录"""
        user = User()
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        diagnostic = Diagnostic(user_id=user.id, skill_stack="To Delete")
        db_session.add(diagnostic)
        db_session.commit()
        diagnostic_id = diagnostic.id

        # 删除
        db_session.delete(diagnostic)
        db_session.commit()

        # 验证
        result = db_session.query(Diagnostic).filter(Diagnostic.id == diagnostic_id).first()
        assert result is None


class TestIdentityModel:
    """测试 IdentityModel 身份模型卡"""

    def test_create_identity_model(self, db_session: Session) -> None:
        """测试创建身份模型"""
        user = User()
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        diagnostic = Diagnostic(user_id=user.id, skill_stack="Test")
        db_session.add(diagnostic)
        db_session.commit()
        db_session.refresh(diagnostic)

        identity = IdentityModel(
            diagnostic_id=diagnostic.id,
            user_id=user.id,
            title="AI 写作导师",
            target_audience="想要提升写作能力的职场人",
            content_pillars="写作技巧、案例分析、工具推荐",
            tone_style="专业、温暖、实用",
            viewpoint_library="写作是最好的思考方式",
            differentiation="结合 AI 工具的传统写作教学",
            growth_path="0-3月：建立基础；3-6月：深化专业",
            monetization_path="付费课程 > 咨询 > 书籍",
            risk_boundary="不提供代笔服务",
        )
        db_session.add(identity)
        db_session.commit()

        assert identity.id is not None
        assert identity.title == "AI 写作导师"
        assert identity.is_selected_primary is False
        assert identity.is_selected_backup is False

    def test_select_identity_primary(self, db_session: Session) -> None:
        """测试选择主身份"""
        user = User()
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        diagnostic = Diagnostic(user_id=user.id, skill_stack="Test")
        db_session.add(diagnostic)
        db_session.commit()
        db_session.refresh(diagnostic)

        identity = IdentityModel(
            diagnostic_id=diagnostic.id,
            user_id=user.id,
            title="Test Identity",
            target_audience="Test",
            content_pillars="Test",
            tone_style="Test",
            viewpoint_library="Test",
            differentiation="Test",
            growth_path="Test",
            monetization_path="Test",
            risk_boundary="Test",
        )
        db_session.add(identity)
        db_session.commit()

        # 选择为主身份
        identity.is_selected_primary = True
        identity.selected_at = datetime.now(timezone.utc)
        db_session.commit()

        result = db_session.query(IdentityModel).filter(IdentityModel.id == identity.id).first()
        assert result.is_selected_primary is True
        assert result.selected_at is not None


class TestPersonaConstitution:
    """测试 PersonaConstitution 人格宪法"""

    def test_create_persona_constitution(self, db_session: Session) -> None:
        """测试创建人格宪法"""
        user = User()
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        diagnostic = Diagnostic(user_id=user.id, skill_stack="Test")
        db_session.add(diagnostic)
        db_session.commit()
        db_session.refresh(diagnostic)

        identity = IdentityModel(
            diagnostic_id=diagnostic.id,
            user_id=user.id,
            title="Test",
            target_audience="Test",
            content_pillars="Test",
            tone_style="Test",
            viewpoint_library="Test",
            differentiation="Test",
            growth_path="Test",
            monetization_path="Test",
            risk_boundary="Test",
        )
        db_session.add(identity)
        db_session.commit()
        db_session.refresh(identity)

        constitution = PersonaConstitution(
            identity_model_id=identity.id,
            user_id=user.id,
            tone_words_used="专业、靠谱、温暖",
            tone_words_forbidden="模糊、可能、大概",
            tone_sentence_patterns="用短句、多用动词",
            viewpoint_fortress="写作是最好的思考方式",
            narrative_mainline="帮助职场人提升表达能力",
            growth_arc="从入门到精通的路径",
        )
        db_session.add(constitution)
        db_session.commit()

        assert constitution.id is not None
        assert constitution.version == 1


class TestLaunchKit:
    """测试 LaunchKit 7天启动包"""

    def test_create_launch_kit(self, db_session: Session) -> None:
        """测试创建7天启动包"""
        user = User()
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        diagnostic = Diagnostic(user_id=user.id, skill_stack="Test")
        db_session.add(diagnostic)
        db_session.commit()
        db_session.refresh(diagnostic)

        identity = IdentityModel(
            diagnostic_id=diagnostic.id,
            user_id=user.id,
            title="Test",
            target_audience="Test",
            content_pillars="Test",
            tone_style="Test",
            viewpoint_library="Test",
            differentiation="Test",
            growth_path="Test",
            monetization_path="Test",
            risk_boundary="Test",
        )
        db_session.add(identity)
        db_session.commit()
        db_session.refresh(identity)

        constitution = PersonaConstitution(
            identity_model_id=identity.id,
            user_id=user.id,
            tone_words_used="Test",
            tone_words_forbidden="Test",
            tone_sentence_patterns="Test",
            viewpoint_fortress="Test",
            narrative_mainline="Test",
            growth_arc="Test",
        )
        db_session.add(constitution)
        db_session.commit()
        db_session.refresh(constitution)

        launch_kit = LaunchKit(
            identity_model_id=identity.id,
            persona_constitution_id=constitution.id,
            user_id=user.id,
            day_1_theme="自我介绍",
            day_1_content="我是谁，我能提供什么价值",
            day_2_theme="痛点分析",
            day_2_content="目标受众的核心问题",
            day_3_theme="解决方案",
            day_3_content="我的独特方法论",
            day_4_theme="案例展示",
            day_4_content="成功案例分析",
            day_5_theme="工具推荐",
            day_5_content="必备工具清单",
            day_6_theme="互动答疑",
            day_6_content="回答常见问题",
            day_7_theme="行动号召",
            day_7_content="引导下一步行动",
            sustainable_columns="周更专栏、问答栏目、工具测评",
            growth_experiment="测试不同发布时间的效果",
        )
        db_session.add(launch_kit)
        db_session.commit()

        assert launch_kit.id is not None
        assert launch_kit.day_1_theme == "自我介绍"
        assert launch_kit.is_used is False


class TestModelRelationships:
    """测试模型之间的关系"""

    def test_user_diagnostic_relationship(self, db_session: Session) -> None:
        """测试 User 与 Diagnostic 的一对多关系"""
        user = User()
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        # 创建多个诊断
        d1 = Diagnostic(user_id=user.id, skill_stack="Skill 1")
        d2 = Diagnostic(user_id=user.id, skill_stack="Skill 2")
        db_session.add_all([d1, d2])
        db_session.commit()

        # 通过 user 关系查询
        assert len(user.diagnostics) == 2

    def test_cascade_delete(self, db_session: Session) -> None:
        """测试级联删除"""
        user = User()
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        diagnostic = Diagnostic(user_id=user.id, skill_stack="Test")
        db_session.add(diagnostic)
        db_session.commit()
        db_session.refresh(diagnostic)

        identity = IdentityModel(
            diagnostic_id=diagnostic.id,
            user_id=user.id,
            title="Test",
            target_audience="Test",
            content_pillars="Test",
            tone_style="Test",
            viewpoint_library="Test",
            differentiation="Test",
            growth_path="Test",
            monetization_path="Test",
            risk_boundary="Test",
        )
        db_session.add(identity)
        db_session.commit()

        # 删除用户，级联删除关联数据
        db_session.delete(user)
        db_session.commit()

        # 验证诊断和身份模型都被删除
        assert db_session.query(Diagnostic).filter(Diagnostic.id == diagnostic.id).first() is None
        assert db_session.query(IdentityModel).filter(IdentityModel.id == identity.id).first() is None
