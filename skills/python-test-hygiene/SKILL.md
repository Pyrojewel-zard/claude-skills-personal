---
name: python-test-hygiene
description: Python 测试卫生最佳实践 - 测试清理、隔离、mock 管理、fixture 设计，确保测试套件健康可维护。
origin: custom
---

# Python Test Hygiene

测试卫生最佳实践，确保测试套件健康、独立、可维护。

## When to Activate

- 编写新测试或修改现有测试
- 设计测试 fixtures
- 处理测试污染问题（测试间依赖）
- 配置 pytest 环境
- 清理测试遗留文件

## 核心原则

### 1. 测试独立性（Test Isolation）

**每个测试必须独立运行，不依赖其他测试的状态。**

```python
# ❌ 错误：测试间共享状态
class TestUser:
    user = None  # 类属性共享

    def test_create(self):
        self.user = create_user("Alice")

    def test_update(self):
        # 依赖上一个测试创建的 user
        update_user(self.user, "Bob")  # 如果 test_create 失败，这里也失败

# ✅ 正确：每个测试独立设置
class TestUser:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.user = create_user("Alice")
        yield
        # teardown: 清理创建的数据

    def test_create(self):
        assert self.user.name == "Alice"

    def test_update(self):
        # 使用 fixture 提供的独立数据
        update_user(self.user, "Bob")
        assert self.user.name == "Bob"
```

### 2. 测试清理（Test Cleanup）

**测试结束后必须清理所有临时资源。**

#### 自动清理机制

```python
# pytest 内置 fixtures
def test_with_tmp_path(tmp_path):
    """tmp_path 自动清理"""
    test_file = tmp_path / "test.txt"
    test_file.write_text("content")
    # 测试结束后 tmp_path 自动删除

def test_with_tmpdir(tmpdir):
    """tmpdir 自动清理"""
    test_file = tmpdir.join("test.txt")
    test_file.write("content")
    # 测试结束后 tmpdir 自动删除

# 自定义清理 fixture
@pytest.fixture
def temp_database():
    """创建临时数据库，测试后自动删除"""
    db_path = f"/tmp/test_db_{uuid.uuid4()}.sqlite"
    db = Database(db_path)
    db.create_tables()
    yield db
    # Teardown
    db.close()
    os.remove(db_path)
```

#### 清理 pytest 缓存

```bash
# 清理 pytest 缓存
pytest --cache-clear

# 清理 __pycache__
find . -type d -name "__pycache__" -exec rm -rf {} +

# 清理 .pytest_cache
rm -rf .pytest_cache

# 清理覆盖率文件
rm -rf .coverage coverage.json htmlcov/
```

### 3. Mock 管理（Mock Management）

**Mock 必须在测试结束后恢复原始状态。**

```python
# ❌ 错误：Mock 没有清理
def test_api_call():
    mock = Mock()
    api_call = mock  # 全局污染
    # 测试结束后 api_call 仍然是 mock

# ✅ 正确：使用 patch 自动恢复
@patch("module.api_call")
def test_api_call(mock_api):
    mock_api.return_value = {"status": "ok"}
    result = process_request()
    assert result["status"] == "ok"
    # 测试结束后 api_call 自动恢复

# ✅ 正确：手动清理
def test_api_call():
    original = module.api_call
    module.api_call = Mock(return_value={"status": "ok"})
    try:
        result = process_request()
        assert result["status"] == "ok"
    finally:
        module.api_call = original  # 必须恢复

# ✅ 正确：使用 fixture 管理 mock
@pytest.fixture
def mock_api():
    with patch("module.api_call") as mock:
        mock.return_value = {"status": "ok"}
        yield mock
        # 自动恢复
```

### 4. Fixture 设计原则

#### Scope 选择

| Scope | 使用场景 | 注意事项 |
|-------|----------|----------|
| `function` | 默认，每个测试独立 | 最安全，推荐 |
| `class` | 类内测试共享 | 需要清理 |
| `module` | 模块内测试共享 | 资源昂贵时使用 |
| `session` | 整个测试会话共享 | 全局配置、数据库连接 |

```python
# function scope（默认）- 最安全
@pytest.fixture
def user():
    return User(name="Alice")
    # 每个测试获得独立的 User

# module scope - 共享昂贵资源
@pytest.fixture(scope="module")
def database():
    db = Database(":memory:")
    db.create_tables()
    yield db
    db.close()  # 模块结束后清理

# session scope - 全局资源
@pytest.fixture(scope="session")
def test_config():
    return load_test_config()
    # 整个测试会话共享
```

#### Autouse 警告

```python
# ❌ 谨慎使用 autouse
@pytest.fixture(autouse=True)
def setup_database():
    # 所有测试都会执行，即使不需要
    db = Database()
    yield db
    db.close()

# ✅ 明确指定需要的测试
@pytest.fixture
def database():
    db = Database()
    yield db
    db.close()

def test_query(database):  # 明确声明需要
    result = database.query("SELECT 1")
    assert result is not None
```

### 5. 测试数据库管理

#### 事务回滚

```python
@pytest.fixture
def db_session():
    """每个测试使用事务，结束后回滚"""
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    session = Session()

    # 开始事务
    session.begin_nested()

    yield session

    # 回滚事务
    session.rollback()
    session.close()
```

#### 测试数据库隔离

```python
@pytest.fixture(scope="session")
def test_db():
    """会话级测试数据库"""
    db_path = f"/tmp/test_db_{uuid.uuid4()}.sqlite"
    db = Database(db_path)
    db.create_tables()
    yield db
    # 会话结束后删除
    db.close()
    os.remove(db_path)

@pytest.fixture
def clean_db(test_db):
    """每个测试前清空数据"""
    test_db.clear_all_tables()
    yield test_db
    # 测试结束后再次清空（可选）
```

### 6. 测试命名规范

```python
# ✅ 好的命名
def test_create_user_with_valid_data_returns_user():
    ...

def test_create_user_with_duplicate_email_raises_error():
    ...

def test_calculate_total_with_empty_cart_returns_zero():
    ...

# ❌ 糟糕的命名
def test_user():
    ...

def test_1():
    ...

def test_it_works():
    ...
```

### 7. 测试分类标记

```python
# pytest.ini 或 pyproject.toml
[pytest]
markers =
    unit: 单元测试，快速，无外部依赖
    integration: 集成测试，涉及数据库/API
    slow: 慢测试，执行时间 > 1s
    e2e: 端到端测试

# 使用标记
@pytest.mark.unit
def test_calculate_total():
    ...

@pytest.mark.integration
def test_database_query():
    ...

@pytest.mark.slow
def test_large_file_processing():
    ...

# 运行特定类别
pytest -m unit          # 只运行单元测试
pytest -m "not slow"    # 跳过慢测试
pytest -m integration   # 只运行集成测试
```

## 常见问题与解决方案

### 问题 1: 测试顺序影响结果

**症状**：单独运行通过，一起运行失败。

**原因**：测试间共享状态。

**解决**：
```python
# 添加 autouse fixture 清理状态
@pytest.fixture(autouse=True)
def reset_global_state():
    GlobalConfig.reset()
    yield
    GlobalConfig.cleanup()
```

### 问题 2: Mock 污染其他测试

**症状**：测试 A 的 mock 影响测试 B。

**原因**：Mock 没有正确恢复。

**解决**：
```python
# 使用 patch 而不是直接赋值
@patch("module.function")
def test_a(mock_func):
    ...

# 或在 fixture 中管理
@pytest.fixture
def mock_environment():
    patches = [
        patch("module.api_call"),
        patch("module.database")
    ]
    mocks = [p.start() for p in patches]
    yield mocks
    for p in patches:
        p.stop()
```

### 问题 3: 临时文件残留

**症状**：测试后 `/tmp` 有大量残留文件。

**解决**：
```python
# 使用 pytest 内置 fixtures
def test_file_operations(tmp_path):
    # tmp_path 自动清理
    ...

# 或使用 tempfile
def test_file_operations():
    with tempfile.NamedTemporaryFile(delete=True) as f:
        f.write(b"content")
        # 文件自动删除
```

### 问题 4: 数据库状态污染

**症状**：集成测试后数据库有测试数据。

**解决**：
```python
@pytest.fixture
def isolated_db():
    # 使用内存数据库
    db = Database(":memory:")
    yield db
    # 无需清理，内存数据库自动消失

# 或使用事务回滚
@pytest.fixture
def db_session():
    session = Session()
    session.begin_nested()
    yield session
    session.rollback()
```

## 测试卫生检查清单

每次编写或修改测试时，检查：

- [ ] 测试是否独立（不依赖其他测试）
- [ ] Fixture 是否正确清理
- [ ] Mock 是否自动恢复
- [ ] 临时文件是否自动删除
- [ ] 测试命名是否清晰描述行为
- [ ] 是否有适当的测试标记
- [ ] 数据库状态是否回滚/清理

## 自动化清理脚本

```python
# tests/conftest.py - 全局清理配置

import pytest
import os
import shutil

@pytest.fixture(scope="session", autouse=True)
def cleanup_test_artifacts():
    """会话结束后清理所有测试产物"""
    yield

    # 清理 __pycache__
    for root, dirs, files in os.walk("."):
        if "__pycache__" in dirs:
            shutil.rmtree(os.path.join(root, "__pycache__"))

    # 清理 pytest 缓存
    if os.path.exists(".pytest_cache"):
        shutil.rmtree(".pytest_cache")

    # 清理覆盖率文件
    for f in [".coverage", "coverage.json"]:
        if os.path.exists(f):
            os.remove(f)

    # 清理临时测试文件
    tmp_pattern = "test_tmp_*"
    for f in os.listdir("/tmp"):
        if f.startswith(tmp_pattern):
            os.remove(os.path.join("/tmp", f))
```

## 最佳实践总结

| 实践 | 工具/方法 |
|------|-----------|
| 临时文件 | `tmp_path`, `tmpdir`, `tempfile` |
| Mock 管理 | `@patch`, `patch.object`, fixture |
| 数据库隔离 | 事务回滚, 内存数据库 |
| 状态清理 | `autouse` fixture, `yield` teardown |
| 测试分类 | `@pytest.mark` |
| 命名规范 | `test_<action>_<condition>_<result>` |

---

**记住**：干净的测试套件是可维护代码库的基础。测试卫生问题会随时间累积，尽早解决。