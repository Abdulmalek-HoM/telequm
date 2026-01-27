# Contributing to TELEQUM

Thank you for your interest in contributing to TELEQUM! We're building the future of quantum-powered telecommunications.

## 🚀 Quick Start

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Run tests: `pytest tests/`
5. Commit: `git commit -m 'Add amazing feature'`
6. Push: `git push origin feature/amazing-feature`
7. Open a Pull Request

## 📋 Contribution Types

### 🐛 Bug Reports
- Check existing issues first
- Include minimal reproduction steps
- Specify Python version, Qiskit version, OS

### 💡 Feature Requests
- Describe the use case
- Explain how it benefits telecom applications

### 📝 Documentation
- Improve docstrings
- Add examples to notebooks
- Update README sections

### 🔬 Code Contributions
- Follow existing code style
- Add unit tests for new features
- Update relevant documentation

## 🎨 Code Style

- **Formatter**: Black (line length 100)
- **Linter**: Ruff
- **Type hints**: Required for public APIs
- **Docstrings**: NumPy format

```bash
# Format code
black telequm/ tests/

# Lint
ruff check telequm/

# Type check
mypy telequm/
```

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=telequm --cov-report=term-missing

# Test notebooks
pytest --nbmake notebooks/
```

## 📁 Directory Guidelines

| Directory | Content |
|-----------|---------|
| `telequm/core/` | Reusable circuits, Hamiltonians |
| `telequm/algorithms/` | QAOA, VQE, QML |
| `telequm/telecom/` | Industry-specific modules |
| `notebooks/` | Educational content |
| `dashboard/` | Streamlit app |
| `tests/` | Unit tests |

## 🔄 Pull Request Process

1. Update tests and documentation
2. Ensure CI passes
3. Request review from maintainers
4. Address feedback
5. Squash commits before merge

## 📜 Code of Conduct

Be respectful, inclusive, and constructive. We're building something great together.

## 📞 Questions?

Open an issue or reach out to the maintainers.

---

*Thank you for helping make TELEQUM the #1 quantum-telecom platform!*
