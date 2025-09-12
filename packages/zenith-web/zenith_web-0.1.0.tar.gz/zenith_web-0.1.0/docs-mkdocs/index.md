# Zenith Framework

## Build Modern Python APIs

!!! info "Clean Architecture"
    Organize business logic with clean contexts. Keep your domain logic independent of web concerns.

!!! success "Type-Safe by Default"
    Full type hints with Pydantic validation. Catch errors at development time with complete IDE support.

!!! example "SQLModel Integration"
    One model for everything - API validation, database tables, and documentation. No more duplication.

!!! tip "Production Ready"
    Built-in middleware for security, CORS, rate limiting, compression, monitoring, and health checks.

## Quick Start

```bash
# Install Zenith
pip install zenith-web

# Create a new project
zen new my-api

# Start development server
zen server --reload
```

## Why Developers Choose Zenith

### Developer Experience
Modern CLI tools, hot reload, auto-documentation, and comprehensive testing utilities make development a joy.

### Performance First
Built on Starlette with modern async patterns. Leverages Python 3.12+ features for optimal performance.

### Well Tested
Comprehensive test suite with 285+ tests. Zero memory leaks with bounded caches and automatic cleanup.

### Framework Agnostic
Serve any SPA framework with one command. React, Vue, Angular, SolidJS - we've got you covered.

## See It In Action

```python
from zenith import Zenith

app = Zenith()

@app.get("/")
async def hello():
    return {"message": "Hello, World!"}
```

That's all you need to build a production-ready API with automatic documentation, type validation, and error handling.

[Get Started](quick-start.md){ .md-button .md-button--primary }
[View on GitHub](https://github.com/nijaru/zenith){ .md-button }