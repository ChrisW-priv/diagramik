"""Code validators for generated diagram code."""

import ast
import re

from pydantic import BaseModel


class ValidationResult(BaseModel):
    """Result of code validation."""

    is_valid: bool
    errors: list[str] = []
    warnings: list[str] = []

    def __bool__(self) -> bool:
        """Allow using ValidationResult in boolean context."""
        return self.is_valid

    def get_feedback(self) -> str:
        """Get human-readable feedback for code generation retry.

        Returns:
            Formatted string with errors and warnings
        """
        lines = []
        if self.errors:
            lines.append("ERRORS:")
            lines.extend(f"  - {err}" for err in self.errors)
        if self.warnings:
            lines.append("WARNINGS:")
            lines.extend(f"  - {warn}" for warn in self.warnings)
        return "\n".join(lines) if lines else "Code is valid"


class PythonCodeValidator:
    """Validator for Python diagrams library code.

    Ensures generated code follows safety rules:
    - No imports
    - No with statements
    - No dangerous operations
    - Valid Python syntax
    - Has edge connections
    """

    FORBIDDEN_KEYWORDS = [
        "import ",
        "from ",
        "__import__",
        "eval(",
        "exec(",
        "compile(",
        "open(",
        "file(",
    ]

    DANGEROUS_MODULES = [
        "os.",
        "sys.",
        "subprocess",
        "pathlib",
        "__builtins__",
        "__globals__",
        "__locals__",
    ]

    def validate(self, code: str) -> ValidationResult:
        """Validate Python diagrams code.

        Args:
            code: Generated Python code to validate

        Returns:
            ValidationResult with is_valid flag and error messages
        """
        errors = []
        warnings = []

        if not code or not code.strip():
            errors.append("Code is empty")
            return ValidationResult(is_valid=False, errors=errors)

        # Check for forbidden imports
        for keyword in self.FORBIDDEN_KEYWORDS:
            if keyword in code:
                errors.append(
                    f"Code contains forbidden keyword: {keyword}. Imports are handled externally."
                )

        # Check for dangerous operations
        for module in self.DANGEROUS_MODULES:
            if module in code:
                errors.append(f"Code contains dangerous module reference: {module}")

        # Check for with statement (Diagram context manager)
        if "with " in code.lower():
            errors.append(
                "Code contains 'with' statement. Diagram context manager is handled externally."
            )

        # Syntax validation via AST
        try:
            ast.parse(code)
        except SyntaxError as e:
            errors.append(f"Syntax error: {e.msg} at line {e.lineno}")

        # Check for edge connections (>> operator or Edge() calls)
        has_edges = ">>" in code or "Edge(" in code
        if not has_edges:
            warnings.append(
                "No edge connections found (>> operator or Edge() calls). "
                "Diagram may not show relationships between nodes."
            )

        # Check for common mistakes
        if code.count("=") == 0:
            warnings.append("No variable assignments found. Are nodes being created?")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )


class MermaidCodeValidator:
    """Validator for Mermaid diagram syntax.

    Ensures generated code:
    - Declares diagram type
    - Has valid syntax structure
    - Contains nodes/entities
    - Has connections/relationships
    """

    DIAGRAM_TYPES = [
        "flowchart",
        "graph",
        "sequenceDiagram",
        "classDiagram",
        "stateDiagram",
        "erDiagram",
        "gantt",
        "pie",
        "journey",
        "gitGraph",
    ]

    def validate(self, code: str) -> ValidationResult:
        """Validate Mermaid diagram code.

        Args:
            code: Generated Mermaid code to validate

        Returns:
            ValidationResult with is_valid flag and error messages
        """
        errors = []
        warnings = []

        if not code or not code.strip():
            errors.append("Code is empty")
            return ValidationResult(is_valid=False, errors=errors)

        lines = [line.strip() for line in code.split("\n") if line.strip()]

        if not lines:
            errors.append("Code contains no non-empty lines")
            return ValidationResult(is_valid=False, errors=errors)

        # Check for diagram type declaration
        first_line = lines[0].lower()
        diagram_type = None

        for dtype in self.DIAGRAM_TYPES:
            if first_line.startswith(dtype.lower()):
                diagram_type = dtype
                break

        if not diagram_type:
            errors.append(
                f"First line must declare diagram type. "
                f"Valid types: {', '.join(self.DIAGRAM_TYPES)}"
            )
            return ValidationResult(is_valid=False, errors=errors)

        # Type-specific validation
        if diagram_type in ["flowchart", "graph"]:
            self._validate_flowchart(code, lines, warnings)
        elif diagram_type == "sequenceDiagram":
            self._validate_sequence(code, lines, warnings)
        elif diagram_type == "erDiagram":
            self._validate_er(code, lines, warnings)

        # General checks
        if len(lines) < 2:
            warnings.append("Diagram only has type declaration, no content")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    def _validate_flowchart(
        self, code: str, lines: list[str], warnings: list[str]
    ) -> None:
        """Validate flowchart-specific syntax."""
        # Check for arrows/connections
        has_connections = any(
            arrow in code for arrow in ["-->", "---", "-.->", "==>", "->", "~~>"]
        )
        if not has_connections:
            warnings.append("No arrow connections found in flowchart")

        # Check for node definitions
        has_nodes = bool(re.search(r"\[.*\]|\(.*\)|{.*}|\[\[.*\]\]", code))
        if not has_nodes:
            warnings.append("No node definitions found (brackets, parentheses, braces)")

    def _validate_sequence(
        self, code: str, lines: list[str], warnings: list[str]
    ) -> None:
        """Validate sequence diagram-specific syntax."""
        # Check for participant declarations or arrows
        has_participants = "participant " in code.lower()
        has_arrows = any(arrow in code for arrow in ["->", "->>", "-->", "-->>"])

        if not (has_participants or has_arrows):
            warnings.append(
                "No participants or message arrows found in sequence diagram"
            )

    def _validate_er(self, code: str, lines: list[str], warnings: list[str]) -> None:
        """Validate ER diagram-specific syntax."""
        # Check for entity definitions and relationships
        has_entities = bool(re.search(r"\w+\s*{", code))
        has_relationships = any(rel in code for rel in ["}o", "}|", "||", "|o", "o{"])

        if not has_entities:
            warnings.append("No entity definitions found (entity {)")
        if not has_relationships:
            warnings.append("No relationship symbols found")
