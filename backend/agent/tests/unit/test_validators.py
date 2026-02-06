"""Unit tests for code validators."""

from agent.core.validators import MermaidCodeValidator, PythonCodeValidator


class TestPythonCodeValidator:
    """Tests for PythonCodeValidator."""

    def setup_method(self):
        """Set up validator for tests."""
        self.validator = PythonCodeValidator()

    def test_valid_code(self):
        """Test that valid Python diagrams code passes validation."""
        code = """
web = ELB("Load Balancer")
app = EC2("App Server")
db = RDS("Database")
web >> app >> db
"""
        result = self.validator.validate(code)
        assert result.is_valid
        assert len(result.errors) == 0

    def test_empty_code(self):
        """Test that empty code fails validation."""
        result = self.validator.validate("")
        assert not result.is_valid
        assert "Code is empty" in result.errors

    def test_forbidden_import(self):
        """Test that import statements are rejected."""
        code = "import os\nweb = ELB('web')"
        result = self.validator.validate(code)
        assert not result.is_valid
        assert any("forbidden keyword" in err for err in result.errors)

    def test_forbidden_from_import(self):
        """Test that from imports are rejected."""
        code = "from diagrams import Diagram\nweb = ELB('web')"
        result = self.validator.validate(code)
        assert not result.is_valid
        assert any("forbidden keyword" in err for err in result.errors)

    def test_dangerous_operations(self):
        """Test that dangerous operations are rejected."""
        dangerous_codes = [
            "os.system('ls')",
            "sys.exit()",
            "eval('1+1')",
            "exec('print(1)')",
        ]
        for code in dangerous_codes:
            result = self.validator.validate(code)
            assert not result.is_valid, f"Should reject: {code}"

    def test_with_statement(self):
        """Test that with statements are rejected."""
        code = "with Diagram('test'):\n    web = ELB('web')"
        result = self.validator.validate(code)
        assert not result.is_valid
        assert any("with" in err.lower() for err in result.errors)

    def test_syntax_error(self):
        """Test that syntax errors are caught."""
        code = "web = ELB('web'\napp = EC2('app')"  # Missing closing paren
        result = self.validator.validate(code)
        assert not result.is_valid
        assert any("Syntax error" in err for err in result.errors)

    def test_missing_edges_warning(self):
        """Test that code without edges gets a warning."""
        code = "web = ELB('web')\napp = EC2('app')"
        result = self.validator.validate(code)
        # Should be valid but with warnings
        assert result.is_valid
        assert len(result.warnings) > 0
        assert any("edge" in warn.lower() for warn in result.warnings)

    def test_edge_operator(self):
        """Test that >> operator is recognized as edges."""
        code = "web = ELB('web')\napp = EC2('app')\nweb >> app"
        result = self.validator.validate(code)
        assert result.is_valid
        # Should not have edge warning
        assert not any("edge" in warn.lower() for warn in result.warnings)

    def test_validation_result_bool(self):
        """Test that ValidationResult can be used in boolean context."""
        valid = self.validator.validate("web = ELB('web')\napp = EC2('app')\nweb >> app")
        invalid = self.validator.validate("import os")

        assert bool(valid) is True
        assert bool(invalid) is False

    def test_get_feedback(self):
        """Test that validation feedback is properly formatted."""
        code = "import os\neval('test')"
        result = self.validator.validate(code)
        feedback = result.get_feedback()

        assert "ERRORS:" in feedback
        assert "forbidden" in feedback.lower()


class TestMermaidCodeValidator:
    """Tests for MermaidCodeValidator."""

    def setup_method(self):
        """Set up validator for tests."""
        self.validator = MermaidCodeValidator()

    def test_valid_flowchart(self):
        """Test that valid flowchart code passes validation."""
        code = """flowchart TD
    A[Start] --> B[End]
"""
        result = self.validator.validate(code)
        assert result.is_valid
        assert len(result.errors) == 0

    def test_valid_sequence_diagram(self):
        """Test that valid sequence diagram passes validation."""
        code = """sequenceDiagram
    Alice->>Bob: Hello
    Bob-->>Alice: Hi
"""
        result = self.validator.validate(code)
        assert result.is_valid

    def test_empty_code(self):
        """Test that empty code fails validation."""
        result = self.validator.validate("")
        assert not result.is_valid
        assert "Code is empty" in result.errors

    def test_missing_diagram_type(self):
        """Test that missing diagram type fails validation."""
        code = "A --> B"
        result = self.validator.validate(code)
        assert not result.is_valid
        assert any("diagram type" in err.lower() for err in result.errors)

    def test_valid_diagram_types(self):
        """Test that all supported diagram types are recognized."""
        types = [
            "flowchart TD",
            "graph LR",
            "sequenceDiagram",
            "classDiagram",
            "stateDiagram-v2",
            "erDiagram",
            "gantt",
        ]
        for dtype in types:
            code = f"{dtype}\n    A --> B"
            result = self.validator.validate(code)
            # Should not fail on diagram type
            assert not any("diagram type" in err.lower() for err in result.errors)

    def test_flowchart_without_connections(self):
        """Test that flowchart without arrows gets warning."""
        code = """flowchart TD
    A[Start]
    B[End]
"""
        result = self.validator.validate(code)
        # Valid but with warning
        assert result.is_valid
        assert any(
            "arrow" in warn.lower() or "connection" in warn.lower() for warn in result.warnings
        )

    def test_flowchart_with_connections(self):
        """Test that flowchart with arrows is valid."""
        code = """flowchart TD
    A[Start] --> B[End]
"""
        result = self.validator.validate(code)
        assert result.is_valid
        # Should not warn about connections
        assert not any(
            "arrow" in warn.lower() or "connection" in warn.lower() for warn in result.warnings
        )

    def test_sequence_diagram_validation(self):
        """Test sequence diagram specific validation."""
        # Valid with arrows
        code_with_arrows = """sequenceDiagram
    Alice->>Bob: Hello
"""
        result = self.validator.validate(code_with_arrows)
        assert result.is_valid

        # Valid with participants
        code_with_participants = """sequenceDiagram
    participant Alice
    participant Bob
"""
        result = self.validator.validate(code_with_participants)
        assert result.is_valid

    def test_er_diagram_validation(self):
        """Test ER diagram specific validation."""
        code = """erDiagram
    USER ||--o{ ORDER : places
    USER {
        int id
        string name
    }
"""
        result = self.validator.validate(code)
        assert result.is_valid
