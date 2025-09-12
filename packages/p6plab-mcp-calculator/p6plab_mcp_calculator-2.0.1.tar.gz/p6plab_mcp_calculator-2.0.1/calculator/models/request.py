"""Pydantic request models for input validation."""

from typing import List, Optional, Union

from pydantic import BaseModel, Field, field_validator, model_validator


class BasicOperationRequest(BaseModel):
    """Request model for basic arithmetic operations."""

    a: float = Field(..., description="First number")
    b: float = Field(..., description="Second number")


class ExpressionRequest(BaseModel):
    """Request model for mathematical expression evaluation."""

    expression: str = Field(
        ...,
        max_length=1000,
        description="Mathematical expression to evaluate",
        examples=["2 + 3 * 4", "sin(pi/2)", "sqrt(16)"],
    )

    @field_validator("expression")
    @classmethod
    def validate_expression(cls, v):
        """Validate that expression is not empty and contains valid characters."""
        if not v.strip():
            raise ValueError("Expression cannot be empty")

        # Basic validation for potentially dangerous patterns
        dangerous_patterns = ["__", "import", "exec", "eval", "open", "file"]
        v_lower = v.lower()
        for pattern in dangerous_patterns:
            if pattern in v_lower:
                raise ValueError(f"Expression contains potentially dangerous pattern: {pattern}")

        return v.strip()


class TrigonometricRequest(BaseModel):
    """Request model for trigonometric function calculations."""

    function: str = Field(
        ...,
        pattern="^(sin|cos|tan|sec|csc|cot|asin|acos|atan|sinh|cosh|tanh)$",
        description="Trigonometric function name",
    )
    value: float = Field(..., description="Input value")
    unit: str = Field(
        default="radians", pattern="^(radians|degrees)$", description="Unit for angle measurement"
    )


class LogarithmRequest(BaseModel):
    """Request model for logarithmic calculations."""

    value: float = Field(..., gt=0, description="Value for logarithm (must be positive)")
    base: Optional[float] = Field(
        default=None, gt=0, json_schema_extra={"ne": 1}, description="Logarithm base (natural log if not provided)"
    )


class StatisticalRequest(BaseModel):
    """Request model for statistical operations."""

    data: List[float] = Field(
        ..., min_length=1, max_length=10000, description="Dataset for statistical analysis"
    )

    @field_validator("data")
    @classmethod
    def validate_data(cls, v):
        """Validate that data contains finite numbers."""
        import math

        for i, value in enumerate(v):
            if not math.isfinite(value):
                raise ValueError(f"Data point at index {i} is not finite: {value}")

        return v


class ProbabilityDistributionRequest(BaseModel):
    """Request model for probability distribution calculations."""

    distribution: str = Field(
        ...,
        pattern="^(normal|binomial|poisson|uniform|exponential)$",
        description="Type of probability distribution",
    )
    parameters: dict = Field(..., description="Distribution parameters")
    x: float = Field(..., description="Value to calculate probability for")

    @model_validator(mode='after')
    def validate_parameters(self):
        """Validate parameters based on distribution type."""
        if not hasattr(self, 'distribution') or not hasattr(self, 'parameters'):
            return self

        dist = self.distribution
        v = self.parameters

        if dist == "normal":
            required = {"mean", "std"}
            if not required.issubset(v.keys()):
                raise ValueError(f"Normal distribution requires parameters: {required}")
            if v["std"] <= 0:
                raise ValueError("Standard deviation must be positive")

        elif dist == "binomial":
            required = {"n", "p"}
            if not required.issubset(v.keys()):
                raise ValueError(f"Binomial distribution requires parameters: {required}")
            if not (0 <= v["p"] <= 1):
                raise ValueError("Probability p must be between 0 and 1")
            if v["n"] <= 0 or not isinstance(v["n"], int):
                raise ValueError("Number of trials n must be a positive integer")

        elif dist == "poisson":
            required = {"lambda"}
            if not required.issubset(v.keys()):
                raise ValueError(f"Poisson distribution requires parameters: {required}")
            if v["lambda"] <= 0:
                raise ValueError("Lambda parameter must be positive")

        return self


class MatrixRequest(BaseModel):
    """Request model for matrix operations."""

    matrix_a: List[List[float]] = Field(..., description="First matrix")
    matrix_b: Optional[List[List[float]]] = Field(
        default=None, description="Second matrix (for binary operations)"
    )

    @field_validator("matrix_a")
    @classmethod
    def validate_matrix_a(cls, v):
        """Validate that matrix_a is a valid matrix."""
        return cls._validate_matrix(v, "matrix_a")

    @field_validator("matrix_b")
    @classmethod
    def validate_matrix_b(cls, v):
        """Validate that matrix_b is a valid matrix if provided."""
        if v is not None:
            return cls._validate_matrix(v, "matrix_b")
        return v

    @staticmethod
    def _validate_matrix(matrix: List[List[float]], name: str) -> List[List[float]]:
        """Validate matrix structure and values."""
        import math

        if not matrix:
            raise ValueError(f"{name} cannot be empty")

        # Check that all rows have the same length
        row_length = len(matrix[0])
        if row_length == 0:
            raise ValueError(f"{name} rows cannot be empty")

        for i, row in enumerate(matrix):
            if len(row) != row_length:
                raise ValueError(f"{name} row {i} has different length than first row")

            # Check for finite values
            for j, value in enumerate(row):
                if not math.isfinite(value):
                    raise ValueError(f"{name}[{i}][{j}] is not finite: {value}")

        return matrix


class ComplexNumberRequest(BaseModel):
    """Request model for complex number operations."""

    operation: str = Field(
        ...,
        pattern="^(add|subtract|multiply|divide|magnitude|phase|conjugate|polar)$",
        description="Complex number operation",
    )
    a: Union[complex, str] = Field(..., description="First complex number")
    b: Optional[Union[complex, str]] = Field(
        default=None, description="Second complex number (for binary operations)"
    )

    @field_validator("a", "b")
    @classmethod
    def validate_complex_numbers(cls, v):
        """Validate and convert complex number representations."""
        if v is None:
            return v

        if isinstance(v, str):
            try:
                # Handle common string representations
                v = v.replace("i", "j").replace(" ", "")
                return complex(v)
            except ValueError:
                raise ValueError(f"Invalid complex number format: {v}")

        return v


class UnitConversionRequest(BaseModel):
    """Request model for unit conversions."""

    value: float = Field(..., description="Value to convert")
    from_unit: str = Field(..., min_length=1, description="Source unit")
    to_unit: str = Field(..., min_length=1, description="Target unit")
    unit_type: str = Field(
        ...,
        pattern="^(length|weight|temperature|volume|time|energy|pressure|power|frequency)$",
        description="Type of unit conversion",
    )


class CurrencyConversionRequest(BaseModel):
    """Request model for currency conversions."""

    amount: float = Field(..., gt=0, description="Amount to convert")
    from_currency: str = Field(
        ...,
        min_length=3,
        max_length=3,
        pattern="^[A-Z]{3}$",
        description="Source currency code (ISO 4217)",
    )
    to_currency: str = Field(
        ...,
        min_length=3,
        max_length=3,
        pattern="^[A-Z]{3}$",
        description="Target currency code (ISO 4217)",
    )


class FinancialCalculationRequest(BaseModel):
    """Request model for financial calculations."""

    calculation_type: str = Field(
        ...,
        pattern="^(compound_interest|present_value|future_value|annuity|loan_payment|irr|npv)$",
        description="Type of financial calculation",
    )
    parameters: dict = Field(..., description="Financial calculation parameters")

    @model_validator(mode='after')
    def validate_financial_parameters(self):
        """Validate financial parameters based on calculation type."""
        if not hasattr(self, 'calculation_type') or not hasattr(self, 'parameters'):
            return self

        calc_type = self.calculation_type
        v = self.parameters

        if calc_type == "compound_interest":
            required = {"principal", "rate", "time", "compound_frequency"}
            if not required.issubset(v.keys()):
                raise ValueError(f"Compound interest requires: {required}")

            if v["principal"] <= 0:
                raise ValueError("Principal must be positive")
            if v["rate"] < 0:
                raise ValueError("Interest rate cannot be negative")
            if v["time"] <= 0:
                raise ValueError("Time period must be positive")
            if v["compound_frequency"] <= 0:
                raise ValueError("Compound frequency must be positive")

        elif calc_type == "loan_payment":
            required = {"principal", "rate", "periods"}
            if not required.issubset(v.keys()):
                raise ValueError(f"Loan payment requires: {required}")

            if v["principal"] <= 0:
                raise ValueError("Principal must be positive")
            if v["rate"] < 0:
                raise ValueError("Interest rate cannot be negative")
            if v["periods"] <= 0:
                raise ValueError("Number of periods must be positive")

        return self


class EquationSolvingRequest(BaseModel):
    """Request model for equation solving."""

    equation_type: str = Field(
        ...,
        pattern="^(linear|quadratic|polynomial|system)$",
        description="Type of equation to solve",
    )
    equations: List[str] = Field(
        ..., min_length=1, max_length=10, description="Equation(s) to solve"
    )
    variables: Optional[List[str]] = Field(
        default=None, description="Variable names (auto-detected if not provided)"
    )

    @field_validator("equations")
    @classmethod
    def validate_equations(cls, v):
        """Validate equation format."""
        for i, eq in enumerate(v):
            if not eq.strip():
                raise ValueError(f"Equation {i} cannot be empty")

            # Basic validation for dangerous patterns
            dangerous_patterns = ["__", "import", "exec", "eval", "open", "file"]
            eq_lower = eq.lower()
            for pattern in dangerous_patterns:
                if pattern in eq_lower:
                    raise ValueError(f"Equation {i} contains dangerous pattern: {pattern}")

        return [eq.strip() for eq in v]


class CalculusRequest(BaseModel):
    """Request model for calculus operations."""

    operation: str = Field(
        ...,
        pattern="^(derivative|integral|definite_integral|partial_derivative)$",
        description="Calculus operation type",
    )
    expression: str = Field(..., max_length=1000, description="Mathematical expression")
    variable: str = Field(
        default="x",
        pattern="^[a-zA-Z][a-zA-Z0-9_]*$",
        description="Variable for differentiation/integration",
    )
    lower_bound: Optional[float] = Field(
        default=None, description="Lower bound for definite integrals"
    )
    upper_bound: Optional[float] = Field(
        default=None, description="Upper bound for definite integrals"
    )

    @field_validator("expression")
    @classmethod
    def validate_expression(cls, v):
        """Validate mathematical expression."""
        if not v.strip():
            raise ValueError("Expression cannot be empty")

        # Basic validation for dangerous patterns
        dangerous_patterns = ["__", "import", "exec", "eval", "open", "file"]
        v_lower = v.lower()
        for pattern in dangerous_patterns:
            if pattern in v_lower:
                raise ValueError(f"Expression contains dangerous pattern: {pattern}")

        return v.strip()

    @model_validator(mode='after')
    def validate_bounds(self):
        """Validate that upper bound is greater than lower bound."""
        if (hasattr(self, 'upper_bound') and hasattr(self, 'lower_bound') and 
            self.upper_bound is not None and self.lower_bound is not None):
            if self.upper_bound <= self.lower_bound:
                raise ValueError("Upper bound must be greater than lower bound")
        return self
