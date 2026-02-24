"""
API 完整流程测试

使用 FastAPI TestClient 演示用户从注册到获取7天启动包的完整流程
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_full_flow():
    print("=" * 50)
    print("Bamboo Shoot Soup API 完整流程测试")
    print("=" * 50)
    print()

    # 步骤 1: 创建用户
    print("步骤 1: 创建用户")
    resp = client.post("/users/", json={})
    print(f"  状态码: {resp.status_code}")
    assert resp.status_code == 201, f"Expected 201, got {resp.status_code}"
    user_data = resp.json()
    user_id = user_data["id"]
    print(f"  用户ID: {user_id}")
    print()

    # 步骤 2: 创建诊断记录
    print("步骤 2: 创建诊断记录 (能力画像)")
    diagnostic_data = {
        "user_id": user_id,
        "skill_stack": "Python, SQL, AI产品开发",
        "interest_energy_curve": "上午高效创作，晚间复盘思考",
        "cognitive_style": "视觉型，擅长架构设计",
        "value_boundary": "不违法、不虚假宣传",
        "risk_tolerance": "中等，可接受适度争议",
        "time_commitment": "每天2小时"
    }
    resp = client.post("/diagnostics/", json=diagnostic_data)
    print(f"  状态码: {resp.status_code}")
    assert resp.status_code == 201, f"Expected 201, got {resp.status_code}: {resp.text}"
    diag_data = resp.json()
    diag_id = diag_data["id"]
    print(f"  诊断ID: {diag_id}")
    print(f"  技能栈: {diag_data['skill_stack']}")
    print()

    # 步骤 3: 创建身份模型
    print("步骤 3: 创建身份模型")
    identity_data = {
        "user_id": user_id,
        "diagnostic_id": diag_id,
        "title": "AI产品笔记侠",
        "target_audience": "想用AI提升效率的产品经理和创业者",
        "content_pillars": "AI工具测评、产品思考、效率方法",
        "tone_style": "专业但不高冷，用人话讲AI",
        "viewpoint_library": "AI是每个人的副业加速器",
        "differentiation": "不做纯技术教程，只做接地气的AI应用",
        "growth_path": "0-3月：建立人设；3-6月：内容系列化",
        "monetization_path": "付费社群 > 咨询 > 课程",
        "risk_boundary": "不评测医疗、金融等敏感领域"
    }
    resp = client.post("/identity-models/", json=identity_data)
    print(f"  状态码: {resp.status_code}")
    assert resp.status_code == 201, f"Expected 201, got {resp.status_code}: {resp.text}"
    ident_data = resp.json()
    ident_id = ident_data["id"]
    print(f"  身份模型ID: {ident_id}")
    print(f"  标题: {ident_data['title']}")
    print()

    # 步骤 4: 创建人格宪法
    print("步骤 4: 创建人格宪法")
    constitution_data = {
        "user_id": user_id,
        "identity_model_id": ident_id,
        "tone_words_used": "实测、效果、简单粗暴",
        "tone_words_forbidden": "大约、可能、套话",
        "tone_sentence_patterns": "短句为主，多用动词，用第一人称",
        "viewpoint_fortress": "AI是每个人的机会，不懂技术也能用",
        "narrative_mainline": "用AI提升工作效率，过更好的生活",
        "growth_arc": "从AI小白到AI应用高手的成长之路"
    }
    resp = client.post("/persona-constitutions/", json=constitution_data)
    print(f"  状态码: {resp.status_code}")
    assert resp.status_code == 201, f"Expected 201, got {resp.status_code}: {resp.text}"
    const_data = resp.json()
    const_id = const_data["id"]
    print(f"  人格宪法ID: {const_id}")
    print(f"  口吻词(使用): {const_data['tone_words_used']}")
    print()

    # 步骤 5: 创建7天启动包
    print("步骤 5: 创建7天启动包")
    launch_kit_data = {
        "user_id": user_id,
        "identity_model_id": ident_id,
        "persona_constitution_id": const_id,
        "day_1": {"theme": "我是谁", "content": "介绍自己的背景和AI结缘的故事"},
        "day_2": {"theme": "你能获得什么", "content": "目标受众的痛点和解决方案"},
        "day_3": {"theme": "我的方法论", "content": "分享一个具体的AI使用技巧"},
        "day_4": {"theme": "案例展示", "content": "一个真实的提效案例"},
        "day_5": {"theme": "工具清单", "content": "推荐3个必备AI工具"},
        "day_6": {"theme": "互动答疑", "content": "回答评论区常见问题"},
        "day_7": {"theme": "邀请行动", "content": "引导关注和转发"},
        "sustainable_columns": "周更AI工具测评、月度复盘、读者问答",
        "growth_experiment": "测试不同发布时间段的效果"
    }
    resp = client.post("/launch-kits/", json=launch_kit_data)
    print(f"  状态码: {resp.status_code}")
    assert resp.status_code == 201, f"Expected 201, got {resp.status_code}: {resp.text}"
    launch_data = resp.json()
    launch_id = launch_data["id"]
    print(f"  启动包ID: {launch_id}")
    print(f"  第1天主题: {launch_data['day_1_theme']}")
    print()

    # 步骤 6: 查询验证
    print("=" * 50)
    print("验证数据完整性")
    print("=" * 50)
    print()

    # 查询用户的诊断
    resp = client.get(f"/diagnostics/user/{user_id}")
    diagnostics = resp.json()
    print(f"用户的诊断记录数: {len(diagnostics)}")

    # 查询诊断的身份模型
    resp = client.get(f"/identity-models/diagnostic/{diag_id}")
    identities = resp.json()
    print(f"诊断生成的身份模型数: {len(identities)}")

    # 查询身份模型的人格宪法
    resp = client.get(f"/persona-constitutions/identity/{ident_id}")
    print(f"人格宪法: {resp.json()['id']}")

    # 查询身份模型的启动包
    resp = client.get(f"/launch-kits/identity/{ident_id}")
    print(f"7天启动包: {resp.json()['id']}")

    print()
    print("=" * 50)
    print("通过:全流程测试已成功完成!")
    print("=" * 50)


if __name__ == "__main__":
    test_full_flow()
